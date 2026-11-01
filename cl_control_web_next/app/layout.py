"""Versioned, declarative dashboard layouts. No executable HTML, JS or HA calls.

Schemas are purposefully small: AI or installers can propose structured layouts,
but only the explicit save endpoint can persist an approved revision.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = 1
ALLOWED = frozenset({"systems", "areas", "cl_systems", "entity", "energy"})
ENTITY_DOMAINS = frozenset({"light", "cover", "climate", "sensor", "binary_sensor", "media_player"})
ENTITY_RE = re.compile(r"^(?:light|cover|climate|sensor|binary_sensor|media_player)\.[a-z0-9_]{1,120}$")
ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")
MAX_WIDGETS = 24
MAX_BYTES = 8192
STORE_FILE = Path(os.environ.get("CL_CONTROL_LAYOUT_PATH", "/data/dashboard-layout.json"))
DEFAULT = {
    "schema_version": SCHEMA,
    "revision": 0,
    "title": "La tua casa",
    "widgets": [
        {"id": "systems", "type": "systems", "title": "Sistemi"},
        {"id": "areas", "type": "areas", "title": "Aree"},
        {"id": "cl-systems", "type": "cl_systems", "title": "Sistemi CL"},
    ],
}


def validate_layout(value, known_entities=None):
    if not isinstance(value, dict) or set(value) != {"schema_version", "revision", "title", "widgets"}:
        raise ValueError("Formato dashboard non valido")
    if type(value["schema_version"]) is not int or value["schema_version"] != SCHEMA:
        raise ValueError("Versione modello non supportata")
    if type(value["revision"]) is not int or value["revision"] < 0:
        raise ValueError("Revisione non valida")
    title = value["title"]
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 64:
        raise ValueError("Titolo non valido")
    widgets = value["widgets"]
    if not isinstance(widgets, list) or not 1 <= len(widgets) <= MAX_WIDGETS:
        raise ValueError("Widget non validi")
    used = set()
    for item in widgets:
        if not isinstance(item, dict):
            raise ValueError("Widget non valido")
        kind = item.get("type")
        expected = {"id", "type", "title"} | ({"entity_id"} if kind == "entity" else set())
        if kind not in ALLOWED or set(item) != expected:
            raise ValueError("Tipo o attributi widget non consentiti")
        ident = item["id"]
        if not isinstance(ident, str) or not ID_RE.fullmatch(ident) or ident in used:
            raise ValueError("Identificatore widget non valido o duplicato")
        used.add(ident)
        if not isinstance(item["title"], str) or not 1 <= len(item["title"].strip()) <= 64:
            raise ValueError("Etichetta widget non valida")
        if kind == "entity":
            entity_id = item["entity_id"]
            if not isinstance(entity_id, str) or not ENTITY_RE.fullmatch(entity_id):
                raise ValueError("Entita non consentita")
            if known_entities is not None and entity_id not in known_entities:
                raise ValueError("Entita non presente nell'impianto")
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > MAX_BYTES:
        raise ValueError("Configurazione troppo grande")
    return deepcopy(value)


def suggest_layout(entities, areas):
    """Deterministic proposal suitable as an input to a future AI planner.

    No LLM runs here. The output must still be approved to persist.
    """
    layout = deepcopy(DEFAULT)
    live = {e for e in entities if isinstance(e, str)}
    if "sensor.senec_solar_generated_power" in live or any(e.startswith("sensor.cl_power_control_energy_") for e in live):
        layout["widgets"].append({"id": "energy-live", "type": "energy", "title": "Energia in tempo reale"})
    first = next((e for e in sorted(live) if e.startswith("light.")), None)
    if first:
        layout["widgets"].append({"id": "favorite-light", "type": "entity", "title": "Luce principale", "entity_id": first})
    return validate_layout(layout, live)


class LayoutStore:
    def __init__(self, path=STORE_FILE):
        self.path = Path(path)
        self.lock = asyncio.Lock()
        self.value = deepcopy(DEFAULT)

    async def load(self):
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            self.value = validate_layout(loaded)
        except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Archivio dashboard non valido, conservato senza reset") from exc

    async def save(self, proposed, expected_revision, known_entities):
        async with self.lock:
            if type(expected_revision) is not int or expected_revision != self.value["revision"]:
                raise ValueError("Dashboard modificata da un'altra sessione: ricaricare")
            candidate = validate_layout(proposed, known_entities)
            candidate["revision"] = self.value["revision"] + 1
            parent = self.path.parent
            parent.mkdir(parents=True, exist_ok=True)
            # Atomic replacement: a failed write leaves the previous layout intact.
            tmp = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=parent, prefix=".layout-", delete=False) as stream:
                    tmp = Path(stream.name)
                    os.chmod(tmp, 0o600)
                    json.dump(candidate, stream, ensure_ascii=False, separators=(",", ":"))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(tmp, self.path)
                self.value = deepcopy(candidate)
            finally:
                if tmp and tmp.exists():
                    tmp.unlink()
            return deepcopy(self.value)

    def snapshot(self):
        return deepcopy(self.value)
