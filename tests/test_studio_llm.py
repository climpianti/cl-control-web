"""Opt-in LLM boundary: privacy, SSRF, schema, fallback and no cloud by default."""
import json
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

from cl_control_web_next.app.layout import DEFAULT
from cl_control_web_next.app.studio_llm import (
    provider_status, validate_ollama_url, validate_model_output,
    generate_layout, StudioProviderError, select_inventory,
)
from cl_control_web_next.app.server import create_app
from aiohttp.test_utils import TestClient, TestServer

ENTITIES = [
    {"entity_id": "light.cucina", "state": "on",
     "attributes": {"friendly_name": "Luce cucina", "access_token": "VERY_SECRET"}},
    {"entity_id": "sensor.senec_solar_generated_power", "state": "100",
     "attributes": {"friendly_name": "Produzione FV", "private": "DONOTSHARE"}},
    {"entity_id": "lock.front_door", "state": "locked",
     "attributes": {"friendly_name": "Porta", "code": "1234"}},
]

class ConfigurationTests(unittest.TestCase):
    def test_default_is_offline_no_llm(self):
        self.assertEqual(provider_status({})["provider"], "offline")
        self.assertFalse(provider_status({})["llm_ready"])
        self.assertFalse(provider_status({"ai_provider": "openai", "ai_openai_model": "gpt-4.1",
            "ai_openai_api_key": "sk-secret-example-123456"})["llm_ready"])
        self.assertFalse(provider_status({"ai_provider": "openai", "ai_openai_model": "gpt-4.1",
            "ai_cloud_opt_in": True})["llm_ready"])
        status = provider_status({"ai_provider": "openai", "ai_openai_model": "gpt-4.1",
            "ai_openai_api_key": "sk-secret-example-123456", "ai_cloud_opt_in": True})
        self.assertTrue(status["llm_ready"])
        self.assertNotIn("sk-secret", str(status))

    def test_ssrf_rejects_public_and_special_urls(self):
        for url in ("http://127.0.0.1:11434","http://169.254.169.254:11434",
                    "https://192.168.1.3:11434","http://example.com:11434",
                    "http://8.8.8.8:11434","http://192.168.1.3:80",
                    "http://192.168.1.3:11434/evil","http://user:secret@192.168.1.3:11434",
                    "http://192.168.1.3:11434/?redirect=http://other"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_ollama_url(url)
        self.assertEqual(validate_ollama_url("http://192.168.1.3:11434"),
                         "http://192.168.1.3:11434/api/chat")

    def test_restricted_model_response(self):
        known={"light.cucina"}
        good={"title":"Casa", "widgets":[{"type":"entity","title":"Luce cucina","entity_id":"light.cucina"},
            {"type":"energy","title":"Energia","entity_id":""}]}
        parsed = validate_model_output(json.dumps(good),known,4)
        self.assertEqual(parsed["revision"],4)
        self.assertEqual(len(parsed["widgets"]),2)
        self.assertTrue(all(w["id"].startswith("studio-") for w in parsed["widgets"]))
        for bad in (
            {"title":"Casa","widgets":[{"type":"entity","title":"Hack","entity_id":"lock.front_door"}]},
            {"title":"Casa","widgets":[{"type":"entity","title":"Hack","entity_id":"light.unlisted"}]},
            {"title":"Casa","widgets":[{"type":"energy","title":"Bad","entity_id":"light.cucina"}]},
            {"title":"Casa","widgets":[{"type":"html","title":"Script","entity_id":""}]},
            {"title":"Casa","widgets":[{"type":"energy","title":"Energia","entity_id":"","service":"light.turn_on"}]},
            {"title":"Casa","widgets":[]},
        ):
            with self.subTest(bad=bad), self.assertRaises(StudioProviderError):
                validate_model_output(json.dumps(bad),known,4)

    def test_inventory_has_no_secret_values(self):
        catalog=select_inventory(ENTITIES,"Luce cucina e fotovoltaico")
        self.assertNotIn("VERY_SECRET",str(catalog))
        self.assertNotIn("DONOTSHARE",str(catalog))
        self.assertNotIn("1234",str(catalog))
        self.assertNotIn("lock.front_door",str(catalog))

class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_offline_never_calls_network(self):
        session=AsyncMock()
        result=await generate_layout(session,{}, "Aggiungi energia SENEC", ENTITIES,deepcopy(DEFAULT))
        self.assertEqual(result["provider"],"offline-rules")
        self.assertFalse(result["fallback"])
        session.post.assert_not_called()

    async def test_explicit_disabled_cloud_uses_offline(self):
        session=AsyncMock()
        result=await generate_layout(session,{
            "ai_provider":"openai","ai_openai_model":"gpt-4.1",
            "ai_openai_api_key":"sk-fake-example-123456",
            "ai_cloud_opt_in":False
        },"Aggiungi energia SENEC",ENTITIES,deepcopy(DEFAULT))
        self.assertEqual(result["provider"],"offline-rules")
        self.assertTrue(result["fallback"])
        session.post.assert_not_called()

    async def test_cloud_output_must_validate_before_preview(self):
        session=AsyncMock()
        opts={"ai_provider":"openai","ai_openai_model":"gpt-4.1",
              "ai_openai_api_key":"sk-fake-example-123456","ai_cloud_opt_in":True}
        valid=json.dumps({"title":"La casa","widgets":[{"type":"energy","title":"Energia","entity_id":""}]})
        with patch("cl_control_web_next.app.studio_llm._llm_generate",new=AsyncMock(return_value=valid)) as llm:
            response=await generate_layout(session,opts,"Crea dashboard con energia",ENTITIES,deepcopy(DEFAULT))
            self.assertEqual(response["provider"],"openai")
            self.assertEqual(response["mode"],"llm")
            self.assertFalse(response["fallback"])
            self.assertEqual(response["draft"]["widgets"][0]["type"],"energy")
            llm.assert_awaited_once()

    async def test_malicious_model_output_falls_back(self):
        session=AsyncMock()
        opts={"ai_provider":"ollama","ai_ollama_model":"qwen2.5:7b","ai_ollama_url":"http://192.168.1.3:11434"}
        output=json.dumps({"title":"Hack","widgets":[{"type":"entity","title":"Apri cancello","entity_id":"script.open_gate"}]})
        with patch("cl_control_web_next.app.studio_llm._llm_generate",new=AsyncMock(return_value=output)):
            result=await generate_layout(session,opts,"Aggiungi energia SENEC",ENTITIES,deepcopy(DEFAULT))
            self.assertEqual(result["provider"],"offline-rules")
            self.assertTrue(result["fallback"])
            self.assertNotIn("script.open_gate",str(result))

class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_access_to_status_denied(self):
        async with TestClient(TestServer(create_app())) as client:
            r=await client.get("/api/studio/status")
            self.assertEqual(r.status,403)

if __name__ == "__main__":
    unittest.main()
