"""CL Control Web Next: Ingress-only, server-side HA API gateway."""
from __future__ import annotations
import asyncio
import json
import logging
import math
import os
from pathlib import Path
from aiohttp import web, ClientSession, ClientTimeout, ClientError
try:
    from .media import profile as media_profile, plan as media_plan
except ImportError:  # Direct execution in the Home Assistant App container.
    from media import profile as media_profile, plan as media_plan

LOG = logging.getLogger("cl_control_web")
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CORE = os.environ.get("HA_CORE_URL", "http://supervisor/core/api").rstrip("/")
def core_websocket_url(core):
    # Supervisor uses /core/websocket, whereas direct Core uses /api/websocket.
    endpoint = core[:-4] + "/websocket" if core.rstrip("/").endswith("/core/api") else core.rstrip("/") + "/websocket"
    return endpoint.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
DOMAINS = {
    "cover": {"open_cover", "close_cover", "stop_cover", "set_cover_position"},
    "climate": {"set_temperature", "set_hvac_mode", "set_preset_mode", "set_fan_mode"},
    "light": {"turn_on", "turn_off"},
    "media_player": {"media_play", "media_pause", "media_next_track", "media_previous_track", "volume_set", "volume_mute"},
}
PERMITTED_LIGHT = {"brightness_pct", "hs_color", "rgbw_color", "rgbww_color", "color_temp_kelvin"}
PERMITTED_MEDIA = {"volume_level", "is_volume_muted"}
MAX_BODY = 2048

@web.middleware
async def security_headers(request, handler):
    response = await handler(request)
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store" if request.path.startswith("/api/") else "no-cache",
        "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'self'; base-uri 'self'",
    })
    return response

async def ha_request(request: web.Request, method: str, endpoint: str, data=None):
    if not TOKEN:
        raise web.HTTPServiceUnavailable(text="Supervisor authentication unavailable")
    async with request.app["session"].request(
        method, f"{CORE}/{endpoint.lstrip('/')}",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json=data, allow_redirects=False,
    ) as res:
        if res.status != 200 and res.status != 201:
            LOG.warning("HA upstream %s returned HTTP %s", endpoint.split("/")[0], res.status)
            raise web.HTTPBadGateway(text="Home Assistant service unavailable")
        return await res.json(content_type=None)

async def bootstrap(request):
    states = await ha_request(request, "GET", "states")
    limited = []
    for item in states:
        eid = item.get("entity_id", "")
        domain = eid.split(".", 1)[0]
        if domain not in {"light","media_player","sensor","binary_sensor","cover","climate","switch","sun","weather","alarm_control_panel","camera","scene"}:
            continue
        attrs = item.get("attributes") or {}
        allowed = {
            k: v for k,v in attrs.items()
            if k in {"current_position","current_temperature","current_humidity","hvac_modes","hvac_action","min_temp","max_temp","target_temp_step","preset_modes","preset_mode","fan_modes","fan_mode","friendly_name","brightness","hs_color","rgb_color","rgbw_color","rgbww_color",
                     "supported_color_modes","color_mode","color_temp_kelvin","min_color_temp_kelvin",
                     "max_color_temp_kelvin","supported_features","volume_level","is_volume_muted",
                     "media_title","media_artist","source","source_list","unit_of_measurement","device_class","temperature","humidity","condition","forecast","entity_picture","supported_features"}
        }
        limited.append({"entity_id":eid,"state":item.get("state"),"attributes":allowed})
    return web.json_response({"version":"0.1.0-beta.6","states":limited})

