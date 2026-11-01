import unittest
from unittest.mock import patch, AsyncMock
from aiohttp.test_utils import TestClient, TestServer
from cl_control_web_next.app.media import profile, plan, FEATURES
from cl_control_web_next.app.server import create_app, core_websocket_url

SERVICES = {"media_player": {k: {} for k in FEATURES}, "webostv": {"button": {}}, "remote": {"send_command": {}}}

def player(state="on", platform="webostv"):
    s = {"entity_id": "media_player.tv", "state": state, "attributes": {"supported_features": sum(set(FEATURES.values())), "source_list": ["HDMI 1", "TV"]}}
    r = [{"entity_id": s["entity_id"], "platform": platform, "device_id": "device-a"}]
    return s, r

class MediaTests(unittest.TestCase):
    def test_supervisor_and_direct_core_websocket_routes(self):
        self.assertEqual(core_websocket_url('http://supervisor/core/api'),'ws://supervisor/core/websocket')
        self.assertEqual(core_websocket_url('https://home.example/api'),'wss://home.example/api/websocket')

    def test_webos_navigation(self):
        s, r = player()
        p = profile(s, r, SERVICES, [s])
        self.assertEqual(plan({"entity_id":s["entity_id"],"action":"key","data":{"key":"up"}},s,p), ("webostv/button", {"entity_id":s["entity_id"],"button":"UP"}))

    def test_same_device_remote_only_and_ambiguous_remotes_rejected(self):
        s, r = player(platform="samsungtv")
        remote = {"entity_id":"remote.tv","platform":"samsungtv","device_id":"device-b"}
        rs = {"entity_id":"remote.tv","state":"on"}
        self.assertEqual(profile(s,r+[remote],SERVICES,[s,rs])["keys"],[])
        remote["device_id"]="device-a"
        p=profile(s,r+[remote],SERVICES,[s,rs])
        self.assertEqual(plan({"entity_id":s["entity_id"],"action":"key","data":{"key":"ok"}},s,p)[1]["command"],"KEY_ENTER")
        self.assertEqual(profile(s,r+[remote,{**remote,"entity_id":"remote.other"}],SERVICES,[s,rs])["keys"],[])

    def test_disabled_remote_and_absent_service(self):
        s,r=player(platform="samsungtv")
        remote={"entity_id":"remote.tv","platform":"samsungtv","device_id":"device-a","disabled_by":"user"}
        self.assertEqual(profile(s,r+[remote],SERVICES,[s,{"entity_id":"remote.tv","state":"on"}])["keys"],[])
        s,r=player()
        self.assertEqual(profile(s,r,{"media_player":{}},[s])["keys"],[])

    def test_sources_and_payloads_are_allowlisted(self):
        s,r=player();p=profile(s,r,SERVICES,[s])
        self.assertEqual(plan({"entity_id":s["entity_id"],"action":"select_source","data":{"source":"HDMI 1"}},s,p)[1]["source"],"HDMI 1")
        for action,data in [("select_source",{"source":"invented"}),("key",{"key":"KEY_FACTORY"}),("key",{"key":"up","entity_id":"remote.other"}),("volume_set",{"volume_level":True}),("turn_on",{"extra":1}),("send_command",{})]:
            with self.subTest(action=action,data=data),self.assertRaises(ValueError):
                plan({"entity_id":s["entity_id"],"action":action,"data":data},s,p)

    def test_off_allows_only_supported_power_on(self):
        s,r=player("off");p=profile(s,r,SERVICES,[s])
        self.assertEqual(plan({"entity_id":s["entity_id"],"action":"turn_on"},s,p)[0],"media_player/turn_on")
        with self.assertRaises(ValueError):plan({"entity_id":s["entity_id"],"action":"volume_up"},s,p)
        s["state"]="unavailable";p=profile(s,r,SERVICES,[s])
        with self.assertRaises(ValueError):plan({"entity_id":s["entity_id"],"action":"turn_on"},s,p)

class MediaRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_route_validates_live_state_and_forwards_only_resolved_target(self):
        s,r=player()
        async def upstream(request,method,endpoint,data=None):
            if method=="GET":return [s]
            return []
        with patch('cl_control_web_next.app.server.ha_request',new=AsyncMock(side_effect=upstream)) as ha,patch('cl_control_web_next.app.server.media_metadata',new=AsyncMock(return_value=(r,SERVICES))):
            async with TestClient(TestServer(create_app())) as client:
                response=await client.post('/api/media-command',json={"entity_id":s["entity_id"],"action":"key","data":{"key":"home"}})
                self.assertEqual(response.status,200)
                self.assertEqual(ha.call_args.args[2:],('services/webostv/button',{'entity_id':'media_player.tv','button':'HOME'}))
                s['attributes']['source_list']=['TV']
                response=await client.post('/api/media-command',json={"entity_id":s["entity_id"],"action":"select_source","data":{"source":"HDMI 1"}})
                self.assertEqual(response.status,400)
                response=await client.post('/api/media-command',json={"entity_id":"lock.door","action":"turn_on"})
                self.assertEqual(response.status,400)

if __name__=='__main__':unittest.main()
