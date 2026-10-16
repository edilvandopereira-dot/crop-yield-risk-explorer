'use strict';
const byId=id=>document.getElementById(id);
const fmt=(n,d=1)=>n===null||n===undefined?'Unavailable':Number(n).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const states=[...new Map(DATA.states.map(r=>[r.state_id,{id:r.state_id,name:r.state,abbr:r.abbr,region:r.region}])).values()];
let chartTrend,chartScatter,currentSummary=[],sortKey='frequency',sortAscending=false;
Chart.defaults.font.family='Arial, Helvetica, sans-serif';Chart.defaults.color='#596C77';Chart.defaults.font.size=11;Chart.defaults.animation=false;
const settings=()=>({state:byId('state').value,end:+byId('endYear').value,window:+byId('window').value,threshold:+byId('threshold').value,region:byId('region').value,minArea:+byId('minArea').value});
function summary(id,s){
 const history=DATA.states.filter(r=>r.state_id===id&&r.year>=s.end-s.window+1&&r.year<=s.end);
 const end=history.find(r=>r.year===s.end),valid=history.filter(r=>r.gap_pct!==null);
 const n=valid.length,events=valid.filter(r=>r.gap_pct < -s.threshold),worst=n?Math.min(...valid.map(r=>r.gap_pct)):null;
 const y=history.filter(r=>r.yield_kg_ha!==null),nation=DATA.brazil.find(r=>r.year===s.end);
 return {id,state:end?.state||states.find(x=>x.id===id).name,abbr:end?.abbr||'',region:end?.region||'',yield:end?.yield_kg_ha??null,production:end?.production_t??null,area:end?.harvested_ha??null,share:end?.production_t!==null&&nation?.production_t>0?100*end.production_t/nation.production_t:null,n,count:events.length,frequency:n?100*events.length/n:null,worst,worstYear:valid.find(r=>r.gap_pct===worst)?.year??null,meanYield:y.length?y.reduce((a,r)=>a+r.yield_kg_ha,0)/y.length:null};
}
function chooseState(id){byId('state').value=id;render();}
function render(){
 const s=settings(),a=summary(s.state,s),start=Math.max(2010,s.end-s.window+1);
 byId('period').textContent=`State focus: ${a.state} · Analysis window ${start}–${s.end} · Baseline: preceding 3 years · Threshold: >${s.threshold}% below baseline`;
 byId('yield').textContent=a.yield===null?'—':`${fmt(a.yield/1000,2)} t/ha`;
 byId('yieldNote').textContent=`${a.state}, ${s.end} · reported average`;
 byId('share').textContent=a.share===null?'—':`${fmt(a.share,1)}%`;
 byId('productionNote').textContent=a.production===null?'No production value available':`${fmt(a.production/1e6,2)} million tonnes in ${s.end}`;
 byId('frequency').textContent=a.n?`${a.count} / ${a.n}`:'—';
 byId('frequencyNote').textContent=a.n?`${fmt(a.frequency,1)}% of valid baseline years; descriptive`:'Insufficient baseline history';
 byId('worst').textContent=a.worst===null?'—':`${a.worst>0?'+':''}${fmt(a.worst,1)}%`;
 byId('worstNote').textContent=a.worstYear?`Gap in ${a.worstYear} versus its preceding 3-year mean`:'No valid comparison available';
 byId('trendTitle').textContent=`${a.state}: yield versus its recent baseline`;
 byId('insight').textContent=a.n?`In ${a.state}, ${a.count} of ${a.n} evaluable years had yields more than ${s.threshold}% below the preceding three-year mean. The lowest gap was ${fmt(a.worst,1)}% (${a.worstYear}). A high average yield can coexist with substantial downside years; inspect both before narrowing a regional research shortlist.`:'No valid baseline years in this selection. Extend the window or choose another state.';
 byId('trendNote').textContent='Baseline and event definition use earlier observations only. This snapshot uses revised source values; it is not a real-time forecast evaluation.';
 const history=DATA.states.filter(r=>r.state_id===s.state&&r.year>=start&&r.year<=s.end);
 const series=[{label:'Reported yield (t/ha)',data:history.map(r=>r.yield_kg_ha===null?null:r.yield_kg_ha/1000),borderColor:'#007E84',backgroundColor:'#007E84',borderWidth:3,pointRadius:3,tension:0},
 {label:'Preceding 3-year mean',data:history.map(r=>r.baseline_kg_ha===null?null:r.baseline_kg_ha/1000),borderColor:'#8A9EA1',borderDash:[6,5],borderWidth:2,pointRadius:0,tension:0},
 {label:`Shortfall >${s.threshold}%`,data:history.map(r=>r.gap_pct!==null&&r.gap_pct < -s.threshold?r.yield_kg_ha/1000:null),borderColor:'#C26642',backgroundColor:'#C26642',showLine:false,pointRadius:6,pointStyle:'rectRot'}];
 if(chartTrend){chartTrend.data.labels=history.map(r=>r.year);chartTrend.data.datasets=series;chartTrend.update('none');}
 else chartTrend=new Chart(byId('trend'),{type:'line',data:{labels:history.map(r=>r.year),datasets:series},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,padding:18}},tooltip:{callbacks:{afterBody:items=>{const focus=settings();const r=DATA.states.find(x=>x.state_id===focus.state&&x.year===Number(chartTrend.data.labels[items[0].dataIndex]));return !r||r.gap_pct===null?'Baseline unavailable':`Gap to baseline: ${fmt(r.gap_pct,1)}%`;}}}},scales:{y:{beginAtZero:true,title:{display:true,text:'Yield (tonnes per hectare)'},grid:{color:'#EDF0ED'}},x:{grid:{display:false}}}}});
 currentSummary=states.map(x=>summary(x.id,s)).filter(x=>x.n>=5&&x.area!==null&&x.area>0&&x.area>=s.minArea&&(s.region==='all'||x.region===s.region));
 const maxProd=Math.max(1,...currentSummary.map(x=>x.production||0));
 const pts=currentSummary.filter(x=>x.meanYield!==null).map(x=>({x:x.meanYield/1000,y:x.frequency,r:5+17*Math.sqrt((x.production||0)/maxProd),id:x.id,label:x.state,n:x.n,count:x.count,production:x.production}));
 const scatterData={datasets:[{label:'States',data:pts,backgroundColor:pts.map(x=>x.id===s.state?'#C26642CC':'#007E8480'),borderColor:pts.map(x=>x.id===s.state?'#8F3C20':'#007E84'),borderWidth:1.5}]};
 if(chartScatter){chartScatter.data=scatterData;chartScatter.update('none');}
 else chartScatter=new Chart(byId('scatter'),{type:'bubble',data:scatterData,options:{responsive:true,maintainAspectRatio:false,onClick:(e,els)=>{if(els.length)chooseState(chartScatter.data.datasets[0].data[els[0].index].id);},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>{const x=ctx.raw;return [`${x.label}: ${fmt(x.x,2)} t/ha`,`${x.count}/${x.n} shortfall years (${fmt(x.y)}%)`,`Production: ${fmt(x.production/1e6,2)} million t`];}}}},scales:{x:{min:0,title:{display:true,text:'Mean annual yield in selected window (t/ha)'},grid:{color:'#EDF0ED'}},y:{min:0,max:100,title:{display:true,text:'Historical shortfall frequency (%)'},grid:{color:'#EDF0ED'}}}}});
 byId('tableCaption').textContent=`${currentSummary.length} states with ≥5 valid baseline years, matching region and end-year area filters. State focus indicators above remain independent of comparison filters.`;
 renderTable(s);
}
function renderTable(s){
 const data=[...currentSummary].sort((a,b)=>{const x=a[sortKey],y=b[sortKey];if(x===null)return 1;if(y===null)return -1;return(typeof x==='string'?x.localeCompare(y):x-y)*(sortAscending?1:-1);});
 byId('rows').replaceChildren();
 for(const x of data){const tr=document.createElement('tr');if(x.id===s.state)tr.className='selected';
  const td=document.createElement('td'),b=document.createElement('button');b.textContent=`${x.state} (${x.abbr})`;b.onclick=()=>chooseState(x.id);td.append(b);tr.append(td);
  const cells=[`${fmt(x.yield/1000,2)} t/ha`,`${fmt(x.production/1e6,2)}m t`,`${fmt(x.share,1)}%`,`${x.count}/${x.n} (${fmt(x.frequency,1)}%)`,`${x.worst>0?'+':''}${fmt(x.worst,1)}%`,`${x.n} baseline years`];
  cells.forEach((txt,i)=>{const cell=document.createElement('td');cell.textContent=txt;if(i===3)cell.className='freq';tr.append(cell);});byId('rows').append(tr);}
 if(!data.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=7;td.className='empty';td.textContent='No state meets these comparison filters. Reduce the minimum area or extend the window.';tr.append(td);byId('rows').append(tr);}
}
states.sort((a,b)=>a.name.localeCompare(b.name)).forEach(s=>byId('state').add(new Option(`${s.name} (${s.abbr})`,s.id)));
byId('state').value='51';for(let y=DATA.latest_year;y>=2017;y--)byId('endYear').add(new Option(y,y));
['state','endYear','window','threshold','region','minArea'].forEach(id=>byId(id).addEventListener('change',render));
document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sort;sortAscending=sortKey===key?!sortAscending:key==='state';sortKey=key;document.querySelectorAll('[data-sort]').forEach(x=>x.textContent=x.textContent.replace(/ [↑↓]$/,''));b.textContent+=sortAscending?' ↑':' ↓';renderTable(settings());}));
byId('download').addEventListener('click',()=>{const output={filters:settings(),source:DATA.table_url,retrieved_at:DATA.manifest.retrieved_at,definition:'Shortfall: yield strictly more than threshold below preceding 3-year mean. Retrospective current-vintage analysis.',states:currentSummary};const blob=new Blob([JSON.stringify(output,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='crop-yield-filtered.json';a.click();URL.revokeObjectURL(a.href);});
byId('sourceDate').textContent=`Source snapshot retrieved: ${DATA.manifest.retrieved_at}. Four source files are retained with SHA-256 hashes in the repository. All 48 additive state-to-national checks and yield/area consistency checks passed at build time.`;
render();
