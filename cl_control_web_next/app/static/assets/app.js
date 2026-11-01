const el=document.getElementById("app"), esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const SYMBOLS=Object.fromEntries(Object.entries({"home":"M3 11 12 3l9 8M5 10v11h5v-7h4v7h5V10","light":"M9 18h6m-6 3h6M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 2H9s0-1-1-2","cover":"M3 21V3h18v18M6 7h12M6 11h12M6 15h12M12 15v5","climate":"M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0M12 8v10","security":"m12 3 9 4v5c0 5-9 10-9 10S3 17 3 12V7l9-4Zm-4 9 3 3 5-6","camera":"M3 7h12v11H3zM15 11l6-4v11l-6-4","media":"M3 4h18v16H3zM10 8l6 4-6 4z","scene":"M12 3a9 9 0 1 0 0 18c4 0 0-5 4-5h2c5 0 4-13-6-13ZM7 9h.01M12 6h.01M17 9h.01M7 14h.01","energy":"m13 2-9 12h7l-1 8 10-13h-7z","irrigation":"M12 13v9M8 22h8M3 5l2 2M8 3l1 3M16 3l-1 3M21 5l-2 2M3 12h3M18 12h3M8 10l4-3 4 3","area":"m12 3 10 6-10 6L2 9Zm-10 11 10 6 10-6M2 18l10 6 10-6","support":"M3 14v-3a9 9 0 0 1 18 0v3M3 12h4v8H3zM17 12h4v8h-4zM17 20c0 2-3 2-5 2","back":"m15 4-8 8 8 8"}).map(([key,path])=>[key,'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+path+'"/></svg>']));
const nav=[["Home","home"],["Aree","area"],["Luci","light"],["Aperture","cover"],["Clima","climate"],["Multimedia","media"],["Energia","energy"],["Sicurezza","security"],["Scenari","scene"],["Personalizza","scene"],["AI Studio","scene"],["Assistenza","support"]];
let remoteId="", remoteTrigger=null, mediaProfiles=[], mediaError="";
let detailId="", detailTrigger=null;
let page="Home",areaId="",search="",data=[],areas=[],error="",busy=false;
let dashboardLayout=null,dashboardDraft=null,layoutMessage="",layoutSaving=false;
let layoutCatalog=null,layoutValidated=false;
let studioInstruction="",studioExplanation="",studioBusy=false,studioSupported=false;
const layoutTypes=[["systems","Sistemi"],["areas","Aree"],["cl_systems","Sistemi CL"],["energy","Energia"],["entity","Singola entità"]];
function cloneLayout(v){return JSON.parse(JSON.stringify(v))}
function getEditorDraft(){if(!dashboardDraft&&dashboardLayout)dashboardDraft=cloneLayout(dashboardLayout);return dashboardDraft}
function editLayoutDraft(mutator){
 const next=cloneLayout(getEditorDraft());
 mutator(next);
 dashboardDraft=next;layoutValidated=false;
 layoutMessage="Modifiche locali da verificare. Nessun salvataggio effettuato.";
 render();
}
function draftWidgetId(draft){
 let n=1;while(draft.widgets.some(w=>w.id==="widget-"+n))n++;
 return "widget-"+n;
}
function addLayoutWidget(type){
 if(!layoutTypes.some(pair=>pair[0]===type))return;
 if(!getEditorDraft()||dashboardDraft.widgets.length>=24){layoutMessage="Massimo 24 widget";render();return}
 const ids=layoutCatalog?.entities||[];
 if(type==="entity"&&!ids.length){layoutMessage="Nessuna entità compatibile disponibile";render();return}
 editLayoutDraft(d=>{
   const widget={id:draftWidgetId(d),type,title:layoutTypes.find(x=>x[0]===type)[1]};
   if(type==="entity")widget.entity_id=ids[0].entity_id;
   d.widgets.push(widget);
 });
}
function moveLayoutWidget(index,direction){
 const d=getEditorDraft();const target=index+direction;
 if(!d||target<0||target>=d.widgets.length)return;
 editLayoutDraft(x=>{[x.widgets[index],x.widgets[target]]=[x.widgets[target],x.widgets[index]]});
}
function removeLayoutWidget(index){
 const d=getEditorDraft();
 if(!d||d.widgets.length<=1){layoutMessage="La dashboard deve contenere almeno un widget";render();return}
 editLayoutDraft(x=>x.widgets.splice(index,1));
}
async function loadCatalog(){
 try{layoutCatalog=await api("layout/catalog");render()}
 catch(e){layoutCatalog=null;layoutMessage="Catalogo widget non disponibile: "+e.message;render()}
}

async function loadLayout(){
 try{const r=await api("layout");dashboardLayout=r.layout;render()}
 catch(e){layoutMessage="Configurazione dashboard non raggiungibile";render()}
}
const iconForWidget={systems:"area",areas:"area",cl_systems:"energy",energy:"energy",entity:"light"};
function widgetHtml(widget){
 const title=esc(widget.title);
 if(widget.type==="entity"){
  const item=byId(widget.entity_id);
  return '<section class="section-block layout-widget"><h2>'+title+'</h2>'+
   (item?'<div class="devices">'+card(item)+'</div>':'<p class="empty">Entità non disponibile</p>')+'</section>';
 }
 if(widget.type==="energy")return '<section class="section-block layout-widget"><h2>'+title+'</h2><div class="cl-grid">'+
  tile("Consumo",fmtPower(energy().house),"energy","Energia")+
  tile("Fotovoltaico",fmtPower(energy().solar),"energy","Energia")+'</div></section>';
 if(widget.type==="areas")return '<section class="section-block layout-widget"><h2>'+title+'</h2><div class="area-grid">'+cardsForArea()+'</div></section>';
 if(widget.type==="systems"){
  const descriptors=[["Luci",status("light"),"light","Luci"],["Aperture",status("cover"),"cover","Aperture"],["Clima",status("climate"),"climate","Clima"],["Multimedia",status("media_player"),"media","Multimedia"]];
  return '<section class="section-block layout-widget"><h2>'+title+'</h2><div class="system-grid">'+descriptors.map(x=>tile(...x)).join("")+'</div></section>';
 }
 if(widget.type==="cl_systems")return '<section class="section-block layout-widget"><h2>'+title+'</h2><div class="cl-grid">'+
 tile("Energia",fmtPower(energy().house),"energy","Energia")+
 tile("Irrigazione",named("sensor.cl_irrigation_stato_sistema")||"Non disponibile","irrigation","Irrigazione")+'</div></section>';
 return "";
}
function dynamicHome(layout){
 return '<section class="welcome"><h2>'+esc(layout.title)+'</h2><p>CL Control · Layout personalizzato</p></section>'+
 '<div class="tri dynamic-widgets">'+layout.widgets.map(widgetHtml).join("")+'</div>';
}
function renderStudio(){
 const examples=["Crea una dashboard per le aree con luci e fotovoltaico","Aggiungi energia e batteria SENEC","Mostra il clima, i sensori di temperatura e le luci della cucina"];
 return '<section class="studio-panel"><div class="studio-heading"><h2>CL Control AI Studio</h2>'+
 '<span class="studio-mode">Motore locale sperimentale · AI generativa non collegata</span></div>'+
 '<p>Descrivi come desideri la dashboard. Il pianificatore usa solo le entità presenti in Home Assistant e non controlla alcun dispositivo.</p>'+
 '<form id="studio-form"><label for="studio-prompt">Richiesta in linguaggio naturale</label>'+
 '<textarea id="studio-prompt" maxlength="700" required minlength="3" rows="4" placeholder="Es. Crea una dashboard con luci, clima ed energia SENEC">'+esc(studioInstruction)+'</textarea>'+
 '<button type="submit" class="action" '+(studioBusy?'disabled':'')+'>Genera proposta</button></form>'+
 '<div class="studio-examples">'+examples.map(v=>'<button type="button" data-studio-example="'+esc(v)+'">'+esc(v)+'</button>').join("")+'</div>'+
 (studioExplanation?'<p class="studio-response" role="status">'+esc(studioExplanation)+'</p>':'')+
 (dashboardDraft&&studioSupported?'<div class="studio-next"><p>Proposta creata, ma non salvata. Puoi modificarla nell’editor e verificarla prima dell’approvazione.</p><button type="button" class="action" data-studio-editor>Apri nell’editor</button></div>':'')+
 '</section>';
}
async function generateStudioDraft(){
 const instruction=studioInstruction.trim();
 if(instruction.length<3||instruction.length>700){studioExplanation="Inserisci una richiesta tra 3 e 700 caratteri.";render();return}
 studioBusy=true;studioExplanation="Analisi locale in corso…";render();
 try{
  const res=await api("studio/draft",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({instruction})});
  if(res.provider!=="offline-rules"||!res.draft)throw Error("Risposta inattesa");
  studioSupported=Boolean(res.supported);
  studioExplanation=res.explanation||"Proposta ricevuta";
  if(studioSupported){
   dashboardDraft=cloneLayout(res.draft);
   dashboardDraft.revision=dashboardLayout?.revision||0;
   layoutValidated=false;
   layoutMessage="Proposta AI Studio locale, da verificare con il server prima di salvare.";
  }
 }catch(e){studioExplanation="Generazione non disponibile: "+e.message;studioSupported=false}
 finally{studioBusy=false;render()}
}
function renderLayoutEditor(){
 const selected=dashboardDraft||dashboardLayout;
 if(!selected)return '<p>Layout non disponibile.</p>';
 const editing=!!dashboardDraft,entityOptions=layoutCatalog?.entities||[];
 const controls=selected.widgets.map((w,i)=>{
  const options=entityOptions.map(e=>'<option value="'+esc(e.entity_id)+'"'+(w.entity_id===e.entity_id?' selected':'')+'>'+esc(e.name+' · '+e.entity_id)+'</option>').join('');
  const type=layoutTypes.find(x=>x[0]===w.type)?.[1]||"Non supportato";
  return '<div class="layout-edit-row" data-widget-row="'+i+'"><div class="layout-edit-head"><strong>'+esc(type)+'</strong><span>'+(i+1)+'/'+selected.widgets.length+'</span></div>'+
   '<label>Titolo<input aria-label="Titolo widget '+(i+1)+'" data-edit-title="'+i+'" maxlength="64" value="'+esc(w.title)+'"></label>'+
   (w.type==="entity"?'<label>Entità<select aria-label="Entità widget '+(i+1)+'" data-edit-entity="'+i+'">'+options+'</select></label>':'')+
   '<div class="layout-edit-buttons"><button type="button" data-move-widget="'+i+'" data-direction="-1" '+(i===0?'disabled':'')+' aria-label="Sposta su widget '+(i+1)+'">↑ Su</button>'+
   '<button type="button" data-move-widget="'+i+'" data-direction="1" '+(i===selected.widgets.length-1?'disabled':'')+' aria-label="Sposta giù widget '+(i+1)+'">↓ Giù</button>'+
   '<button type="button" data-remove-widget="'+i+'" '+(selected.widgets.length===1?'disabled':'')+' aria-label="Rimuovi widget '+(i+1)+'">Rimuovi</button></div></div>';
 }).join('');
 const choices=layoutTypes.map(([type,label])=>'<button type="button" data-add-widget="'+esc(type)+'"'+(!layoutCatalog||selected.widgets.length>=24?' disabled':'')+'>+ '+esc(label)+'</button>').join('');
 return '<section class="layout-editor"><div class="layout-editor-head"><h2>Personalizza dashboard</h2><p>Le modifiche rimangono locali fino ad anteprima validata e approvazione. Nessun dispositivo viene comandato.</p></div>'+
 '<div class="layout-editor-grid"><div class="layout-editor-controls"><label class="layout-title-label">Titolo dashboard<input data-layout-title maxlength="64" value="'+esc(selected.title)+'"></label>'+
 '<h3>Widget ('+selected.widgets.length+'/24)</h3><div class="layout-edit-rows">'+controls+'</div><h3>Aggiungi widget</h3><div class="layout-add-buttons">'+choices+'</div>'+
 '<div class="layout-editor-actions"><button class="action" type="button" data-layout-preview>Verifica anteprima</button>'+
 (editing?'<button class="action" type="button" data-layout-save '+(!layoutValidated||layoutSaving?'disabled':'')+'>Approva e salva</button><button class="action" type="button" data-layout-cancel>Annulla modifiche</button>':'')+
 '<button class="action" type="button" data-layout-suggest>Proponi automaticamente</button></div>'+
 '<p class="layout-message" role="status">'+esc(layoutMessage||"Modifica l'ordine e le proprietà dei widget.")+'</p>'+
 '<p class="layout-message">Revisione attiva: '+Number(dashboardLayout?.revision||0)+' · '+(layoutValidated?"Anteprima verificata, non salvata":editing?"Modifiche da verificare":"Nessuna modifica in corso")+'</p></div>'+
 '<div class="layout-editor-preview"><h3>Anteprima non interattiva</h3><div class="layout-preview-shield" inert aria-label="Anteprima dashboard, comandi disabilitati">'+
 '<div class="tri dynamic-widgets">'+selected.widgets.map(widgetHtml).join("")+'</div></div></div></div></section>';
}
async function previewDashboard(suggest=false){
 if(layoutSaving)return;
 try{
  const payload=suggest?{suggest:true}:{layout:dashboardDraft||dashboardLayout};
  const res=await api("layout/preview",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(suggest)dashboardDraft=res.layout;
  else if(!dashboardDraft)dashboardDraft=cloneLayout(res.layout);
  layoutValidated=true;
  layoutMessage="Anteprima verificata dal server. Puoi approvare e salvare.";
 }catch(e){layoutValidated=false;layoutMessage="Verifica fallita: "+e.message;}
 render();
}
async function saveDashboard(){
 if(!dashboardDraft||layoutSaving||!layoutValidated)return;
 if(!window.confirm("Salvare questo layout come dashboard attiva per l’impianto?"))return;
 layoutSaving=true;render();
 try{const res=await api("layout/save",{method:"POST",headers:{"Content-Type":"application/json","X-CL-Layout-Confirm":"yes"},body:JSON.stringify({layout:dashboardDraft,expected_revision:dashboardLayout?.revision||0})});
 dashboardLayout=res.layout;dashboardDraft=null;layoutValidated=false;layoutMessage="Dashboard salvata. Riapri Home per visualizzarla.";
 }catch(e){layoutMessage="Salvataggio non riuscito: "+e.message;}
 finally{layoutSaving=false;render();}
}

const mobileNav=[["Home","home"],["Aree","area"],["Luci","light"],["Energia","energy"],["Altro","area"]];
const CORE_SCENES_PATH="/cl-control/light-scenes";
function nativeScenesPage(){
 return '<section class="native-scenes"><div class="native-scenes-icon">'+SYMBOLS.scene+'</div>'+
 '<h2>Scenari e preferiti CL Control</h2>'+
 '<p>Gli scenari “Fotografa e salva” e i preferiti luminosità/colore sono gestiti dall’integrazione CL Control Core, con archivio personale per utente e verifica delle autorizzazioni.</p>'+
 '<a class="native-scenes-link" href="'+CORE_SCENES_PATH+'" target="_top" rel="noopener">Apri scenari nel CL Control Core</a>'+
 '<p class="native-scenes-note">Il collegamento apre la dashboard nativa Home Assistant. Non vengono copiati scenari, preferiti, credenziali o autorizzazioni nella Web App.</p></section>';
}
function morePage(){
 return '<h2>Tutti i sistemi</h2><div class="system-grid more-systems">'+
 nav.filter(item=>!["Home","Aree","Luci","Energia"].includes(item[0]))
 .map(([name,icon])=>tile(name,"Apri sezione",icon,name)).join("")+
 '</div>';
}
function bottomNavigation(){
 return '<nav class="bottom-nav" aria-label="Navigazione principale smartphone">'+
 mobileNav.map(([name,icon])=>{
 const active=(name==="Aree"&&page==="Area")||name===page||
 (name==="Altro"&&!["Home","Aree","Area","Luci","Energia"].includes(page));
 return '<button type="button" data-page="'+esc(name)+'" class="'+(active?"selected":"")+'"'+
 (active?' aria-current="page"':'')+' aria-label="'+esc(name)+'">'+SYMBOLS[icon]+'<span>'+esc(name)+'</span></button>';
 }).join("")+'</nav>';
}

const by=d=>data.filter(s=>s.entity_id.startsWith(d+".")), valid=s=>s&&!["unknown","unavailable","none"].includes(s.state),byId=id=>data.find(s=>s.entity_id===id),name=s=>s?.attributes?.friendly_name||s?.entity_id||"",count=(d,fn)=>by(d).filter(fn).length;
const named=(id)=>byId(id)?.state;
const status=(domain)=>{const s=by(domain),available=s.filter(valid);if(!s.length)return "Nessun dispositivo";if(!available.length)return "Dati non disponibili";if(domain==="light")return count("light",x=>x.state==="on")?count("light",x=>x.state==="on")+" accese":"Tutte spente";if(domain==="cover")return count("cover",x=>x.state==="open"||x.state==="opening")?count("cover",x=>x.state==="open"||x.state==="opening")+" aperte":"Tutte chiuse";if(domain==="climate")return available.some(x=>x.state!=="off")?"Climatizzazione attiva":"Tutto spento";if(domain==="media_player")return count(domain,x=>x.state==="playing")?count(domain,x=>x.state==="playing")+" in riproduzione":"Nessuna riproduzione";if(domain==="camera")return available.length+" disponibili";return available.length+" dispositivi"};
const metric=(ids)=>{for(const id of ids){const s=byId(id);if(valid(s)&&Number.isFinite(Number(s.state)))return {value:Number(s.state),unit:s.attributes?.unit_of_measurement||""}}return null};
const fmtPower=m=>m?((m.unit==="W"&&Math.abs(m.value)>=1000)?(m.value/1000).toLocaleString("it-IT",{maximumFractionDigits:2})+" kW":m.value.toLocaleString("it-IT",{maximumFractionDigits:1})+" "+m.unit):"Dato non disponibile";
function energyReading(sources){
 for(const [id,source] of sources){
  const item=byId(id);
  if(!valid(item)||!Number.isFinite(Number(item.state))||item.state.trim()==="")continue;
  const unit=item.attributes?.unit_of_measurement||"W";
  if(unit!=="W"&&unit!=="kW"&&unit!=="%")continue;
  return {value:Number(item.state)*(unit==="kW"?1000:1),unit:unit==="kW"?"W":unit,source};
 }
 return null;
}
function energy(){
 // SENEC is the primary independent source. Derived CL values are only fallbacks.
 // SENEC grid: positive=import, negative=export. Battery state: negative=discharge.
 const house=energyReading([["sensor.senec_house_power","SENEC"],["sensor.cl_power_control_energy_consumo_casa","CL Power Control"],["sensor.consumo_casa_mia","Misuratore casa"]]);
 const solar=energyReading([["sensor.senec_solar_generated_power","SENEC"],["sensor.cl_power_control_energy_fotovoltaico","CL Power Control"]]);
 const grid=energyReading([["sensor.senec_grid_state_power","SENEC"],["sensor.cl_power_control_energy_rete","CL Power Control"]]);
 const soc=energyReading([["sensor.senec_battery_charge_percent","SENEC"],["sensor.cl_power_control_energy_soc_batteria","CL Power Control"]]);
 const rawBattery=energyReading([["sensor.senec_battery_state_power","SENEC"]]);
 const fallbackBattery=energyReading([["sensor.cl_power_control_energy_batteria","CL Power Control"]]);
 const battery=rawBattery?{...rawBattery,value:-rawBattery.value}:fallbackBattery;
 const control=byId("sensor.cl_power_control_energy_control_stato");
 const loadCount=byId("sensor.cl_power_control_carichi_configurati");
 return {house,solar,grid,battery,soc,control:valid(control)?control.state:"Dato non disponibile",
  loadCount:valid(loadCount)?loadCount.state:"—"};
}
function energyDashboard(){
 const e=energy();
 const card=(heading,reading,detail="")=>'<article class="device-card energy-overview-card"><strong>'+esc(heading)+'</strong><p class="energy-value">'+esc(fmtPower(reading))+'</p><small class="energy-source">'+esc(reading?.source?"Fonte: "+reading.source:"Nessun sensore disponibile")+'</small>'+(detail?'<p class="energy-detail">'+esc(detail)+'</p>':"")+'</article>';
 const gridDetail=e.grid?(e.grid.value>=0?"Prelievo dalla rete":"Immissione in rete"):"Direzione non disponibile";
 const batteryDetail=e.battery?(e.battery.value>0?"Batteria in scarica":e.battery.value<0?"Batteria in carica":"Batteria in standby"):"Stato non disponibile";
 const power=m=>m?{...m,value:Math.abs(m.value)}:null;
 const flows='<div class="energy-flow" aria-label="Flussi energetici"><span>☀ Fotovoltaico<br><strong>'+esc(fmtPower(e.solar))+'</strong></span><span>⌂ Casa<br><strong>'+esc(fmtPower(e.house))+'</strong></span><span>⚡ Rete<br><strong>'+esc(fmtPower(power(e.grid)))+'</strong><small>'+esc(gridDetail)+'</small></span><span>▣ Batteria<br><strong>'+esc(fmtPower(power(e.battery)))+'</strong><small>'+esc(batteryDetail)+'</small></span></div>';
 const info='<div class="energy-note">Valori istantanei letti dalle entità di Home Assistant. Non vengono stimati bilanci energetici quando i sensori non coincidono. '+esc(e.control==="Attivo"?"CL Power Control Energy Control attivo":e.control==="Dato non disponibile"?"Stato Energy Control non disponibile":"CL Power Control: "+e.control)+'. Carichi configurati: '+esc(e.loadCount)+'.</div>';
 return '<h2>Energia in tempo reale</h2>'+flows+'<div class="devices energy-devices">'+card("Consumo casa",e.house)+card("Produzione fotovoltaica",e.solar)+card("Rete elettrica",power(e.grid),gridDetail)+card("Potenza batteria",power(e.battery),batteryDetail)+card("Batteria SOC",e.soc)+'</div>'+info;
}

const tile=(title,subtitle,icon,target,cls="")=>'<button class="mini '+cls+'" data-page="'+esc(target)+'"><span class="mini-icon">'+(SYMBOLS[icon]||"◇")+'</span><span class="mini-txt"><strong>'+esc(title)+'</strong><small>'+esc(subtitle)+'</small></span></button>';
function areaMetric(a,kind){let ids=a.entities||[];let explicit=ids.filter(id=>kind==="temp"?/temperat|temperature|climate/i.test(id):/umid|humid/i.test(id));let match=explicit.map(byId).find(s=>valid(s)&&s.attributes?.unit_of_measurement===(kind==="temp"?"°C":"%")&&!/shelly.*temperatura|battery|batteria|cpu|intern/.test(s.entity_id));if(!match)return "";const v=Number(match.state);return Number.isFinite(v)?v.toLocaleString("it-IT",{maximumFractionDigits:1})+(kind==="temp"?" °C":" %"):""}
const cardsForArea=()=>areas.map(a=>{let temperature=areaMetric(a,"temp"),hum=areaMetric(a,"humidity");return '<button class="area-tile" data-area="'+esc(a.id)+'"><span class="area-glyph">'+(SYMBOLS.area)+'</span><span><strong>'+esc(a.name)+'</strong><small>'+(temperature?esc(temperature):"")+(temperature&&hum?" · ":"")+(hum?esc(hum):"")+(temperature||hum?"":"Apri area")+'</small></span></button>'}).join("");
const secureState=()=>{const a=by("alarm_control_panel").filter(valid);return a.length?a[0].state.replaceAll("_"," "):"Stato non disponibile"};
function home(){let E=energy(),cycle=named("binary_sensor.cl_irrigation_ciclo_in_esecuzione"),irrig=named("sensor.cl_irrigation_stato_sistema"),scenes=by("scene").length,ww=by("weather").find(valid);
let wheather=ww&&Number.isFinite(Number(ww.attributes.temperature))?Number(ww.attributes.temperature).toLocaleString("it-IT",{maximumFractionDigits:1})+" °C":"Meteo non configurato";
const summ=[["Luci",status("light"),"light"],["Aperture",status("cover"),"cover"],["Clima",status("climate"),"climate"],["Sicurezza",secureState(),"security"],["Telecamere",status("camera"),"camera"],["Multimedia",status("media_player"),"media"],["Scenari luci",scenes?scenes+" disponibili":"Da configurare","scene"],["Energia",fmtPower(E.house),"energy"]];
const targets=["Luci","Aperture","Clima","Sicurezza","Sicurezza","Multimedia","Scenari","Energia"];
let greeting=new Date().getHours()<12?"Buongiorno":new Date().getHours()<18?"Buon pomeriggio":"Buonasera";
return '<div class="top-summary"><div><strong>CL Control</strong><small>Casa</small></div><span class="top-weather"><span>☀</span><span><strong>'+esc(wheather)+'</strong><small>'+esc(ww?.state||"Meteo non disponibile")+'</small></span></span></div>'+
'<section class="welcome"><h2>'+greeting+', benvenuto in CL Control <span>👋</span></h2><p>La tua casa, tutte le tecnologie, un unico controllo.</p></section>'+
'<div class="tri"><section class="section-block"><h2>▦ &nbsp;Sistemi</h2><div class="system-grid">'+summ.map((x,i)=>tile(x[0],x[1],x[2],targets[i])).join("")+'</div></section>'+
'<section class="section-block"><h2>◇ &nbsp;Aree</h2><div class="area-grid">'+cardsForArea()+'</div></section>'+
'<section class="section-block"><h2>▦ &nbsp;Sistemi CL</h2><div class="cl-grid">'+tile("Irrigazione",cycle==="on"?"Ciclo in corso":irrig&&irrig!=="unknown"?irrig:"In attesa","irrigation","Irrigazione","cl-tile")+tile("Energia","Casa: "+fmtPower(E.house)+" · FV: "+fmtPower(E.solar),"energy","Energia","cl-tile")+tile("Stato impianto",error?"Connessione da verificare":data.length?"Home Assistant connesso":"In attesa di dati","security","Sicurezza","cl-tile")+'</div></section></div>'}
function card(s, expanded=false){if(/^(cover|climate)\./.test(s.entity_id))return comfortCard(s);if(s.entity_id.startsWith("media_player."))return mediaCard(s);if(s.entity_id.startsWith("light.")&&!expanded)return lightTile(s);let d=s.entity_id.split(".")[0],a=s.attributes||{},c=a.supported_color_modes||[],isLight=d==="light",m=d==="media_player",on=s.state==="on",ok=valid(s);let buttons=[];if(isLight)buttons.push(button(s.entity_id,on?"turn_off":"turn_on",on?"Spegni":"Accendi",ok));if(m){let f=a.supported_features||0;buttons.push(button(s.entity_id,"media_previous_track","⏮",ok&&!!(f&16)),button(s.entity_id,s.state==="playing"?"media_pause":"media_play",s.state==="playing"?"Pausa":"Riproduci",ok&&!!(f&(s.state==="playing"?1:16384))),button(s.entity_id,"media_next_track","⏭",ok&&!!(f&32)))}
let ranges=[];if(isLight){if(c.some(x=>["brightness","rgb","rgbw","rgbww","color_temp","hs","xy"].includes(x)))ranges.push(slider(s,"brightness_pct","Luminosità",1,100,Math.round((a.brightness||0)/255*100)));if(c.some(x=>["hs","rgb","rgbw","rgbww","xy"].includes(x)))ranges.push(slider(s,"hs_color","Tonalità colore",0,360,Math.round(a.hs_color?.[0]||0)));if(c.includes("rgbw"))ranges.push(slider(s,"rgbw_color","Bianco W",0,255,a.rgbw_color?.[3]||0));if(c.includes("color_temp"))ranges.push(slider(s,"color_temp_kelvin","Temperatura bianco",a.min_color_temp_kelvin||2000,a.max_color_temp_kelvin||6500,a.color_temp_kelvin||3000));}
if(m&&(a.supported_features&4))ranges.push(slider(s,"volume_level","Volume",0,100,Math.round((a.volume_level||0)*100)));
return '<article class="device-card"><div class="device-head"><span class="device-icon">'+(SYMBOLS[d==="media_player"?"media":d]||"◈")+'</span><div><strong>'+esc(name(s))+'</strong><small>'+(isLight?esc(ok?(on?"Accesa":"Spenta"):"Non disponibile"):esc(s.state))+(a.media_title?" · "+esc(a.media_title):"")+'</small></div></div><div class="actions">'+buttons.join("")+'</div>'+ranges.join("")+'</article>';}

function mediaCard(s){
 const a=s.attributes||{},f=a.supported_features||0,playing=s.state==='playing',off=s.state==='off',ok=valid(s)&&!off,tv=a.device_class==='tv';
 const state=({playing:'In riproduzione',paused:'In pausa',idle:'Pronto',off:'Spento',standby:'In standby',unavailable:'Non disponibile',unknown:'Non disponibile'})[s.state]||s.state;
 const icon=(path)=>'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+path+'"/></svg>';
 const control=(action,title,path,enabled,primary=false)=>'<button class="media-control '+(primary?'media-primary':'')+'" aria-label="'+title+' '+esc(name(s))+'" title="'+title+'" data-entity="'+esc(s.entity_id)+'" data-action="'+action+'" '+(!enabled?'disabled':'')+'>'+icon(path)+'</button>';
 return '<article class="media-card '+(playing?'is-playing ':'')+(!ok?'is-inactive':'')+'"><div class="media-identity"><span class="media-device-icon">'+icon(tv?'M3 4h18v13H3zM8 21h8M12 17v4':'M6 2h12v20H6zM10 6h4M9 15a3 3 0 1 0 6 0 3 3 0 1 0-6 0')+'</span><div><h3>'+esc(name(s))+'</h3><p>'+esc(ok?(a.media_title||a.source||state):state)+'</p>'+(a.media_artist?'<small>'+esc(a.media_artist)+'</small>':'')+'</div></div><div class="media-art" aria-hidden="true">'+(tv?'<span>TV</span><small>HOME CINEMA</small>':icon('M9 18V5l11-2v12M9 9l11-2M9 18a3 3 0 1 1-3-3c2 0 3 1 3 3Zm11-3a3 3 0 1 1-3-3c2 0 3 1 3 3Z'))+'</div><div class="media-transport">'+control('media_previous_track','Precedente','M6 5v14M19 5l-10 7 10 7z',ok&&!!(f&16))+control(playing?'media_pause':'media_play',playing?'Pausa':'Riproduci',playing?'M8 5v14M16 5v14':'m8 4 12 8-12 8z',ok&&!!(f&(playing?1:16384)),true)+control('media_next_track','Successivo','M18 5v14M5 5l10 7-10 7z',ok&&!!(f&32))+'</div><div class="media-bottom"><span class="media-status"><i></i>'+esc(state)+'</span>'+((f&4)?'<div class="media-volume"><span aria-hidden="true">'+icon('m11 4-6 5H2v6h3l6 5zM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14')+'</span>'+slider({...s,state:ok?s.state:'unavailable'},'volume_level','Volume',0,100,Math.round((a.volume_level||0)*100))+'<span class="volume-number">'+Math.round((a.volume_level||0)*100)+'%</span></div>':'')+'</div><button class="remote-open" data-remote="'+esc(s.entity_id)+'" aria-label="Telecomando '+esc(name(s))+'" aria-haspopup="dialog">Telecomando <span aria-hidden="true">⌘</span></button></article>';
}


async function loadMediaProfiles(){try{const r=await api('media-profiles');mediaProfiles=r.profiles||[];mediaError=''}catch{mediaProfiles=[];mediaError='Rilevamento comandi non disponibile. Riprova.'}}
function closeRemote(){remoteId='';document.querySelector('#media-dialog')?.remove();render();document.querySelectorAll('[data-remote]').forEach(b=>{if(b.dataset.remote===remoteTrigger?.dataset.remote)b.focus()})}
async function openRemote(id){remoteId=id;remoteTrigger=document.activeElement;showRemote(true);await loadMediaProfiles();if(remoteId===id)showRemote()}
function showRemote(loading=false,feedback=''){
 const s=byId(remoteId);if(!s)return closeRemote();const p=mediaProfiles.find(p=>p.entity_id===remoteId),a=s.attributes||{};
 const btn=(action,label,params={},cls='')=>'<button aria-label="'+esc(({up:'Su',down:'Giù',left:'Sinistra',right:'Destra',ok:'Conferma'})[params.key]||label)+'" class="remote-key '+cls+'" data-remote-action="'+esc(action)+'" data-params="'+esc(JSON.stringify(params))+'" '+(!p||!p.available||(!p.powered&&action!=='turn_on')||!(action==='key'?p.keys.includes(params.key):p.actions.includes(action))?'disabled':'')+'>'+esc(label)+'</button>';
 let body='<div class="dialog-top"><span>TELECOMANDO</span><button class="dialog-close" aria-label="Chiudi telecomando">×</button></div><h2>'+esc(name(s))+'</h2>';
 if(loading)body+='<p role="status">Rilevamento dei comandi…</p>';
 else if(mediaError||!p)body+='<p role="alert">'+esc(mediaError||'Dispositivo non trovato')+'</p><button class="action" id="retry-remote">Riprova</button>';
 else{
 body+='<p class="remote-note">'+(p.available?(p.powered?'Comandi rilevati automaticamente':'Dispositivo spento'): 'Dispositivo non disponibile')+'</p><div class="remote-row">'+btn('turn_on','Accendi')+btn('turn_off','Spegni')+'</div>';
 if(p.keys.length)body+='<div class="remote-dpad">'+btn('key','▲',{key:'up'},'remote-up')+btn('key','◀',{key:'left'},'remote-left')+btn('key','OK',{key:'ok'},'remote-ok')+btn('key','▶',{key:'right'},'remote-right')+btn('key','▼',{key:'down'},'remote-down')+'</div><div class="remote-row">'+btn('key','Indietro',{key:'back'})+btn('key','Home',{key:'home'})+btn('key','Menu',{key:'menu'})+'</div>';
 else body+='<p class="remote-note">Tasti direzionali non esposti da questa integrazione. Sono disponibili i controlli qui sotto.</p>';
 body+='<div class="remote-row">'+btn('volume_down','Volume −')+btn('volume_mute',a.is_volume_muted?'Riattiva audio':'Muto',{is_volume_muted:!a.is_volume_muted})+btn('volume_up','Volume +')+'</div>';
 if(p.actions.includes('volume_set'))body+=slider({...s,state:p.powered?s.state:'unavailable'},'remote_volume','Volume',0,100,Math.round((a.volume_level||0)*100));
 body+='<div class="remote-row">'+btn('media_previous_track','Precedente')+btn(s.state==='playing'?'media_pause':'media_play',s.state==='playing'?'Pausa':'Riproduci')+btn('media_next_track','Successivo')+'</div>';
 if(p.sources.length)body+='<label class="remote-source">Sorgente / app<select id="remote-source" '+(!p.powered?'disabled':'')+'><option value="" disabled '+(!p.sources.includes(a.source)?'selected':'')+'>Scegli sorgente</option>'+p.sources.map(v=>'<option value="'+esc(v)+'" '+(a.source===v?'selected':'')+'>'+esc(v)+'</option>').join('')+'</select></label>';
 if(p.keys.includes('channel_up'))body+='<div class="remote-row">'+btn('key','Canale −',{key:'channel_down'})+btn('key','Canale +',{key:'channel_up'})+'</div><details class="remote-numbers"><summary>Tastierino numerico</summary><div>'+[1,2,3,4,5,6,7,8,9,0].map(n=>btn('key',String(n),{key:String(n)})).join('')+'</div></details>';
 }
 body+='<p class="remote-feedback" role="status">'+esc(feedback)+'</p>';
 let d=document.querySelector('#media-dialog');if(!d){d=document.createElement('dialog');d.id='media-dialog';d.className='remote-dialog';el.append(d);d.addEventListener('cancel',e=>{e.preventDefault();closeRemote()});d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeRemote()}})}
 d.setAttribute('aria-label','Telecomando '+name(s));d.innerHTML=body;d.querySelector('.dialog-close').onclick=closeRemote;
 d.querySelector('#retry-remote')?.addEventListener('click',async()=>{await loadMediaProfiles();if(remoteId)showRemote()});
 d.querySelectorAll('[data-remote-action]').forEach(b=>b.onclick=()=>sendRemote(b.dataset.remoteAction,JSON.parse(b.dataset.params)));
 d.querySelector('#remote-source')?.addEventListener('change',e=>sendRemote('select_source',{source:e.target.value}));
 d.querySelector('[data-slider="remote_volume"]')?.addEventListener('change',e=>sendRemote('volume_set',{volume_level:Number(e.target.value)/100}));
 if(!d.open)d.showModal();
}
async function sendRemote(action,params={}){if(busy)return;const id=remoteId;busy=true;const focus=document.activeElement,focusAction=focus?.dataset?.remoteAction,focusParams=focus?.dataset?.params,focusId=focus?.id,focusSlider=focus?.dataset?.slider;document.querySelectorAll('#media-dialog button:not(.dialog-close),#media-dialog input,#media-dialog select').forEach(b=>b.disabled=true);let message='Comando inviato';try{await api('media-command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:id,action,data:params})});await refresh();await loadMediaProfiles()}catch(e){message='Comando non riuscito: '+e.message}finally{busy=false;if(remoteId===id){showRemote(false,message);document.querySelectorAll('#media-dialog button,#media-dialog input,#media-dialog select').forEach(b=>{if((focusAction&&b.dataset.remoteAction===focusAction&&b.dataset.params===focusParams)||(focusId&&b.id===focusId)||(focusSlider&&b.dataset.slider===focusSlider))b.focus()})}}}

function lightTile(s){const a=s.attributes||{},on=s.state==='on',ok=valid(s),pct=Number.isFinite(a.brightness)?Math.round(a.brightness/255*100):null;return '<article data-light-card="'+esc(s.entity_id)+'" class="light-tile '+(on?'is-on':'')+'"><button class="light-info" data-detail="'+esc(s.entity_id)+'" aria-haspopup="dialog" aria-label="Dettagli '+esc(name(s))+'"><span class="light-orb">'+SYMBOLS.light+'</span><span><strong>'+esc(name(s))+'</strong><small>'+(ok?(on?'Accesa':'Spenta'):'Non disponibile')+(on&&pct!==null?' · '+pct+'%':'')+'</small></span><span class="detail-chevron">›</span></button><button class="light-switch" role="switch" aria-checked="'+on+'" aria-label="'+(on?'Spegni ':'Accendi ')+esc(name(s))+'" data-entity="'+esc(s.entity_id)+'" data-action="'+(on?'turn_off':'turn_on')+'" '+(!ok?'disabled':'')+'><span></span></button></article>'}
function closeDetail(){detailId='';document.querySelector('#light-dialog')?.remove();render();document.querySelectorAll("[data-detail]").forEach(b=>{if(b.dataset.detail===detailTrigger?.dataset.detail)b.focus()})}
function openDetail(id){detailId=id;const s=byId(id);if(!s)return;detailTrigger=document.activeElement;document.querySelector('#light-dialog')?.remove();const dialog=document.createElement('dialog');dialog.id='light-dialog';dialog.className='light-dialog';dialog.setAttribute('aria-label','Dettagli '+name(s));dialog.innerHTML='<div class="dialog-top"><span>ILLUMINAZIONE / DETTAGLI</span><button class="dialog-close" aria-label="Chiudi dettagli">×</button></div>'+card(s,true)+'<p class="dialog-note">'+(valid(s)?'Controlli disponibili per questa luce':'Dispositivo non disponibile')+'</p><div class="dialog-feedback" role="status"></div>';el.append(dialog);dialog.querySelector('.dialog-close').onclick=closeDetail;dialog.addEventListener('cancel',e=>{e.preventDefault();closeDetail()});dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDetail()}});dialog.dataset.lightCard=id;paintLights(dialog);bindControls(dialog);dialog.showModal()}
function button(id,act,title,ok=true){return '<button class="action" data-entity="'+esc(id)+'" data-action="'+act+'" '+(!ok?'disabled':'')+'>'+esc(title)+'</button>';}
function slider(s,type,label,min,max,value){return '<label class="range-label">'+esc(label)+'<input type="range" data-slider="'+type+'" data-entity="'+esc(s.entity_id)+'" min="'+min+'" max="'+max+'" value="'+Number(value||0)+'" '+(!valid(s)?'disabled':'')+'></label>'}
function other(){let key={"Luci":"light","Multimedia":"media_player","Aperture":"cover","Clima":"climate","Sicurezza":"alarm_control_panel","Scenari":"scene"}[page];if(page==="Scenari")return nativeScenesPage();if(page==="Personalizza")return renderLayoutEditor();if(page==="AI Studio")return renderStudio();if(page==="Altro")return morePage();if(page==="Aree")return '<h2>Le tue aree</h2><div class="area-grid wide">'+cardsForArea()+'</div>';if(page==="Area"){let a=areas.find(a=>a.id===areaId);if(!a)return '<p>Area non disponibile</p>';let devices=data.filter(s=>a.entities.includes(s.entity_id)&&["light","media_player","cover","climate"].some(d=>s.entity_id.startsWith(d+".")));return '<button class="action" data-page="Aree">‹ Tutte le aree</button><h2>'+esc(a.name)+'</h2><div class="devices">'+devices.map(s=>card(s)).join("")+'</div>'}if(page==="Irrigazione"){let s=by("sensor").filter(x=>x.entity_id.startsWith("sensor.cl_irrigation_")&&valid(x));return '<h2>CL Irrigation</h2><div class="devices">'+s.slice(0,12).map(x=>'<div class="device-card"><strong>'+esc(name(x))+'</strong><p>'+esc(x.state)+' '+esc(x.attributes?.unit_of_measurement||"")+'</p></div>').join("")+'</div>'}if(page==="Energia")return energyDashboard();if(page==="Assistenza")return '<div class="device-card"><h2>Assistenza CL Impianti</h2><p>Per richieste tecniche e assistenza contatta CL Impianti.</p><a href="https://www.climpianti.net/contatti.html" target="_blank" rel="noopener">Contatti e assistenza</a></div>';let ds=key?by(key):[];if(page==="Sicurezza"&&!ds.length)return '<h2>Sicurezza</h2><div class="empty">Nessuna centrale antifurto esposta come entità Home Assistant. Controlla le integrazioni Risco/INIM.</div>';return '<div class="content-heading"><span class="list-caption">Dispositivi</span><input id="search" placeholder="Cerca dispositivo" value="'+esc(search)+'" aria-label="Cerca dispositivi"></div><div class="devices">'+ds.filter(x=>name(x).toLowerCase().includes(search.toLowerCase())).map(s=>card(s)).join("")+'</div>'}
async function api(path,options={}){const r=await fetch("api/"+path,{credentials:"same-origin",cache:"no-store",...options});if(!r.ok)throw Error("HTTP "+r.status);return r.json()}
async function command(id,action,params={}){if(busy)return;const focusedSlider=document.activeElement?.dataset?.slider;busy=true;document.querySelectorAll("[data-action], [data-slider], [data-comfort-select], [data-comfort-form] input, [data-comfort-form] button").forEach(x=>x.disabled=true);try{await api("command",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({entity_id:id,action,data:params})});await refresh()}catch(e){error="Comando non riuscito: "+e.message;render()}finally{busy=false;if(detailId){const id=detailId,trigger=detailTrigger;openDetail(id);detailTrigger=trigger;if(focusedSlider)document.querySelectorAll("#light-dialog [data-slider]").forEach(x=>{if(x.dataset.slider===focusedSlider)x.focus()});document.querySelector(".dialog-feedback").textContent=error||"Comando inviato"}else render()}}