def valid_control(obj):
    if not isinstance(obj,dict) or set(obj)-{"entity_id","action","data"}:
        raise ValueError("Invalid request")
    eid, action, params = obj.get("entity_id"), obj.get("action"), obj.get("data",{})
    if not isinstance(eid,str) or "." not in eid or len(eid)>255 or not all(c.isascii() and (c.isalnum() or c in "._") for c in eid):
        raise ValueError("Invalid entity ID")
    dom=eid.split(".",1)[0]
    if action not in DOMAINS.get(dom, set()) or not isinstance(params,dict):
        raise ValueError("Action not allowed")
    if dom in {"cover", "climate"}:
        expected = {"set_cover_position": "position", "set_temperature": "temperature", "set_hvac_mode": "hvac_mode", "set_preset_mode": "preset_mode", "set_fan_mode": "fan_mode"}.get(action)
        if set(params) != ({expected} if expected else set()):
            raise ValueError("Parametri non consentiti")
        if expected in {"position", "temperature"}:
            value = params[expected]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Valore non valido")
            if expected == "position" and (type(value) is not int or not 0 <= value <= 100):
                raise ValueError("Posizione non valida")
        elif expected and (not isinstance(params[expected], str) or len(params[expected]) > 100):
            raise ValueError("Modalità non valida")
        return dom, action, eid, params
    allowed=PERMITTED_LIGHT if dom=="light" else PERMITTED_MEDIA
    if set(params)-allowed:
        raise ValueError("Parameters not allowed")
    if action in {"turn_off","media_play","media_pause","media_previous_track","media_next_track"} and params:
        raise ValueError("Unexpected parameters")
    if action=="turn_on" and dom=="light":
        if sum(k in params for k in ("hs_color","rgbw_color","rgbww_color","color_temp_kelvin"))>1:
            raise ValueError("Conflicting color modes")
        if "brightness_pct" in params and (type(params["brightness_pct"]) not in (int,float) or not 1<=params["brightness_pct"]<=100):
            raise ValueError("Invalid brightness")
        if "color_temp_kelvin" in params and (type(params["color_temp_kelvin"]) is not int or not 1000<=params["color_temp_kelvin"]<=10000):
            raise ValueError("Invalid Kelvin")
        for key, size, high in (("hs_color",2,360),("rgbw_color",4,255),("rgbww_color",5,255)):
            if key in params and (not isinstance(params[key],list) or len(params[key])!=size or any(type(x) not in (int,float) or not 0<=x<=(100 if key=="hs_color" and i==1 else high) for i,x in enumerate(params[key]))):
                raise ValueError("Invalid color")
    if dom=="media_player":
        if action=="volume_set" and (set(params)!={"volume_level"} or type(params["volume_level"]) not in (int,float) or not 0<=params["volume_level"]<=1):
            raise ValueError("Invalid volume")
        if action=="volume_mute" and (set(params)!={"is_volume_muted"} or type(params["is_volume_muted"]) is not bool):
            raise ValueError("Invalid mute")
    return dom,action,eid,params

def validate_live_control(dom, action, params, state, services):
    if not state or state.get("state") in {"unknown", "unavailable", None}:
        raise ValueError("Dispositivo non disponibile")
    if action not in services.get(dom, {}):
        raise ValueError("Servizio non disponibile")
    a = state.get("attributes") or {}
    flags = a.get("supported_features", 0)
    bits = {"open_cover": 1, "close_cover": 2, "set_cover_position": 4, "stop_cover": 8,
            "set_temperature": 1, "set_preset_mode": 16, "set_fan_mode": 8}
    if action in bits and not flags & bits[action]:
        raise ValueError("Funzione non supportata")
    if action == "set_temperature":
        low, high = a.get("min_temp"), a.get("max_temp")
        if type(low) not in (int, float) or type(high) not in (int, float) or not low <= params["temperature"] <= high:
            raise ValueError("Temperatura fuori dai limiti del dispositivo")
    for key, values in (("hvac_mode", "hvac_modes"), ("preset_mode", "preset_modes"), ("fan_mode", "fan_modes")):
        if key in params and params[key] not in a.get(values, []):
            raise ValueError("Modalità non supportata")

async def command(request):
    if request.content_length and request.content_length>MAX_BODY:
        raise web.HTTPRequestEntityTooLarge(max_size=MAX_BODY,actual_size=request.content_length)
    if request.content_type!="application/json":
        raise web.HTTPUnsupportedMediaType()
    try:
        obj=await request.json()
        dom,action,eid,params=valid_control(obj)
        if dom in {"cover", "climate"}:
            states = await ha_request(request, "GET", "states")
            state = next((s for s in states if s.get("entity_id") == eid), None)
            raw = await ha_request(request, "GET", "services")
            validate_live_control(dom, action, params, state, {s["domain"]: s.get("services", {}) for s in raw})
    except (ValueError,TypeError,json.JSONDecodeError) as ex:
        raise web.HTTPBadRequest(text=str(ex)) from ex
    await ha_request(request,"POST",f"services/{dom}/{action}",{"entity_id":eid,**params})
    return web.json_response({"ok":True})


