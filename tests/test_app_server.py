"""Security regression checks for Ingress API command validation."""
import unittest
from cl_control_web_next.app.server import valid_control

class CommandTests(unittest.TestCase):
    def test_light_on(self):
        self.assertEqual(valid_control({"entity_id":"light.salone","action":"turn_on","data":{"brightness_pct":50}})[:2],("light","turn_on"))
    def test_rgbw(self):
        self.assertEqual(valid_control({"entity_id":"light.rgbw","action":"turn_on","data":{"rgbw_color":[25,0,200,120]}})[1],"turn_on")
    def test_prohibited_domains(self):
        for eid in ("lock.porta","alarm_control_panel.casa","switch.caldaia","script.apriporta"):
            with self.subTest(eid=eid), self.assertRaises(ValueError):
                valid_control({"entity_id":eid,"action":"turn_on"})
    def test_no_arbitrary_services(self):
        for action in ("toggle","send_command","media_play_media","reload","__import__"):
            with self.subTest(action=action),self.assertRaises(ValueError):
                valid_control({"entity_id":"light.salone","action":action})
    def test_reject_invalid_color(self):
        for value in ([256,0,0,0],[0,0,0],[0,0,0,0,0],["1",2,3,4]):
            with self.subTest(value=value),self.assertRaises(ValueError):
                valid_control({"entity_id":"light.rgbw","action":"turn_on","data":{"rgbw_color":value}})
    def test_reject_conflicting_modes(self):
        with self.assertRaises(ValueError):
            valid_control({"entity_id":"light.rgbw","action":"turn_on","data":{"rgbw_color":[0,0,0,0],"hs_color":[0,100]}})
    def test_reject_unknown_fields(self):
        with self.assertRaises(ValueError):
            valid_control({"entity_id":"light.led","action":"turn_on","data":{"transition":5}})
    def test_reject_bad_volume(self):
        with self.assertRaises(ValueError):
            valid_control({"entity_id":"media_player.salone","action":"volume_set","data":{"volume_level":1.2}})
if __name__=="__main__":
    unittest.main()