function lightVisual(s){
 const a=s?.attributes||{},m=a.supported_color_modes||[],dimmable=m.some(x=>['brightness','rgb','rgbw','rgbww','color_temp','hs','xy','white'].includes(x));
 if(s?.state!=='on'||!dimmable)return null;
 const clamp=(n,lo,hi)=>Math.min(hi,Math.max(lo,Number(n)||0));
 const level=Number.isFinite(a.brightness)?clamp(a.brightness,0,255)/255:1;
 let rgb=[255,218,160];
 if(a.color_mode==='color_temp'||(!a.color_mode&&a.color_temp_kelvin)){
  const t=clamp(a.color_temp_kelvin||3000,1000,40000)/100;
  rgb=[t<=66?255:329.698727446*Math.pow(t-60,-.1332047592),t<=66?99.4708025861*Math.log(t)-161.1195681661:288.1221695283*Math.pow(t-60,-.0755148492),t>=66?255:t<=19?0:138.5177312231*Math.log(t-10)-305.0447927307];
 }else if(a.color_mode==='white'){rgb=[255,244,225]}
 else if(Array.isArray(a.rgbw_color)&&(!a.color_mode||a.color_mode==='rgbw')){const c=a.rgbw_color;rgb=c.slice(0,3).map(v=>Number(v)+Number(c[3]||0))}
 else if(Array.isArray(a.rgbww_color)&&(!a.color_mode||a.color_mode==='rgbww')){const c=a.rgbww_color;rgb=c.slice(0,3).map((v,i)=>Number(v)+Number(c[3]||0)*[1,.95,.85][i]+Number(c[4]||0)*[1,.65,.3][i])}
 else if(Array.isArray(a.rgb_color)){rgb=a.rgb_color.slice(0,3)}
 else if(Array.isArray(a.hs_color)){const h=clamp(a.hs_color[0],0,360),sat=clamp(a.hs_color[1],0,100)/100;rgb=[5,3,1].map(n=>{const k=(n+h/60)%6;return 255*(1-sat*Math.max(0,Math.min(k,4-k,1)))})}
 const peak=Math.max(...rgb);if(peak>0)rgb=rgb.map(v=>Math.round(clamp(v/peak*255,0,255)));else rgb=[255,244,225];
 return {rgb:rgb.join(' '),level};
}
function paintLight(node,s){const v=lightVisual(s);node.classList.toggle('light-reactive',!!v);for(const key of ['--light-rgb','--light-wash','--light-edge','--light-glow'])node.style.removeProperty(key);if(!v)return;node.style.setProperty('--light-rgb',v.rgb);node.style.setProperty('--light-wash',String(.025+v.level*.38));node.style.setProperty('--light-edge',String(.15+v.level*.55));node.style.setProperty('--light-glow',String(v.level*.32))}
function paintLights(root){const nodes=[...root.querySelectorAll('[data-light-card]')];if(root.dataset?.lightCard)nodes.push(root);nodes.forEach(n=>paintLight(n,byId(n.dataset.lightCard)))}
function previewLight(input){const s=byId(input.dataset.entity);if(!s?.entity_id.startsWith('light.'))return;const a={...s.attributes},v=Number(input.value),key=input.dataset.slider;if(key==='brightness_pct')a.brightness=Math.round(v*255/100);else if(key==='hs_color'){const color=colorParams(s,v);Object.assign(a,color);a.color_mode=color.rgbw_color?"rgbw":color.rgbww_color?"rgbww":"hs";a.hs_color=[v,a.hs_color?.[1]??100];if(!a.supported_color_modes?.some(x=>['rgbw','rgbww'].includes(x))){a.color_mode='hs';delete a.rgb_color}}else if(key==='color_temp_kelvin'){a.color_temp_kelvin=v;a.color_mode='color_temp'}else if(key==='rgbw_color'){a.rgbw_color=[...(a.rgbw_color||[0,0,0,0]).slice(0,3),v];a.color_mode='rgbw'}else return;document.querySelectorAll('[data-light-card]').forEach(n=>{if(n.dataset.lightCard===s.entity_id)paintLight(n,{...s,state:'on',attributes:a})})}

