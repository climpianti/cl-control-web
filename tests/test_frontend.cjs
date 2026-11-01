const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../cl_control_web_next/app/static/assets/app.js'),'utf8');
const sandbox={document:{getElementById:()=>({}),querySelector:()=>null,querySelectorAll:()=>[]},setInterval:()=>{}};
vm.createContext(sandbox);vm.runInContext(source.slice(0,source.lastIndexOf('\nrender();\nPromise.all')),sandbox);
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

test('realtime accepts only matched filtered state events and removals',()=>{
  const changed=run(`(()=>{data=[{entity_id:'light.kitchen',state:'off',attributes:{}}];return applyStateDelta({type:'state',entity_id:'light.kitchen',state:{entity_id:'light.kitchen',state:'on',attributes:{brightness:128}}})})()`);
  assert.equal(changed,true);
  assert.equal(run("data[0].state"),"on");
  assert.equal(run("applyStateDelta({type:'state',entity_id:'light.kitchen',state:{entity_id:'light.else',state:'on',attributes:{}}})"),false);
  assert.equal(run("applyStateDelta({type:'state',entity_id:'light.kitchen',state:null})"),true);
  assert.equal(run("data.length"),0);
  assert.equal(run("applyStateDelta({type:'unknown',entity_id:'light.x',state:null})"),false);
});
test('client transport has a safe reconnect and background polling fallback',()=>{
  assert(source.includes('new WebSocket(url.href)'));
  assert(source.includes('realtimeReady=false'));
  assert(source.includes('!realtimeReady&&refreshAllowed()'));
  assert(source.includes('visibilitychange'));
  assert(!source.includes('SUPERVISOR_TOKEN'));
});


test('SENEC energy data takes priority over circular CL Power Control sensor',()=>{
 const result=JSON.parse(JSON.stringify(run(`(()=>{data=[
 {entity_id:"sensor.senec_house_power",state:"1446.8",attributes:{unit_of_measurement:"W"}},
 {entity_id:"sensor.senec_solar_generated_power",state:"742",attributes:{unit_of_measurement:"W"}},
 {entity_id:"sensor.senec_grid_state_power",state:"12.3",attributes:{unit_of_measurement:"W"}},
 {entity_id:"sensor.cl_power_control_energy_rete",state:"unknown",attributes:{unit_of_measurement:"W"}},
 {entity_id:"sensor.senec_battery_state_power",state:"-347.5",attributes:{unit_of_measurement:"W"}},
 {entity_id:"sensor.senec_battery_charge_percent",state:"63",attributes:{unit_of_measurement:"%"}}
 ];return energy()})()`)));
 assert.equal(result.house.value,1446.8);
 assert.equal(result.house.source,'SENEC');
 assert.equal(result.grid.value,12.3);
 assert.equal(result.battery.value,347.5);
 assert.equal(result.soc.value,63);
 const html=run('energyDashboard()');
 assert.match(html,/Prelievo dalla rete/);
 assert.match(html,/Batteria in scarica/);
 assert.match(html,/Fonte: SENEC/);
});
test('SENEC energy reports unavailable instead of inventing values',()=>{
 const result=JSON.parse(JSON.stringify(run(`(()=>{data=[{entity_id:"sensor.senec_house_power",state:"unavailable",attributes:{unit_of_measurement:"W"}},{entity_id:"sensor.cl_power_control_energy_consumo_casa",state:"unknown",attributes:{unit_of_measurement:"W"}}];return energy()})()`)));
 assert.equal(result.house,null);
 assert.equal(result.solar,null);
 assert.equal(result.grid,null);
 assert.match(run('energyDashboard()'),/Dato non disponibile/);
});
test('Exported power and charging battery direction is explicit',()=>{
 const result=JSON.parse(JSON.stringify(run(`(()=>{data=[{entity_id:"sensor.senec_grid_state_power",state:"-120",attributes:{unit_of_measurement:"W"}},{entity_id:"sensor.senec_battery_state_power",state:"500",attributes:{unit_of_measurement:"W"}}];return energy()})()`)));
 assert.equal(result.grid.value,-120);
 assert.equal(result.battery.value,-500);
 const html=run('energyDashboard()');
 assert.match(html,/Immissione in rete/);
 assert.match(html,/Batteria in carica/);
});


test('mobile navigation has five distinct destinations and represents nested pages',()=>{
 const labels=JSON.parse(JSON.stringify(run('mobileNav.map(([n])=>n)')));
 assert.deepEqual(labels,['Home','Aree','Luci','Energia','Altro']);
 assert.equal(run('mobileNav.length'),5);
 assert.match(run('bottomNavigation()'),/aria-label="Navigazione principale smartphone"/);
 assert.match(run('bottomNavigation()'),/data-page="Altro"/);
 run('page="Area"');
 assert.match(run('bottomNavigation()'),/data-page="Aree" class="selected"/);
 run('page="Multimedia"');
 assert.match(run('bottomNavigation()'),/data-page="Altro" class="selected"/);
});
test('saved scenes stay owned by Core and open its canonical native route',()=>{
 assert.equal(run('CORE_SCENES_PATH'),'/cl-control/light-scenes');
 const page=run('nativeScenesPage()');
 assert(page.includes('href="/cl-control/light-scenes"'));
 assert.match(page,/target="_top"/);
 assert.match(page,/archivio personale per utente/);
 assert(!source.includes('SUPERVISOR_TOKEN'));
 const other=run('morePage()');
 assert(other.includes('data-page="Scenari"'));
});


test('dashboard widgets render only explicit supported kinds',()=>{
 const layout={schema_version:1,revision:1,title:'Villa',widgets:[
 {id:'systems',type:'systems',title:'Sistemi'},
 {id:'areas',type:'areas',title:'Zone'}]};
 const html=run('dynamicHome('+JSON.stringify(layout)+')');
 assert.match(html,/Villa/);
 assert.match(html,/Sistemi/);
 assert.match(html,/Zone/);
 assert(!html.includes('undefined'));
});
test('declarative dashboard editor has non-persistent preview and approval',()=>{
 const html=run('(()=>{dashboardLayout={schema_version:1,revision:0,title:"La tua casa",widgets:[{id:"systems",type:"systems",title:"Sistemi"}]};return renderLayoutEditor()})()');
 assert(html.includes('data-layout-preview'));
 assert(!html.includes('data-layout-save'));
 const draft=run('(()=>{dashboardDraft={schema_version:1,revision:0,title:"La tua casa",widgets:[{id:"systems",type:"systems",title:"Sistemi"}]};return renderLayoutEditor()})()');
 assert(draft.includes('data-layout-save'));
 assert(draft.includes('Anteprima non salvata'));
 assert(source.includes('X-CL-Layout-Confirm'));
});
