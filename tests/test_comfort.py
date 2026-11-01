import unittest
from cl_control_web_next.app.server import valid_control, validate_live_control

class ComfortTests(unittest.TestCase):
    def check(self, eid, action, data, attrs, state='closed'):
        dom,action,eid,params=valid_control(dict(entity_id=eid,action=action,data=data))
        validate_live_control(dom,action,params,dict(state=state,attributes=attrs),{dom:{action:{}}})
    def test_cover_actions(self):
        for action in ('open_cover','close_cover','stop_cover'):
            self.check('cover.test',action,{},dict(supported_features=15))
        self.check('cover.test','set_cover_position',{'position':50},dict(supported_features=15))
    def test_invalid_position_and_payload(self):
        for value in (-1,101,True,50.5,float('nan')):
            with self.assertRaises(ValueError):
                self.check('cover.test','set_cover_position',{'position':value},dict(supported_features=15))
        with self.assertRaises(ValueError):
            self.check('cover.test','open_cover',{'entity_id':'cover.other'},dict(supported_features=15))
    def test_unavailable_unsupported_and_missing_service(self):
        for state,flags in [('unavailable',15),('unknown',15),('closed',0)]:
            with self.assertRaises(ValueError):
                self.check('cover.test','open_cover',{},dict(supported_features=flags),state)
        with self.assertRaises(ValueError):
            validate_live_control('cover','open_cover',{},dict(state='closed',attributes={'supported_features':15}),{})
    def test_temperature_limits(self):
        a=dict(supported_features=1,min_temp=16,max_temp=28)
        self.check('climate.test','set_temperature',{'temperature':22.7},a,'off')
        for v in (15,29,True,float('inf')):
            with self.assertRaises(ValueError):self.check('climate.test','set_temperature',{'temperature':v},a,'off')
    def test_modes(self):
        a=dict(supported_features=25,hvac_modes=['heat','off'],preset_modes=['comfort'],fan_modes=['low'])
        for key,value in [('hvac_mode','heat'),('preset_mode','comfort'),('fan_mode','low')]:
            self.check('climate.test','set_'+key,{key:value},a,'off')
            with self.assertRaises(ValueError):self.check('climate.test','set_'+key,{key:'invalid'},a,'off')
from unittest.mock import AsyncMock, patch
from aiohttp.test_utils import TestClient, TestServer
from cl_control_web_next.app.server import create_app

class ComfortRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_forward_exact_target_and_revalidate(self):
        state={'entity_id':'cover.test','state':'closed','attributes':{'supported_features':15}}
        writes=[]
        async def upstream(request,method,endpoint,data=None):
            if endpoint=='states':return [state]
            if endpoint=='services':return [{'domain':'cover','services':{'set_cover_position':{}}}]
            writes.append((endpoint,data));return []
        with patch('cl_control_web_next.app.server.ha_request',new=AsyncMock(side_effect=upstream)):
            async with TestClient(TestServer(create_app())) as client:
                payload={'entity_id':'cover.test','action':'set_cover_position','data':{'position':45}}
                response=await client.post('/api/command',json=payload)
                self.assertEqual(response.status,200)
                self.assertEqual(writes,[('services/cover/set_cover_position',{'entity_id':'cover.test','position':45})])
                state['state']='unavailable'
                response=await client.post('/api/command',json=payload)
                self.assertEqual(response.status,400);self.assertEqual(len(writes),1)