function colorParams(s,hue){const a=s?.attributes||{},m=a.supported_color_modes||[];const key=m.includes('rgbw')?'rgbw_color':m.includes('rgbww')?'rgbww_color':null;if(!key)return {hs_color:[hue,a.hs_color?.[1]??100]};const old=a[key]||(key==='rgbw_color'?[0,0,0,0]:[0,0,0,0,0]),sat=(a.hs_color?.[1]??100)/100,v=Math.max(...old.slice(0,3))/255||1,f=n=>{const k=(n+hue/60)%6;return Math.round(255*v*(1-sat*Math.max(0,Math.min(k,4-k,1))))};return {[key]:[f(5),f(3),f(1),...old.slice(3,key==='rgbw_color'?4:5)]}}
function bindControls(root){root.querySelectorAll('[data-comfort-form]').forEach(form=>form.onsubmit=e=>{e.preventDefault();if(form.reportValidity())command(form.dataset.entity,form.dataset.comfortForm,{[form.dataset.key]:Number(form.querySelector('input').value)})});root.querySelectorAll('[data-comfort-select]').forEach(b=>b.onchange=()=>command(b.dataset.entity,b.dataset.comfortSelect,{[b.dataset.key]:b.value}));root.querySelectorAll("[data-slider]").forEach(b=>b.oninput=()=>previewLight(b));root.querySelectorAll("[data-action]").forEach(b=>b.onclick=()=>command(b.dataset.entity,b.dataset.action));root.querySelectorAll("[data-slider]").forEach(b=>b.onchange=()=>{let id=b.dataset.entity,key=b.dataset.slider,value=Number(b.value),dataObj={};if(key==="brightness_pct")dataObj={brightness_pct:value};if(key==="hs_color")dataObj=colorParams(byId(id),value);if(key==="color_temp_kelvin")dataObj={color_temp_kelvin:value};if(key==="volume_level")dataObj={volume_level:value/100};if(key==="rgbw_color"){let old=byId(id)?.attributes?.rgbw_color||[0,0,0,0];dataObj={rgbw_color:[...old.slice(0,3),value]}}command(id,key==="volume_level"?"volume_set":"turn_on",dataObj)});}
function render(){if(remoteId&&document.querySelector("#media-dialog"))return;if(detailId&&document.querySelector("#light-dialog"))return;el.innerHTML='<div class="layout"><aside class="side"><div class="brand"><strong>CL CONTROL <b>NEXT</b></strong><img src="assets/cl-logo.png" alt="CL Impianti"></div><nav>'+nav.map(([n,i])=>'<button data-page="'+n+'" class="'+(n===page?"selected":"")+'"><span>'+SYMBOLS[i]+'</span>'+n+'</button>').join("")+'</nav><footer>Blue Tech Premium · beta</footer></aside><main><div class="heading"><div><span class="eyebrow">CL IMPIANTI / SMART BUILDING</span><h1>'+esc(page==="Area"?areas.find(a=>a.id===areaId)?.name:page)+'</h1></div><span class="connection">Home Assistant · Ingress</span></div>'+(error?'<div class="warning">'+esc(error)+'</div>':'')+(page==="Home"&&dashboardLayout?.revision>0?dynamicHome(dashboardLayout):page==="Home"?home():other())+'</main></div>'+bottomNavigation();document.querySelectorAll("[data-page]").forEach(b=>b.onclick=()=>{page=b.dataset.page;search="";render()});document.querySelectorAll("[data-area]").forEach(b=>b.onclick=()=>{areaId=b.dataset.area;page="Area";render()});document.querySelector("#studio-form")?.addEventListener("submit",e=>{e.preventDefault();studioInstruction=document.querySelector("#studio-prompt")?.value||"";generateStudioDraft()});
document.querySelector("#studio-prompt")?.addEventListener("input",e=>{studioInstruction=e.target.value});
document.querySelectorAll("[data-studio-example]").forEach(el=>el.addEventListener("click",()=>{studioInstruction=el.dataset.studioExample;render();document.querySelector("#studio-prompt")?.focus()}));
document.querySelector("[data-studio-editor]")?.addEventListener("click",()=>{page="Personalizza";render()});
document.querySelector("[data-layout-preview]")?.addEventListener("click",()=>previewDashboard(false));
document.querySelector("[data-layout-suggest]")?.addEventListener("click",()=>previewDashboard(true));
document.querySelector("[data-layout-title]")?.addEventListener("change",e=>editLayoutDraft(d=>{d.title=e.target.value}));
document.querySelectorAll("[data-edit-title]").forEach(el=>el.addEventListener("change",e=>editLayoutDraft(d=>{d.widgets[Number(el.dataset.editTitle)].title=e.target.value})));
document.querySelectorAll("[data-edit-entity]").forEach(el=>el.addEventListener("change",e=>editLayoutDraft(d=>{d.widgets[Number(el.dataset.editEntity)].entity_id=e.target.value})));
document.querySelectorAll("[data-add-widget]").forEach(el=>el.addEventListener("click",()=>addLayoutWidget(el.dataset.addWidget)));
document.querySelectorAll("[data-move-widget]").forEach(el=>el.addEventListener("click",()=>moveLayoutWidget(Number(el.dataset.moveWidget),Number(el.dataset.direction))));
document.querySelectorAll("[data-remove-widget]").forEach(el=>el.addEventListener("click",()=>removeLayoutWidget(Number(el.dataset.removeWidget))));
document.querySelector("[data-layout-save]")?.addEventListener("click",saveDashboard);
document.querySelector("[data-layout-cancel]")?.addEventListener("click",()=>{dashboardDraft=null;layoutValidated=false;layoutMessage="Modifiche annullate";render()});
paintLights(document);bindControls(document);document.querySelectorAll("[data-remote]").forEach(b=>b.onclick=()=>openRemote(b.dataset.remote));document.querySelectorAll("[data-detail]").forEach(b=>b.onclick=()=>openDetail(b.dataset.detail));document.querySelector("#search")?.addEventListener("input",e=>{search=e.target.value;let pos=e.target.selectionStart;render();const b=document.querySelector("#search");b.focus();b.setSelectionRange(pos,pos)})}
async function refresh(){try{const res=await api("bootstrap");data=res.states||[];error="";render()}catch(e){error="Connessione Home Assistant: "+e.message;render()}}
async function loadAreas(){try{const res=await api("areas");areas=res.areas||[];render()}catch(e){areas=[];render()}}

