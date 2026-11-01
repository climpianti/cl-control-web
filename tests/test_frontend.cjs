const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../cl_control_web_next/app/static/assets/app.js'),'utf8');
const sandbox={document:{getElementById:()=>({}),querySelector:()=>null,querySelectorAll:()=>[]},setInterval:()=>{}};
vm.createContext(sandbox);vm.runInContext(source.slice(0,source.lastIndexOf('render();Promise.all')),sandbox);
const run=code=>vm.runInContext(code,sandbox);
test('light tint follows RGB and brightness without darkening the hue twice',()=>{
 const v=JSON.parse(JSON.stringify(run(`lightVisual({state:'on',attributes:{supported_color_modes:['rgb'],rgb_color:[0,50,0],brightness:51}})`)));
 assert.equal(v.rgb,'0 255 0');assert.equal(v.level,.2);
 assert.equal(run(`lightVisual({state:'off',attributes:{supported_color_modes:['brightness']}})`),null);
 assert.equal(run(`lightVisual({state:'on',attributes:{supported_color_modes:['onoff']}})`),null);
});
test('Kelvin and RGBW white channel change the card tint',()=>{
 const warm=run(`lightVisual({state:'on',attributes:{supported_color_modes:['color_temp'],color_mode:'color_temp',color_temp_kelvin:2200}}).rgb`);
 const cool=run(`lightVisual({state:'on',attributes:{supported_color_modes:['color_temp'],color_mode:'color_temp',color_temp_kelvin:6500}}).rgb`);
 assert.notEqual(warm,cool);
 assert.equal(run(`lightVisual({state:'on',attributes:{supported_color_modes:['rgbw'],rgbw_color:[0,0,0,255]}}).rgb`),'255 255 255');
});
test('media cards respect playback capabilities and unavailable state',()=>{
 const off=run(`card({entity_id:'media_player.tv',state:'off',attributes:{supported_features:16437}})`);
 assert.equal((off.match(/disabled/g)||[]).length,4);
 const playing=run(`card({entity_id:'media_player.speaker',state:'playing',attributes:{supported_features:1}})`);
 assert(playing.includes('data-action="media_pause"'));assert(!playing.includes('type="range"'));
 assert.equal((playing.match(/disabled/g)||[]).length,2);
});
test('all lights render compact without embedded ranges, including array positions > 0',()=>{
 assert(!source.includes('.map(card)'));
 const html=run(`[{entity_id:'light.a',state:'on',attributes:{supported_color_modes:['rgbw']}},{entity_id:'light.b',state:'off',attributes:{supported_color_modes:['brightness']}}].map(s=>card(s)).join('')`);
 assert.equal((html.match(/class="light-tile/g)||[]).length,2);assert(!html.includes('type="range"'));
});
test('details respect on/off, dimmer, RGBW and temperature capabilities',()=>{
 for(const [m,n] of [['onoff',0],['brightness',1],['rgbw',3],['color_temp',2]]){
 const html=run(`card({entity_id:'light.a',state:'off',attributes:{supported_color_modes:['${m}']}},true)`);
 assert.equal((html.match(/type="range"/g)||[]).length,n);
 }
});
test('RGBW hue preserves white channel and uses one color mode',()=>{
 const result=JSON.parse(JSON.stringify(run(`colorParams({attributes:{supported_color_modes:['rgbw'],rgbw_color:[255,0,0,123],hs_color:[0,100]}},120)`)));
 assert.deepEqual(result,{rgbw_color:[0,255,0,123]});
});
test('unavailable light is disabled and entity names are escaped',()=>{
 const html=run(`lightTile({entity_id:'light.a',state:'unavailable',attributes:{friendly_name:'<img onerror=x>'}})`);
 assert(html.includes('disabled'));assert(html.includes('&lt;img onerror=x&gt;'));assert(!html.includes('<img'));
});
test('cover controls follow features and retain unknown position',()=>{
 const html=run(`card({entity_id:'cover.test',state:'closed',attributes:{supported_features:15,current_position:0}})`);
 assert.match(html,/open_cover/);assert.match(html,/stop_cover/);assert.match(html,/close_cover/);assert.match(html,/value="0"/);
 const limited=run(`card({entity_id:'cover.test',state:'unavailable',attributes:{supported_features:1}})`);
 assert.match(limited,/disabled/);assert.doesNotMatch(limited,/stop_cover/);assert.match(limited,/Posizione non disponibile/);
});
test('climate controls use entity limits modes and measured temperature',()=>{
 const html=run(`card({entity_id:'climate.test',state:'off',attributes:{supported_features:25,hvac_modes:['heat','off'],preset_modes:['comfort'],fan_modes:['low'],min_temp:16,max_temp:28,target_temp_step:0.1,temperature:22.7,current_temperature:21}})`);
 assert.match(html,/min="16" max="28" step="0.1"/);assert.match(html,/set_hvac_mode/);assert.match(html,/set_preset_mode/);assert.match(html,/set_fan_mode/);assert.match(html,/ambiente: 21/);
});
