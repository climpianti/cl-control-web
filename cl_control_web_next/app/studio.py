"""Offline AI Studio layout planner. No cloud, LLM, shell or service execution.

Treat user text as data, never as instructions about privileges, devices or
tool execution. Only names matched to actual allowlisted HA entities enter
the draft. Preview is validated by the existing layout schema.
"""
from __future__ import annotations

from copy import deepcopy
import re
import unicodedata
try:
    from .layout import DEFAULT, MAX_WIDGETS, build_catalog, validate_layout
except ImportError:
    from layout import DEFAULT, MAX_WIDGETS, build_catalog, validate_layout

MAX_PROMPT = 700
STOPWORDS = frozenset({"il","la","lo","di","del","della","delle","dei","da","in","per",
                        "su","un","una","con","che","voglio","metti","mostra","aggiungi",
                        "dashboard","widget","sezione","vista","home","e","ed","nella",
                        "nel","sulla","alla","a","mi","le","gli","i","tutte","tutti",
                        "principale","piu","grande","alto","in","automatico"})


def normalized(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def intent_draft(prompt, states, current=None):
    if not isinstance(prompt, str) or not 3 <= len(prompt.strip()) <= MAX_PROMPT:
        raise ValueError("Richiesta non valida (3-700 caratteri)")
    if not isinstance(states, list):
        raise ValueError("Inventario non valido")
    cleaned = normalized(prompt)
    catalog = build_catalog(states)
    entities = catalog["entities"]
    if not entities:
        raise ValueError("Nessuna entita compatibile disponibile")
    base = deepcopy(DEFAULT if current is None else validate_layout(current))
    base["revision"] = current["revision"] if current is not None else 0
    # Deterministic, bounded edit intents. Unrecognized or dangerous requests are not applied.
    intro = ("crea","genera","realizza","prepara","imposta")
    reset = any(re.search(r"\b"+v+r"\b", cleaned) for v in intro)
    if reset:
        base = deepcopy(DEFAULT)
        base["revision"] = current["revision"] if current is not None else 0
        base["widgets"] = []
    words = {w for w in re.findall(r"[a-z0-9]+", cleaned) if len(w)>2 and w not in STOPWORDS}
    wants = {
        "systems": bool(re.search(r"\b(sistem[ai]|panoramica|generale)\b",cleaned)),
        "areas": bool(re.search(r"\b(aree|ambienti|stanze|pian[oi]|zone)\b",cleaned)),
        "cl_systems": bool(re.search(r"\b(irrigazion[ei]|sistemi cl)\b",cleaned)),
        "energy": bool(re.search(r"\b(energi[ae]|fotovoltaic[oa]|senec|batteri[ae]|consum[oi]|rete elettrica)\b",cleaned)),
    }
    hints = {
        "light":("luc","luci","lampad","illuminazion","led","rgb"),
        "climate":("clima","temperatur","termostat","riscaldament","fancoil","raffrescament"),
        "cover":("tapparel","serrand","apertur","tend","persian"),
        "media_player":("tv","television","multimedia","speaker","musica"),
        "sensor":("sensor","temperatur","umidit","co2"),
        "binary_sensor":("presenz","rilevator","moviment"),
    }
    requested_domains={domain for domain,keys in hints.items() if any(k in cleaned for k in keys)}
    selected=[]
    for ent in entities:
        dom=ent["domain"]
        if dom not in requested_domains:
            continue
        name_words={w for w in re.findall(r"[a-z0-9]+", normalized(ent["name"])) if len(w)>2 and w not in STOPWORDS}
        eid_words=set(ent["entity_id"].split(".",1)[-1].split("_"))
        overlap=len(words & (name_words|eid_words))
        if overlap:
            selected.append((overlap,ent))
    selected.sort(key=lambda pair:(-pair[0],pair[1]["entity_id"]))
    instructions=[]
    def add(kind,title,entity_id=None):
        if len(base["widgets"])>=MAX_WIDGETS:return
        ident=f"ai-{kind}-{len(base['widgets'])+1}"
        while any(w["id"]==ident for w in base["widgets"]):
            ident=f"ai-{kind}-{len(base['widgets'])+2}"
        item={"id":ident,"type":kind,"title":title}
        if entity_id:item["entity_id"]=entity_id
        base["widgets"].append(item)
    for kind,title in (("systems","Sistemi"),("areas","Aree"),
                       ("cl_systems","Sistemi CL"),("energy","Energia")):
        if wants[kind] and not any(w["type"]==kind for w in base["widgets"]):
            add(kind,title);instructions.append(title)
    for score,ent in selected[:6]:
        if not any(w["type"]=="entity" and w["entity_id"]==ent["entity_id"] for w in base["widgets"]):
            add("entity",ent["name"][:64],ent["entity_id"])
            instructions.append(ent["name"])
    if not instructions:
        # No implicit replacement: preserve current layout and explain limitations.
        return {"mode":"offline-rules","supported":False,"draft":validate_layout(base,{e["entity_id"] for e in entities}),
                "explanation":"Richiesta non riconosciuta dalle regole locali. Modifica i widget nell'editor oppure collega in futuro un provider AI."}
    result=validate_layout(base,{e["entity_id"] for e in entities})
    return {"mode":"offline-rules","supported":True,"draft":result,
            "explanation":"Proposta locale basata su entita reali: "+", ".join(instructions[:9])+". Verifica nell'editor prima di salvare."}