function comfortCard(s){
 const a=s.attributes||{},f=a.supported_features||0,ok=valid(s),cover=s.entity_id.startsWith('cover.');
 const labels={closed:'Chiusa',open:'Aperta',opening:'In apertura',closing:'In chiusura',off:'Spento',heat:'Riscaldamento',cool:'Raffrescamento',auto:'Automatico',heat_cool:'Automatico caldo/freddo',dry:'Deumidificazione',fan_only:'Ventilazione',unavailable:'Non disponibile',unknown:'Stato sconosciuto'};
 let controls='';
 if(cover){controls='<div class="actions">'+[[1,'open_cover','Apri'],[8,'stop_cover','Stop'],[2,'close_cover','Chiudi']].filter(x=>f&x[0]).map(x=>button(s.entity_id,x[1],x[2],ok)).join('')+'</div>';
 if(f&4)controls+=comfortNumber(s,'set_cover_position','position','Apertura desiderata (%)',0,100,1,a.current_position);
 }else{
 const select=(key,action,title,values,current)=>Array.isArray(values)&&values.length?'<label class="range-label">'+title+'<select data-comfort-select="'+action+'" data-key="'+key+'" data-entity="'+esc(s.entity_id)+'" '+(!ok?'disabled':'')+'><option value="" disabled '+(!values.includes(current)?'selected':'')+'>Seleziona</option>'+values.map(v=>'<option value="'+esc(v)+'" '+(current===v?'selected':'')+'>'+esc(labels[v]||v)+'</option>').join('')+'</select></label>':'';
 controls+=select('hvac_mode','set_hvac_mode','Modalità',a.hvac_modes,s.state);
 if((f&1)&&Number.isFinite(a.min_temp)&&Number.isFinite(a.max_temp))controls+=comfortNumber(s,'set_temperature','temperature','Temperatura desiderata',a.min_temp,a.max_temp,a.target_temp_step||0.5,a.temperature);
 if(f&16)controls+=select('preset_mode','set_preset_mode','Profilo',a.preset_modes,a.preset_mode);
 if(f&8)controls+=select('fan_mode','set_fan_mode','Ventilazione',a.fan_modes,a.fan_mode);
 }
 return '<article class="device-card comfort-card"><div class="device-head"><span class="device-icon">'+SYMBOLS[cover?'cover':'climate']+'</span><div><strong>'+esc(name(s))+'</strong><small>'+esc(labels[s.state]||s.state)+'</small></div></div><p>'+(cover?(Number.isFinite(a.current_position)?'Apertura attuale: '+a.current_position+'%':'Posizione non disponibile'):(Number.isFinite(a.current_temperature)?'Temperatura ambiente: '+a.current_temperature+'°':'Temperatura ambiente non disponibile'))+'</p>'+controls+'</article>';
}
function comfortNumber(s,action,key,title,min,max,step,value){return '<form class="comfort-form" data-comfort-form="'+action+'" data-key="'+key+'" data-entity="'+esc(s.entity_id)+'"><label class="range-label">'+title+'<input aria-label="'+title+' '+esc(name(s))+'" type="number" required min="'+min+'" max="'+max+'" step="'+step+'" value="'+(Number.isFinite(value)?value:'')+'" '+(!valid(s)?'disabled':'')+'></label><button class="action" '+(!valid(s)?'disabled':'')+'>Applica</button></form>'}

