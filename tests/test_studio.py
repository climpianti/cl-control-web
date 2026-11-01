"""Offline, no-network AI Studio draft planner and authorization gates."""
from copy import deepcopy
import unittest
from unittest.mock import patch, AsyncMock
from aiohttp.test_utils import TestClient, TestServer

from cl_control_web_next.app.layout import DEFAULT, validate_layout
from cl_control_web_next.app.studio import intent_draft
from cl_control_web_next.app.server import create_app

STATES = [
    {"entity_id": "light.cucina_led", "attributes": {"friendly_name": "Luci cucina"}, "state": "on"},
    {"entity_id": "light.salone", "attributes": {"friendly_name": "Luce salone"}, "state": "off"},
    {"entity_id": "climate.cucina", "attributes": {"friendly_name": "Clima cucina"}, "state": "heat"},
    {"entity_id": "sensor.senec_solar_generated_power", "attributes": {"friendly_name": "Fotovoltaico"}, "state": "421"},
    {"entity_id": "lock.front_door", "attributes": {"friendly_name": "Porta privata"}, "state": "locked"},
    {"entity_id": "script.open_gate", "attributes": {}, "state": "off"},
]

class OfflineStudioTests(unittest.TestCase):
    def test_language_request_uses_supported_widgets_and_real_devices(self):
        raw = deepcopy(DEFAULT)
        result = intent_draft("Crea una dashboard con luci della cucina, clima ed energia SENEC", STATES, raw)
        self.assertEqual(result["mode"], "offline-rules")
        self.assertTrue(result["supported"])
        widgets = result["draft"]["widgets"]
        self.assertIn("energy", [w["type"] for w in widgets])
        self.assertIn("light.cucina_led", [w.get("entity_id") for w in widgets])
        self.assertNotIn("lock.front_door", str(widgets))
        self.assertEqual(raw, DEFAULT)
        self.assertEqual(result["draft"], validate_layout(result["draft"], {s["entity_id"] for s in STATES}))

    def test_incremental_change_preserves_layout_without_approval(self):
        original = deepcopy(DEFAULT)
        original["revision"] = 4
        result = intent_draft("Aggiungi energia SENEC", STATES, original)
        self.assertEqual(result["draft"]["revision"], 4)
        self.assertEqual(len(result["draft"]["widgets"]), 4)
        self.assertEqual(len(original["widgets"]), 3)

    def test_unsupported_request_preserves_existing_layout(self):
        current = deepcopy(DEFAULT)
        current["revision"] = 2
        result = intent_draft("Spegni antifurto e apri la serratura", STATES, current)
        self.assertFalse(result["supported"])
        self.assertEqual(result["draft"], current)
        result = intent_draft("Crea una dashboard con codice JavaScript arbitrario", STATES, current)
        self.assertFalse(result["supported"])
        self.assertEqual(result["draft"], current)

    def test_prompt_limits_and_no_unknown_entities(self):
        for bad in ("", "x", "a" * 701, 12, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                intent_draft(bad, STATES, DEFAULT)
        result = intent_draft("Aggiungi temperatura e luce della cucina", STATES, DEFAULT)
        for widget in result["draft"]["widgets"]:
            if widget["type"] == "entity":
                self.assertIn(widget["entity_id"], {s["entity_id"] for s in STATES})

class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_requests_denied_before_inventory_fetch(self):
        with patch("cl_control_web_next.app.server.ha_request", new_callable=AsyncMock) as upstream:
            async with TestClient(TestServer(create_app())) as client:
                response = await client.post("/api/studio/draft", json={"instruction": "Crea una dashboard energia"})
                self.assertEqual(response.status, 403)
            upstream.assert_not_awaited()

if __name__ == "__main__":
    unittest.main()
