'use strict';
const $ = id => document.getElementById(id);
const keys = ['initial','ambient','coefficient','duration','step','target'];
const state = {run:null, name:'The warm cup', presets:[], time:0, playing:false, last:0,
  comparison:null, chart:'temperature', page:0, selected:'warm-cup', request:0};
const number = (value, digits=1) => value === null || !Number.isFinite(value) ? '—' : value.toLocaleString('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits});
const compact = value => value.toLocaleString('en-US',{maximumFractionDigits:2});
const precise = value => value === null ? 'unavailable' : Math.abs(value) < 0.00001 && value !== 0 ? value.toExponential(3) : number(value,5);
const fields = () => Object.fromEntries(keys.map(key=>[key,Number($(key).value)]));
const setFields = p => keys.forEach(key=>{$(key).value=p[key];});
let toastTimer;
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('toast').hidden=true;},4500);}
function pending(){
  const changed=state.run && JSON.stringify(fields())!==JSON.stringify(state.run.parameters);
  $('pending-note').hidden=!changed;
  if(changed){state.selected=null;renderPresetSelection();}
}
function pause(){state.playing=false;state.last=0;$('play-text').textContent='Play';$('play-icon').textContent='▶';$('play').setAttribute('aria-label','Play simulation');}
function exactAt(p,t){return p.ambient+(p.initial-p.ambient)*Math.exp(-p.coefficient*t);}
function updateTime(time){
  if(!state.run)return;
  const p=state.run.parameters;state.time=Math.min(p.duration,Math.max(0,time));
  const temp=exactAt(p,state.time);
  $('temperature').textContent=number(temp);$('elapsed').replaceChildren(document.createTextNode(number(state.time)+' '),Object.assign(document.createElement('span'),{textContent:'min'}));
  $('timeline').value=state.time;$('timeline').setAttribute('aria-valuetext',`${number(state.time)} minutes, ${number(temp)} degrees Celsius`);
  const hot=Math.max(0,Math.min(1,(temp-p.ambient)/65));
  const cold=Math.max(0,Math.min(1,(p.ambient-temp)/35));
  const hue=temp>=p.ambient?34-15*hot:144+47*cold;
  $('scene').style.setProperty('--liquid',`hsl(${hue} ${28+hot*30+cold*8}% ${64-hot*11}%)`);
  $('scene').style.setProperty('--heat',hot*.85);
  const gap=p.initial-p.ambient;
  $('thermal-fill').style.width=(gap===0?0:Math.min(100,Math.abs((temp-p.ambient)/gap)*100))+'%';
  const desc=p.coefficient===0?'No heat exchange in this model.':Math.abs(temp-p.ambient)<0.05?'Almost at room temperature.':temp>p.ambient?'Warmer than the room. Heat moves out.':'Cooler than the room. Heat moves in.';
  $('scene-description').textContent=desc;
  updateMarker();
}
function tick(timestamp){
  if(state.playing){if(state.last){updateTime(state.time+Math.min((timestamp-state.last)/1000,.25)*Number($('speed').value));}state.last=timestamp;if(state.time>=state.run.parameters.duration)pause();}
  requestAnimationFrame(tick);
}
function renderPresetSelection(){document.querySelectorAll('.preset').forEach(b=>{const selected=b.dataset.preset===state.selected;b.classList.toggle('selected',selected);b.setAttribute('aria-pressed',String(selected));});}
function renderPresets(){
  const icons=['♨','◷','❄','∿'];$('presets').replaceChildren();
  for(const [i,preset] of state.presets.entries()){
    const b=document.createElement('button');b.className='preset';b.dataset.preset=preset.id;b.setAttribute('aria-label',preset.name);
    const top=document.createElement('div');top.className='preset-top';
    const title=document.createElement('span');title.className='preset-title';title.textContent=preset.name;
    const icon=document.createElement('span');icon.className='preset-icon';icon.textContent=icons[i];icon.setAttribute('aria-hidden','true');top.append(title,icon);
    const description=document.createElement('p');description.textContent=preset.description;
    const tag=document.createElement('span');tag.className='preset-tag';tag.textContent=preset.tag;
    b.append(top,description,tag);b.addEventListener('click',()=>{setFields(preset.parameters);state.selected=preset.id;renderPresetSelection();runExperiment(preset.name);});$('presets').append(b);
  }
  $('presets').setAttribute('aria-busy','false');renderPresetSelection();
}
async function runExperiment(name='My experiment'){
  if(!$('settings-form').reportValidity())return;
  const settings=fields(),request=++state.request;
  pause();$('run-button').disabled=true;$('run-button').textContent='Calculating…';$('form-error').hidden=true;
  try{
    const response=await fetch('/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings),signal:AbortSignal.timeout(15000)});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'The calculation could not finish.');if(request!==state.request)return;
    state.run=data;state.name=name;state.page=0;state.time=0;
    $('run-title').textContent=name;$('direction').textContent=({cooling:'Cooling gently',warming:'Warming gently',steady:'At a steady temperature'})[data.summary.direction];
    $('room-value').textContent=compact(data.parameters.ambient)+'°C';$('timeline').max=data.parameters.duration;$('timeline-end').textContent=compact(data.parameters.duration)+' min';
    for(const id of ['play','restart','timeline','pin','export-csv'])$(id).disabled=false;
    $('pending-note').hidden=true;
    renderInsights();renderGraph();renderMethods();updateTime(0);
    document.documentElement.dataset.ready='true';
    if(request>1)toast(name+' is ready. Press Play to watch.');
  }catch(error){if(request===state.request){$('form-error').textContent=error.name==='TimeoutError'?'The calculation took too long. Make sure the local Python server is running, then try again.':error.message||'Cannot connect to Python. Start the local server and try again.';$('form-error').hidden=false;}}
  finally{if(request===state.request){$('run-button').disabled=false;$('run-button').innerHTML='Run experiment <span aria-hidden="true">↗</span>';}}
}
function renderInsights(){
  const {parameters:p,summary:s,warnings}=state.run;const target=s.target;
  $('target-label').textContent='TIME TO '+compact(p.target)+'°C';
  $('target-result').textContent=target.minutes!==null?number(target.minutes,1)+' min':target.status==='asymptotic'?'Approaches':'Not reached';
  $('target-context').textContent=target.minutes!==null?(target.status==='after_run'?'Beyond the displayed duration':target.status==='at_start'?'Already there at the start':'From the exact model'):target.message;
  $('half-life').textContent=s.half_life===null?'No decay':number(s.half_life)+' min';
  $('final-label').textContent='AFTER '+compact(p.duration)+' MINUTES';$('final-value').textContent=number(s.final_temperature)+'°C';
  $('numerical-warning').hidden=!warnings.length;$('numerical-warning').textContent=warnings.join(' ');
}
let plot={left:64,right:1084,top:24,bottom:294,min:0,max:100,duration:60};
const x = t=>plot.left+(t/plot.duration)*(plot.right-plot.left);
const y = temp=>plot.bottom-(temp-plot.min)/(plot.max-plot.min)*(plot.bottom-plot.top);
const svgNS='http://www.w3.org/2000/svg';
function svg(tag,attrs={},text){const e=document.createElementNS(svgNS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e;}
function linePath(samples,key){let path='',pen=false;for(const s of samples){const value=s[key];if(value===null||!Number.isFinite(value)){pen=false;continue;}path+=(pen?'L':'M')+x(s.time).toFixed(2)+','+y(value).toFixed(2);pen=true;}return path;}
function renderGraph(){
  if(!state.run)return;
  const g=$('graph'),p=state.run.parameters,samples=state.run.samples,error=state.chart==='error';
  const width=window.innerWidth<=560?460:1120;g.setAttribute('viewBox',`0 0 ${width} 340`);plot.left=width===460?60:64;plot.right=width-30;
  g.replaceChildren();const values=[];
  if(error){if($('show-euler').checked)values.push(...samples.map(s=>s.euler_error));if($('show-rk4').checked)values.push(...samples.map(s=>s.rk4_error));values.push(0);}
  else{
    for(const key of ['exact','euler','rk4'])if($('show-'+key).checked)values.push(...samples.map(s=>s[key]));
    values.push(p.ambient,p.initial,p.target);
    if(state.comparison)values.push(...state.comparison.samples.map(s=>s.exact));
  }
  const finite=values.filter(v=>v!==null&&Number.isFinite(v));let min=Math.min(...finite),max=Math.max(...finite);
  if(max-min<1e-10){if(error){min=0;max=1e-8;}else{min-=5;max+=5;}}
  const pad=(max-min)*.09;plot={...plot,min:error?0:min-pad,max:max+pad,duration:Math.max(p.duration,state.comparison&&!error?state.comparison.parameters.duration:0)};
  const defs=svg('defs');const gradient=svg('linearGradient',{id:'curve-fill',x1:0,y1:0,x2:0,y2:1});gradient.append(svg('stop',{offset:'0%','stop-color':'#b3c49b','stop-opacity':'.22'}),svg('stop',{offset:'100%','stop-color':'#d7e2c8','stop-opacity':'.01'}));defs.append(gradient);g.append(defs);
  for(let i=0;i<=4;i++){
    const value=plot.min+(plot.max-plot.min)*i/4,py=y(value);
    g.append(svg('line',{x1:plot.left,y1:py,x2:plot.right,y2:py,class:'grid'}));
    const label=error?(max<.01?value.toExponential(1):number(value,2)):Math.abs(value)>10000?value.toExponential(1):number(value,0);
    g.append(svg('text',{x:plot.left-15,y:py+4,'text-anchor':'end'},label));
  }
  for(let i=0;i<=6;i++){const t=plot.duration*i/6;g.append(svg('text',{x:x(t),y:319,'text-anchor':'middle'},number(t,t%1?1:0)));}
  g.append(svg('text',{x:plot.left,y:12,class:'axis-title'},error?'ABSOLUTE ERROR (°C)':'TEMPERATURE (°C)'),svg('text',{x:plot.right,y:339,'text-anchor':'end',class:'axis-title'},'TIME (MINUTES)'));
  if(!error){
    g.append(svg('line',{x1:plot.left,y1:y(p.ambient),x2:plot.right,y2:y(p.ambient),class:'ambient'}));
    if($('show-exact').checked){const ref=linePath(state.run.reference,'exact');g.append(svg('path',{d:ref+`L${x(p.duration)},${plot.bottom}L${plot.left},${plot.bottom}Z`,fill:'url(#curve-fill)'}),svg('path',{d:ref,class:'exact-path'}));}
    if(state.comparison)g.append(svg('path',{d:linePath(state.comparison.reference,'exact'),class:'comparison-path'}));
  }
  for(const method of ['euler','rk4'])if($('show-'+method).checked)g.append(svg('path',{d:linePath(samples,error?method+'_error':method),class:method+'-path'}));
  g.append(svg('line',{id:'time-marker',x1:x(state.time),x2:x(state.time),y1:plot.top,y2:plot.bottom,class:'marker'}));
  if(!error)g.append(svg('circle',{id:'time-point',cx:x(state.time),cy:y(exactAt(p,state.time)),r:4,fill:'#fffefa',stroke:'#51734e','stroke-width':2}));
  $('graph').setAttribute('aria-label',error?'Absolute numerical error against time. Euler and RK4 compared with the exact solution.':'Object temperature against time. Exact reference, Euler and RK4 estimates.');
  $('graph-caption').textContent=error?'Absolute error = |numerical temperature − exact temperature|, in °C. The vertical scale adapts to the visible methods.':'Time in minutes. Temperature in °C. The solid line is the exact model. Click or touch the graph to move through time.';
  $('show-exact').disabled=error;updateMarker();
}
function updateMarker(){if(!state.run)return;const marker=$('time-marker');if(marker){marker.setAttribute('x1',x(state.time));marker.setAttribute('x2',x(state.time));}const point=$('time-point');if(point){point.setAttribute('cx',x(state.time));point.setAttribute('cy',y(exactAt(state.run.parameters,state.time)));}}
function graphTime(event){const point=new DOMPoint(event.clientX,event.clientY).matrixTransform($('graph').getScreenCTM().inverse());return Math.max(0,Math.min(state.run.parameters.duration,(point.x-plot.left)/(plot.right-plot.left)*plot.duration));}
function graphTooltip(event){
  if(!state.run)return;const t=graphTime(event);const samples=state.run.samples;const nearest=samples.reduce((best,s)=>Math.abs(s.time-t)<Math.abs(best.time-t)?s:best,samples[0]);
  const tooltip=$('chart-tooltip');tooltip.replaceChildren();const title=document.createElement('strong');title.textContent=number(nearest.time,2)+' min · sampled value';tooltip.append(title);
  for(const [label,key] of [['Exact','exact'],['Euler',state.chart==='error'?'euler_error':'euler'],['RK4',state.chart==='error'?'rk4_error':'rk4']]){if(state.chart==='error'&&key==='exact')continue;const row=document.createElement('div');row.textContent=label+': '+precise(nearest[key])+(nearest[key]!==null?' °C':'');tooltip.append(row);}tooltip.hidden=false;
}
function renderMethods(){
  if(!state.run)return;const p=state.run.parameters,f=state.run.summary.first_step;
  const steps=$('first-step');steps.replaceChildren();
  const euler=document.createElement('div'),rk=document.createElement('div');
  euler.innerHTML='<h3>Euler: use the current rate</h3>';
  const eLines=[`At the start: ${number(p.initial,2)}°C; room: ${number(p.ambient,2)}°C.`,`Rate = −${p.coefficient} × (${p.initial} − ${p.ambient}) = ${number(f.slope,4)} °C/min.`,`Next = ${p.initial} + ${f.h} × (${number(f.slope,4)})`];
  for(const text of eLines){const row=document.createElement('p');row.textContent=text;euler.append(row);}const er=document.createElement('p');er.className='step-result';er.textContent=number(f.euler_next,5)+'°C after '+number(f.h,2)+' min';euler.append(er);
  rk.innerHTML='<h3>RK4: combine four rates</h3>';
  const rkLines=[`k₁ = ${number(f.k1,5)}, k₂ = ${number(f.k2,5)}`,`k₃ = ${number(f.k3,5)}, k₄ = ${number(f.k4,5)} °C/min`,`Next = T₀ + h(k₁ + 2k₂ + 2k₃ + k₄) / 6`];
  for(const text of rkLines){const row=document.createElement('p');row.textContent=text;rk.append(row);}const rr=document.createElement('p');rr.className='step-result';rr.textContent=number(f.rk4_next,5)+'°C · exact: '+number(f.exact_next,5)+'°C';rk.append(rr);steps.append(euler,rk);
  $('error-summary').replaceChildren();for(const method of ['euler','rk4']){const m=state.run.summary.methods[method];const row=document.createElement('span');const name=document.createElement('strong');name.textContent=method==='euler'?'Euler':'RK4';row.append(name,document.createTextNode(` · max error: ${precise(m.max_abs_error)}${m.max_abs_error!==null?' °C':''} · ${m.stability.replaceAll('_',' ')}`));$('error-summary').append(row);}
  renderTable();
}
function renderTable(){if(!state.run)return;const rows=state.run.samples,total=Math.ceil(rows.length/10);state.page=Math.max(0,Math.min(total-1,state.page));$('results-table').replaceChildren();for(const sample of rows.slice(state.page*10,state.page*10+10)){const tr=document.createElement('tr');for(const key of ['time','exact','euler','rk4','euler_error','rk4_error']){const td=document.createElement('td');td.textContent=key==='time'?number(sample[key],2):precise(sample[key]);tr.append(td);}$('results-table').append(tr);}$('table-page').textContent=`${state.page+1} / ${total}`;$('table-prev').disabled=state.page===0;$('table-next').disabled=state.page>=total-1;}
function pinRun(){if(!state.run)return;state.comparison={...structuredClone(state.run),name:state.name};$('comparison-strip').hidden=false;const p=state.comparison.parameters;$('comparison-description').textContent=`Pinned: ${state.name} · ${p.initial}°C start · ${p.ambient}°C room · k = ${p.coefficient} min⁻¹. Dashed blue line = exact reference.`;renderGraph();toast('Reference pinned. Change a setting and run again to compare.');}
function download(filename,content,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('settings-form').addEventListener('submit',e=>{e.preventDefault();state.selected=null;renderPresetSelection();runExperiment();});
for(const key of keys)$(key).addEventListener('input',pending);
$('play').addEventListener('click',()=>{if(!state.run)return;if(state.playing)pause();else{if(state.time>=state.run.parameters.duration)updateTime(0);state.playing=true;state.last=0;$('play-text').textContent='Pause';$('play-icon').textContent='Ⅱ';$('play').setAttribute('aria-label','Pause simulation');}});
$('restart').addEventListener('click',()=>{pause();updateTime(0);});$('timeline').addEventListener('input',()=>{pause();updateTime(Number($('timeline').value));});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
for(const type of ['temperature','error'])$(type+'-tab').addEventListener('click',()=>{state.chart=type;$('temperature-tab').setAttribute('aria-pressed',String(type==='temperature'));$('error-tab').setAttribute('aria-pressed',String(type==='error'));$('chart-tooltip').hidden=true;renderGraph();});
for(const method of ['exact','euler','rk4'])$('show-'+method).addEventListener('change',renderGraph);
$('graph').addEventListener('pointermove',graphTooltip);$('graph').addEventListener('pointerleave',()=>{$('chart-tooltip').hidden=true;});$('graph').addEventListener('click',e=>{if(state.run){pause();updateTime(graphTime(e));}});
$('pin').addEventListener('click',pinRun);$('clear-comparison').addEventListener('click',()=>{state.comparison=null;$('comparison-strip').hidden=true;renderGraph();});
$('export-csv').addEventListener('click',()=>{if(!state.run)return;const p=state.run.parameters;const columns=['time_min','exact_C','euler_C','rk4_C','abs_error_euler_C','abs_error_rk4_C','initial_C','ambient_C','coefficient_per_min','duration_min','calculation_step_min','target_C'];const lines=[columns.join(',')];for(const s of state.run.samples)lines.push([s.time,s.exact,s.euler,s.rk4,s.euler_error,s.rk4_error,...keys.map(k=>p[k])].map(v=>v===null?'':String(v)).join(','));download('ThermoLab-results.csv',lines.join('\r\n'),'text/csv;charset=utf-8');});
$('export-settings').addEventListener('click',()=>{if(!state.run)return;download('ThermoLab-settings.json',JSON.stringify({application:'ThermoLab',schema_version:1,parameters:state.run.parameters},null,2),'application/json');});
$('import-button').addEventListener('click',()=>$('import-file').click());$('import-file').addEventListener('change',async()=>{const file=$('import-file').files[0];if(!file)return;try{if(file.size>16384)throw new Error('Use a ThermoLab settings file smaller than 16 KB.');const data=JSON.parse(await file.text());if(data.application!=='ThermoLab'||data.schema_version!==1||!data.parameters||Object.keys(data.parameters).length!==keys.length||keys.some(k=>typeof data.parameters[k]!=='number'||!Number.isFinite(data.parameters[k])))throw new Error('Choose a valid ThermoLab version 1 settings file.');setFields(data.parameters);state.selected=null;renderPresetSelection();pending();toast('Settings loaded. Press Run experiment to calculate them.');}catch(error){toast(error.message||'That settings file could not be read.');}finally{$('import-file').value='';}});
$('table-prev').addEventListener('click',()=>{state.page--;renderTable();});$('table-next').addEventListener('click',()=>{state.page++;renderTable();});
function showMethods(show=true){$('method-lab').hidden=!show;$('methods-toggle').setAttribute('aria-expanded',String(show));if(show)$('method-lab').scrollIntoView({behavior:'smooth',block:'start'});}
$('methods-toggle').addEventListener('click',()=>showMethods($('method-lab').hidden));$('methods-close').addEventListener('click',()=>{showMethods(false);$('methods-toggle').focus();});
$('methods-nav').addEventListener('click',()=>{$('mathematics').scrollIntoView({behavior:'smooth'});$('methods-nav').classList.add('active');$('experiment-nav').classList.remove('active');});
$('experiment-nav').addEventListener('click',()=>{$('workspace').scrollIntoView({behavior:'smooth'});$('experiment-nav').classList.add('active');$('methods-nav').classList.remove('active');});
$('guide-open').addEventListener('click',()=>$('guide').showModal());for(const id of ['guide-close','guide-start'])$(id).addEventListener('click',()=>$('guide').close());$('guide').addEventListener('click',event=>{if(event.target===$('guide')){const box=$('guide').getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)$('guide').close();}});
$('try-comparison').addEventListener('click',()=>{if(!state.run)return;pinRun();setFields({...state.run.parameters,coefficient:state.run.parameters.coefficient/2});state.selected=null;renderPresetSelection();runExperiment('Half the cooling coefficient');$('workspace').scrollIntoView({behavior:'smooth'});});
async function init(){try{const response=await fetch('/api/presets',{signal:AbortSignal.timeout(10000)});if(!response.ok)throw new Error();state.presets=(await response.json()).presets;if(!state.presets.length)throw new Error();renderPresets();setFields(state.presets[0].parameters);await runExperiment(state.presets[0].name);}catch{$('presets').replaceChildren();const message=document.createElement('p');message.className='loading';message.textContent='Cannot reach the local Python engine. Start the server, then ';const retry=document.createElement('button');retry.className='text-button';retry.textContent='try again';retry.addEventListener('click',init);message.append(retry);$('presets').append(message);$('presets').setAttribute('aria-busy','false');}}
requestAnimationFrame(tick);init();
let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(renderGraph,80);});