// Ingress-only HA state relay. The browser never receives the Supervisor token.
let realtimeSocket=null,realtimeReady=false,realtimeRetry=null;
function applyStateDelta(message){
 if(!message||message.type!=="state"||typeof message.entity_id!=="string")return false;
 const id=message.entity_id,idx=data.findIndex(item=>item.entity_id===id);
 if(message.state===null){
  if(idx===-1)return false;
  data.splice(idx,1);return true;
 }
 const state=message.state;
 if(!state||state.entity_id!==id||typeof state.state!=="string"||!state.attributes||typeof state.attributes!=="object")return false;
 if(idx!==-1&&JSON.stringify(data[idx])===JSON.stringify(state))return false;
 if(idx===-1)data.push(state);else data[idx]=state;
 return true;
}
function refreshAllowed(){
 return !document.hidden&&!busy&&!detailId&&!remoteId&&!document.querySelector("input:focus,textarea:focus,select:focus,[contenteditable]:focus");
}
function startRealtime(){
 if(typeof WebSocket==="undefined"||document.hidden||realtimeSocket)return;
 const url=new URL("api/realtime",window.location.href);
 url.protocol=url.protocol==="https:"?"wss:":"ws:";
 const ws=new WebSocket(url.href);
 realtimeSocket=ws;
 ws.addEventListener("message",evt=>{
  let packet;try{packet=JSON.parse(evt.data)}catch{return}
  if(packet.type==="ready"){realtimeReady=true;refresh();return}
  if(packet.type==="error"){ws.close();return}
  if(applyStateDelta(packet)&&refreshAllowed())render();
 });
 ws.addEventListener("close",()=>{
  if(realtimeSocket!==ws)return;
  realtimeSocket=null;realtimeReady=false;
  if(!document.hidden){clearTimeout(realtimeRetry);realtimeRetry=setTimeout(startRealtime,5000)}
 });
 ws.addEventListener("error",()=>ws.close());
}
render();
Promise.all([refresh(),loadAreas(),loadLayout(),loadCatalog()]).then(startRealtime);
setInterval(()=>{if(!realtimeReady&&refreshAllowed())refresh()},9000);
document.addEventListener("visibilitychange",()=>{
 if(document.hidden){clearTimeout(realtimeRetry);realtimeSocket?.close();return}
 refresh();
 if(!realtimeSocket)startRealtime();
});


