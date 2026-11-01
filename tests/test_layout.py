"""Dashboard schema, persistence and safe fail-closed preview/save regressions."""
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import unittest
from unittest.mock import AsyncMock, patch
from aiohttp.test_utils import TestClient, TestServer
from cl_control_web_next.app.layout import LayoutStore, DEFAULT, validate_layout, suggest_layout, build_catalog
from cl_control_web_next.app.server import create_app


class SchemaTests(unittest.TestCase):
    def test_default_and_proposal(self):
        self.assertEqual(validate_layout(DEFAULT), DEFAULT)
        proposal = suggest_layout({"light.kitchen", "sensor.senec_solar_generated_power"}, [])
        self.assertEqual([w["type"] for w in proposal["widgets"]], [
            "systems", "areas", "cl_systems", "energy", "entity"
        ])
        self.assertEqual(proposal["widgets"][-1]["entity_id"], "light.kitchen")

    def test_no_executable_or_unauthorized_widgets(self):
        for bad in [
            {"id": "x", "type": "html", "title": "X", "html": "<script>alert(1)</script>"},
            {"id": "x", "type": "entity", "title": "X", "entity_id": "lock.front_door"},
            {"id": "x", "type": "entity", "title": "X", "entity_id": "light.unregistered"},
            {"id": "x", "type": "systems", "title": "X", "javascript": "alert(1)"},
        ]:
            draft = deepcopy(DEFAULT)
            draft["widgets"] = [bad]
            with self.assertRaises(ValueError):
                validate_layout(draft, {"light.kitchen"})

    def test_does_not_mutate_input(self):
        draft = deepcopy(DEFAULT)
        checked = validate_layout(draft)
        checked["widgets"].clear()
        self.assertEqual(len(draft["widgets"]), 3)


class CatalogTests(unittest.TestCase):
    def test_only_allowed_entity_types_and_public_fields(self):
        inventory = [
            {"entity_id": "light.kitchen", "state": "on", "attributes": {
                "friendly_name": "Cucina", "access_token": "SECRET", "secret": "hidden"}},
            {"entity_id": "sensor.temperature", "state": "22", "attributes": {"friendly_name": "Temperatura"}},
            {"entity_id": "lock.front_door", "state": "locked", "attributes": {"pin": "1234"}},
            {"entity_id": "script.open_gate", "state": "off", "attributes": {}},
        ]
        result = build_catalog(inventory)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["max_widgets"], 24)
        self.assertEqual({e["entity_id"] for e in result["entities"]},
                         {"light.kitchen", "sensor.temperature"})
        self.assertNotIn("SECRET", str(result))
        self.assertNotIn("1234", str(result))
        self.assertEqual(len(result["widget_types"]), 5)

    def test_entity_rejects_executable_markup_and_bad_ids(self):
        values = [{"entity_id": "<script>alert(1)</script>", "attributes": {}},
                  {"entity_id": "sensor.ok", "attributes": {"friendly_name": "<img onerror=evil>"}}]
        result = build_catalog(values)
        self.assertEqual(len(result["entities"]), 1)
        self.assertEqual(result["entities"][0]["entity_id"], "sensor.ok")

class StorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_atomic_save_restart_and_cas(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout.json"
            store = LayoutStore(path)
            incoming = deepcopy(DEFAULT)
            incoming["title"] = "Villa"
            saved = await store.save(incoming, 0, set())
            self.assertEqual(saved["revision"], 1)
            self.assertEqual(store.snapshot()["title"], "Villa")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            restarted = LayoutStore(path)
            await restarted.load()
            self.assertEqual(restarted.snapshot(), saved)
            with self.assertRaises(ValueError):
                await store.save(incoming, 0, set())
            self.assertEqual(path.read_text(encoding="utf-8") != "", True)

    async def test_broken_storage_does_not_reset(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout.json"
            path.write_text('{"schema_version":999}', encoding="utf-8")
            store = LayoutStore(path)
            with self.assertRaises(RuntimeError):
                await store.load()
            self.assertEqual(path.read_text(encoding="utf-8"), '{"schema_version":999}')


class EndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_does_not_save_and_direct_writes_are_forbidden(self):
        with TemporaryDirectory() as tmp:
            with patch("cl_control_web_next.app.server.LayoutStore", return_value=LayoutStore(Path(tmp)/"layout.json")):
                app = create_app()
            async with TestClient(TestServer(app)) as client:
                response = await client.post("/api/layout/preview", json={"suggest": True})
                self.assertEqual(response.status, 403)
                response = await client.post("/api/layout/save", json={
                    "layout": DEFAULT, "expected_revision": 0
                }, headers={"X-CL-Layout-Confirm": "yes", "Sec-Fetch-Site": "same-origin"})
                self.assertEqual(response.status, 403)
                response = await client.get("/api/layout")
                self.assertEqual(response.status, 200)
                self.assertEqual((await response.json())["layout"]["revision"], 0)
                self.assertFalse((Path(tmp)/"layout.json").exists())


if __name__ == "__main__":
    unittest.main()
