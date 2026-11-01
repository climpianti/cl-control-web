"""Beta 7 read-only bridge: permitted state delta, sanitization and fail-closed."""
import unittest
from unittest.mock import patch
from aiohttp import web, WSMsgType
from aiohttp.test_utils import TestClient, TestServer
from cl_control_web_next.app.realtime import filter_state, relay_event
from cl_control_web_next.app.server import create_app


class FilterTests(unittest.TestCase):
    def test_whitelist_uses_same_shape_as_bootstrap(self):
        raw = {"entity_id": "light.camera", "state": "on", "attributes": {
            "friendly_name": "Camera", "brightness": 75, "access_token": "SECRET",
            "latitude": 40.0, "longitude": 14.0, "rgb_color": [1, 2, 3]}}
        filtered = filter_state(raw)
        self.assertEqual(filtered["attributes"], {
            "friendly_name": "Camera", "brightness": 75, "rgb_color": [1, 2, 3]})
        self.assertNotIn("SECRET", str(filtered))

    def test_unsupported_domain_rejected(self):
        for domain in ("person", "lock", "device_tracker", "persistent_notification"):
            self.assertIsNone(filter_state({
                "entity_id": domain + ".secret", "state": "home", "attributes": {}}))
        self.assertIsNone(filter_state("not a state"))

    def test_event_delta_filters_and_validates_entity(self):
        raw = {"type": "event", "event": {"event_type": "state_changed", "data": {
            "entity_id": "sensor.power", "new_state": {
                "entity_id": "sensor.power", "state": "512", "attributes": {
                    "unit_of_measurement": "W", "secret": "SECRET"}}}}}
        self.assertEqual(relay_event(raw), {"type": "state", "entity_id": "sensor.power",
            "state": {"entity_id": "sensor.power", "state": "512",
                      "attributes": {"unit_of_measurement": "W"}}})
        raw["event"]["data"]["new_state"] = None
        self.assertEqual(relay_event(raw), {"type": "state", "entity_id": "sensor.power", "state": None})
        raw["event"]["data"]["entity_id"] = "lock.door"
        self.assertIsNone(relay_event(raw))


class RealtimeRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_socket_fails_closed_without_token(self):
        with patch("cl_control_web_next.app.server.TOKEN", ""):
            async with TestClient(TestServer(create_app())) as client:
                response = await client.get("/api/realtime")
                self.assertEqual(response.status, 503)

    async def test_live_stream_sanitizes_and_never_exposes_token(self):
        async def source(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            await ws.send_json({"type": "auth_required"})
            auth = await ws.receive_json()
            self.assertEqual(auth, {"type": "auth", "access_token": "TOKEN_TEST"})
            await ws.send_json({"type": "auth_ok"})
            sub = await ws.receive_json()
            self.assertEqual(sub["event_type"], "state_changed")
            await ws.send_json({"type": "result", "id": 1, "success": True, "result": None})
            await ws.send_json({"type": "event", "id": 1, "event": {"event_type": "state_changed",
                "data": {"entity_id": "light.kitchen", "new_state": {
                    "entity_id": "light.kitchen", "state": "on",
                    "attributes": {"brightness": 128, "access_token": "HIDDEN"}}}}})
            await ws.send_json({"type": "event", "id": 1, "event": {"event_type": "state_changed",
                "data": {"entity_id": "lock.front_door", "new_state": {
                    "entity_id": "lock.front_door", "state": "unlocked",
                    "attributes": {"code": "PRIVATE"}}}}})
            await ws.close()
            return ws
        upstream_app = web.Application()
        upstream_app.router.add_get("/ws", source)
        async with TestServer(upstream_app) as upstream:
            url = str(upstream.make_url("/ws")).replace("http://", "ws://")
            with patch("cl_control_web_next.app.server.TOKEN", "TOKEN_TEST"), patch(
                "cl_control_web_next.app.server.core_websocket_url", return_value=url
            ):
                async with TestClient(TestServer(create_app())) as client:
                    async with client.ws_connect("/api/realtime") as ws:
                        ready = await ws.receive_json(timeout=3)
                        self.assertEqual(ready, {"type": "ready"})
                        event = await ws.receive_json(timeout=3)
                        self.assertEqual(event["state"]["attributes"], {"brightness": 128})
                        self.assertEqual(event["entity_id"], "light.kitchen")
                        msg = await ws.receive(timeout=3)
                        self.assertIn(msg.type, (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING))

if __name__ == "__main__":
    unittest.main()
