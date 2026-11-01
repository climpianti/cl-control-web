"""Read-only Home Assistant state-change relay for the Ingress Web App.

One upstream subscription per connected browser. No Home Assistant token or
unfiltered event payload is exposed to the client.
"""
import asyncio
import json
import logging
from aiohttp import web, WSMsgType, ClientError

LOG = logging.getLogger("cl_control_web.realtime")
CLIENT_LIMIT = 6
WS_TIMEOUT = 10
ALLOWED_DOMAINS = frozenset({
    "light", "media_player", "sensor", "binary_sensor", "cover", "climate",
    "switch", "sun", "weather", "alarm_control_panel", "camera", "scene"
})
ALLOWED_ATTRIBUTES = frozenset({
    "current_position", "current_temperature", "current_humidity",
    "hvac_modes", "hvac_action", "min_temp", "max_temp", "target_temp_step",
    "preset_modes", "preset_mode", "fan_modes", "fan_mode", "friendly_name",
    "brightness", "hs_color", "rgb_color", "rgbw_color", "rgbww_color",
    "supported_color_modes", "color_mode", "color_temp_kelvin",
    "min_color_temp_kelvin", "max_color_temp_kelvin", "supported_features",
    "volume_level", "is_volume_muted", "media_title", "media_artist",
    "source", "source_list", "unit_of_measurement", "device_class",
    "temperature", "humidity", "condition", "forecast", "entity_picture"
})


def filter_state(value):
    """Only publish a public-dashboard subset of Home Assistant state."""
    if not isinstance(value, dict):
        return None
    eid = value.get("entity_id")
    if not isinstance(eid, str) or "." not in eid:
        return None
    if eid.split(".", 1)[0] not in ALLOWED_DOMAINS:
        return None
    attrs = value.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    return {
        "entity_id": eid,
        "state": value.get("state"),
        "attributes": {key: val for key, val in attrs.items() if key in ALLOWED_ATTRIBUTES},
    }


def relay_event(message):
    """Return a filtered state_changed delta, or None for non-state events."""
    if not isinstance(message, dict) or message.get("type") != "event":
        return None
    event = message.get("event") or {}
    if event.get("event_type") != "state_changed":
        return None
    data = event.get("data") or {}
    eid = data.get("entity_id")
    if not isinstance(eid, str) or eid.split(".", 1)[0] not in ALLOWED_DOMAINS:
        return None
    new = data.get("new_state")
    if new is None:
        return {"type": "state", "entity_id": eid, "state": None}
    state = filter_state(new)
    if state is None or state["entity_id"] != eid:
        return None
    return {"type": "state", "entity_id": eid, "state": state}


async def relay(request, *, token, websocket_url):
    """Authenticated upstream read-only state subscription; filtered downstream."""
    if not token:
        raise web.HTTPServiceUnavailable(text="Home Assistant unavailable")
    active = request.app.setdefault("realtime_clients", set())
    if len(active) >= CLIENT_LIMIT:
        raise web.HTTPServiceUnavailable(text="Realtime capacity reached")
    downstream = web.WebSocketResponse(heartbeat=30, max_msg_size=512)
    await downstream.prepare(request)
    active.add(downstream)
    try:
        try:
            async with request.app["session"].ws_connect(
                websocket_url, heartbeat=30, max_msg_size=2 * 1024 * 1024
            ) as upstream:
                async with asyncio.timeout(WS_TIMEOUT):
                    greeting = await upstream.receive_json()
                    if greeting.get("type") != "auth_required":
                        raise RuntimeError("Unexpected HA greeting")
                    await upstream.send_json({"type": "auth", "access_token": token})
                    auth = await upstream.receive_json()
                    if auth.get("type") != "auth_ok":
                        raise RuntimeError("HA realtime authentication failed")
                    await upstream.send_json({
                        "id": 1, "type": "subscribe_events", "event_type": "state_changed"
                    })
                    result = await upstream.receive_json()
                    if not result.get("success"):
                        raise RuntimeError("HA state subscription unavailable")
                await downstream.send_json({"type": "ready"})
                async for packet in upstream:
                    if downstream.closed:
                        break
                    if packet.type == WSMsgType.TEXT:
                        try:
                            filtered = relay_event(json.loads(packet.data))
                        except (ValueError, TypeError):
                            continue
                        if filtered:
                            await downstream.send_json(filtered)
                    elif packet.type in (WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSED):
                        break
        except (TimeoutError, OSError, RuntimeError, ClientError) as exc:
            LOG.warning("Realtime bridge unavailable: %s", type(exc).__name__)
            if not downstream.closed:
                await downstream.send_json({"type": "error", "message": "Realtime unavailable"})
    finally:
        active.discard(downstream)
        await downstream.close()
    return downstream
