"""Capability-driven media controls. Never accepts raw services or remote codes."""
FEATURES = {"media_pause": 1, "volume_set": 4, "volume_mute": 8,
            "media_previous_track": 16, "media_next_track": 32,
            "turn_on": 128, "turn_off": 256, "media_stop": 4096,
            "select_source": 2048, "volume_up": 1024, "volume_down": 1024,
            "media_play": 16384}
KEYS = {
    "webostv": dict(up="UP", down="DOWN", left="LEFT", right="RIGHT", ok="ENTER", home="HOME", back="BACK", menu="MENU", channel_up="CHANNELUP", channel_down="CHANNELDOWN", **{str(i): str(i) for i in range(10)}),
    "samsungtv": dict(up="KEY_UP", down="KEY_DOWN", left="KEY_LEFT", right="KEY_RIGHT", ok="KEY_ENTER", home="KEY_HOME", back="KEY_RETURN", menu="KEY_MENU", channel_up="KEY_CHUP", channel_down="KEY_CHDOWN", **{str(i): f"KEY_{i}" for i in range(10)}),
    "androidtv_remote": dict(up="DPAD_UP", down="DPAD_DOWN", left="DPAD_LEFT", right="DPAD_RIGHT", ok="DPAD_CENTER", home="HOME", back="BACK", menu="MENU", channel_up="CHANNEL_UP", channel_down="CHANNEL_DOWN", **{str(i): str(i) for i in range(10)}),
}

def profile(state, registry, services, states):
    eid = state["entity_id"]
    attrs = state.get("attributes") or {}
    flags = attrs.get("supported_features", 0)
    flags = flags if type(flags) is int else 0
    actions = [a for a, bit in FEATURES.items() if flags & bit and a in services.get("media_player", {})]
    entry = next((r for r in registry if r.get("entity_id") == eid and not r.get("disabled_by")), {})
    platform = entry.get("platform")
    remote, provider = None, None
    if platform == "webostv" and "button" in services.get("webostv", {}):
        remote, provider = eid, platform
    elif entry.get("device_id") and "send_command" in services.get("remote", {}):
        matches = [r for r in registry if r.get("device_id") == entry["device_id"]
                   and r.get("entity_id", "").startswith("remote.")
                   and r.get("platform") in ("samsungtv", "androidtv_remote")
                   and not r.get("disabled_by")]
        if len(matches) == 1:
            remote, provider = matches[0]["entity_id"], matches[0]["platform"]
    remote_state = next((s for s in states if s.get("entity_id") == remote), {})
    remote_ready = remote_state.get("state") not in (None, "unknown", "unavailable")
    sources = attrs.get("source_list") or []
    sources = [s for s in sources if isinstance(s, str) and 0 < len(s) <= 300] if isinstance(sources, list) else []
    return {"entity_id": eid, "actions": actions, "sources": sources if "select_source" in actions else [],
            "keys": list(KEYS.get(provider, {})) if remote_ready else [],
            "provider": provider, "remote_entity": remote,
            "available": state.get("state") not in (None, "unknown", "unavailable"),
            "powered": state.get("state") not in (None, "unknown", "unavailable", "off", "standby")}

def plan(obj, state, p):
    if not isinstance(obj, dict) or set(obj) - {"entity_id", "action", "data"}:
        raise ValueError("Richiesta non valida")
    eid, action, data = obj.get("entity_id"), obj.get("action"), obj.get("data", {})
    if not isinstance(eid, str) or eid != p["entity_id"] or not eid.startswith("media_player.") or not isinstance(action, str) or not isinstance(data, dict):
        raise ValueError("Dispositivo non valido")
    if not p["available"] or (not p["powered"] and action != "turn_on"):
        raise ValueError("Dispositivo spento o non disponibile")
    if action == "key":
        key = data.get("key")
        if set(data) != {"key"} or not isinstance(key, str) or key not in p["keys"]:
            raise ValueError("Tasto non disponibile")
        provider = p["provider"]
        if provider == "webostv":
            return "webostv/button", {"entity_id": eid, "button": KEYS[provider][key]}
        return "remote/send_command", {"entity_id": p["remote_entity"], "command": KEYS[provider][key]}
    if action not in p["actions"]:
        raise ValueError("Funzione non supportata")
    if action == "select_source":
        if set(data) != {"source"} or data["source"] not in p["sources"]:
            raise ValueError("Sorgente non disponibile")
    elif action == "volume_set":
        if set(data) != {"volume_level"} or type(data["volume_level"]) not in (int, float) or not 0 <= data["volume_level"] <= 1:
            raise ValueError("Volume non valido")
    elif action == "volume_mute":
        if set(data) != {"is_volume_muted"} or type(data["is_volume_muted"]) is not bool:
            raise ValueError("Mute non valido")
    elif data:
        raise ValueError("Parametri non previsti")
    return "media_player/" + action, {"entity_id": eid, **data}