async def areas(request):
    """Read-only areas with registry-linked temperature/humidity, no direct user token."""
    template = """{% set ns = namespace(items=[]) %}{% for a in areas() %}{% set ns.items = ns.items + [dict(id=a,name=area_name(a),temperature=area_entities(a)|list)] %}{% endfor %}{{ ns.items | to_json }}"""
    try:
        if not TOKEN:
            raise web.HTTPServiceUnavailable(text="HA token unavailable")
        async with request.app["session"].post(f"{CORE}/template",json={"template":template},headers={"Authorization":f"Bearer {TOKEN}"},allow_redirects=False) as res:
            if res.status != 200:
                raise web.HTTPBadGateway(text="HA areas unavailable")
            value=await res.text()
        data=json.loads(value)
        return web.json_response({"areas":[{"id":a["id"],"name":a["name"],"entities":a["temperature"][:600]} for a in data][:100]})
    except (ValueError,KeyError,TypeError) as exc:
        LOG.warning("Invalid HA areas response: %s",type(exc).__name__)
        raise web.HTTPBadGateway(text="HA areas response invalid") from exc

async def index(_):
    return web.FileResponse(STATIC/"index.html")

async def media_metadata(request):
    """Read only the registry and registered services; no entity-name heuristics."""
    raw = await ha_request(request, "GET", "services")
    services = {s["domain"]: s.get("services", {}) for s in raw}
    registry = []
    try:
        async with asyncio.timeout(8):
            async with request.app["session"].ws_connect(core_websocket_url(CORE), headers={"Authorization": f"Bearer {TOKEN}"}) as ws:
                if (await ws.receive_json()).get("type") != "auth_required":
                    raise ValueError("Unexpected WebSocket greeting")
                await ws.send_json({"type": "auth", "access_token": TOKEN})
                if (await ws.receive_json()).get("type") != "auth_ok":
                    raise ValueError("Registry authentication unavailable")
                await ws.send_json({"id": 1, "type": "config/entity_registry/list"})
                result = await ws.receive_json()
                if result.get("success"):
                    registry = result.get("result", [])
    except (TimeoutError, ValueError, OSError, ClientError):
        LOG.warning("Media registry unavailable; using basic controls only")
    return registry, services

async def media_profiles(request):
    states = await ha_request(request, "GET", "states")
    registry, services = await media_metadata(request)
    return web.json_response({"profiles": [media_profile(s, registry, services, states)
                             for s in states if s.get("entity_id", "").startswith("media_player.")]})

async def media_command(request):
    if request.content_type != "application/json":
        raise web.HTTPUnsupportedMediaType()
    try:
        obj = await request.json()
        eid = obj.get("entity_id") if isinstance(obj, dict) else None
        if not isinstance(eid, str) or not eid.startswith("media_player."):
            raise ValueError("Dispositivo non valido")
        states = await ha_request(request, "GET", "states")
        state = next((s for s in states if s.get("entity_id") == eid), None)
        if state is None:
            raise ValueError("Dispositivo non trovato")
        registry, services = await media_metadata(request)
        p = media_profile(state, registry, services, states)
        endpoint, payload = media_plan(obj, state, p)
    except (ValueError, TypeError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    await ha_request(request, "POST", "services/" + endpoint, payload)
    return web.json_response({"ok": True})

async def health(_):
    return web.json_response({"ok":True,"version":"0.1.0-beta.6"})

async def start_session(app):
    app["session"]=ClientSession(timeout=ClientTimeout(total=8))
    yield
    await app["session"].close()

def create_app():
    app=web.Application(middlewares=[security_headers],client_max_size=MAX_BODY)
    app.cleanup_ctx.append(start_session)
    app.router.add_get("/",index)
    app.router.add_get("/api/health",health)
    app.router.add_get("/api/bootstrap",bootstrap)
    app.router.add_get("/api/areas",areas)
    app.router.add_post("/api/command",command)
    app.router.add_get("/api/media-profiles",media_profiles)
    app.router.add_post("/api/media-command",media_command)
    app.router.add_static("/assets/",STATIC/"assets",show_index=False,follow_symlinks=False)
    return app

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(create_app(),host="0.0.0.0",port=8099,access_log=None)
