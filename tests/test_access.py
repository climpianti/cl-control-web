"""No customer escalation from headers, no raw IDs in diagnostics."""
import unittest
from unittest.mock import patch, AsyncMock
from aiohttp.test_utils import TestClient, TestServer
from cl_control_web_next.app.access import (
    identity_from_ingress, may_access_customer, access_summary,
)
from cl_control_web_next.app.server import create_app, valid_control


class IngressIdentityTests(unittest.TestCase):
    def test_real_proxy_user_is_authenticated_but_not_promoted_to_admin(self):
        user = "a" * 32
        ctx = identity_from_ingress("172.30.32.2", {"X-Remote-User-Id": user})
        self.assertTrue(ctx.ingress_verified)
        self.assertEqual(ctx.user_id, user)
        self.assertFalse(may_access_customer(ctx, "light.kitchen", "turn_on"))
        self.assertNotIn(user, str(access_summary(ctx)))
        self.assertEqual(access_summary(ctx)["role_verification"], "not_available")

    def test_spoofed_headers_do_not_grant_access(self):
        for host in ("127.0.0.1", "192.168.1.5", None, "invalid"):
            ctx = identity_from_ingress(host, {
                "X-Remote-User-Id": "a" * 32,
                "X-Remote-User-Groups": "system-admin",
            })
            self.assertFalse(ctx.ingress_verified)
            self.assertFalse(may_access_customer(ctx, "light.a", "turn_off"))

    def test_missing_user_or_unsupported_group_is_not_role(self):
        ctx = identity_from_ingress("172.30.32.2", {
            "X-Remote-User-Groups": "system-admin",
        })
        self.assertFalse(ctx.ingress_verified)
        self.assertEqual(access_summary(ctx)["role"], "unverified")


class SecurityRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_access_status_has_no_user_id(self):
        async with TestClient(TestServer(create_app())) as client:
            response = await client.get("/api/access")
            self.assertEqual(response.status, 200)
            data = await response.json()
            self.assertEqual(data["customer_enabled"], False)
            self.assertFalse(data["ingress_verified"])
            self.assertNotIn("user_id", data)

    async def test_media_and_light_revalidate_real_state_before_actuation(self):
        states = [
            {"entity_id": "light.living", "state": "unavailable", "attributes": {}},
            {"entity_id": "media_player.tv", "state": "on",
             "attributes": {"supported_features": 0}},
        ]
        calls = []
        async def upstream(request, method, endpoint, data=None):
            calls.append((method, endpoint))
            if endpoint == "states":
                return states
            if endpoint == "services":
                return [{"domain": "light", "services": {"turn_on": {}}},
                        {"domain": "media_player", "services": {"media_play": {}}}]
            raise AssertionError("No action should reach HA")
        with patch("cl_control_web_next.app.server.ha_request",
                   new=AsyncMock(side_effect=upstream)):
            async with TestClient(TestServer(create_app())) as client:
                for payload in [
                    {"entity_id": "light.living", "action": "turn_on"},
                    {"entity_id": "media_player.tv", "action": "media_play"},
                ]:
                    response = await client.post("/api/command", json=payload)
                    self.assertEqual(response.status, 400)
        self.assertFalse(any("/services/" in p for _, p in calls))


if __name__ == "__main__":
    unittest.main()
