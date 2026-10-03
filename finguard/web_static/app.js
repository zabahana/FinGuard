'use strict';
const $ = id => document.getElementById(id);
let token = null, pending = false, current = null, reportKey = '', jobKey = '';
const labels = {download:'Prepare data',train:'Train detector',services:'Start and check services',investigate:'Sandbox investigation',full:'Full end-to-end workflow'};
const stageNames = {download:'Prepare real ULB data',train:'Train and evaluate detector',services:'Check local services',export:'Export label-blind evidence',build:'Build minimal agent image',control:'Run plain Docker control',sandbox:'Create sandbox and enable audit',probes:'Run containment probes',policy:'Apply deployment policy',investigate:'Run Qwen investigation',collect:'Collect runtime evidence',verify:'Verify local deployment'};
const fmt = n => typeof n === 'number' ? n.toLocaleString('en-US') : '—';
const pct = n => typeof n === 'number' ? `${(n*100).toFixed(2)}%` : '—';
function el(tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;}
function clear(id){$(id).replaceChildren();return $(id);}
function badge(id,text,failed=false){$(id).textContent=text;$(id).classList.toggle('failed',failed);}
function details(id,items){const root=clear(id);items.forEach(([k,v])=>root.append(el('dt',k),el('dd',String(v??'—'))));}
function renderReports(results){
  const t=results.training,a=results.agent,v=results.verification,p=results.containment;
  const summary=clear('summary-metrics');
  [[t?pct(t.test.precision):'—','Held-out detector precision'],[t?pct(t.test.recall):'—','Held-out detector recall'],[p?`${p.probes.filter(x=>x.passed).length} / ${p.probes.length}`:'—','Direct containment checks'],[a?String(a.tool_calls):'—','Tool calls in saved investigation']].forEach(([value,label])=>{const div=el('div','','summary-metric');div.append(el('strong',value),el('span',label));summary.append(div);});
  badge('agent-state',a?a.status.toUpperCase():'NO REPORT',a&&a.status!=='complete');
  $('recommendation').textContent=a?.recommendation||'No completed recommendation is available. Run a sandbox investigation.';
  details('agent-details',[['Transaction',a?.transaction_id],['Model',a?.model],['Model / tool calls',a?`${a.model_calls} / ${a.tool_calls}`:null],['Runtime',a?.runtime],['Banking actions',a?.banking_actions],['Case persisted',a?String(a.case_persisted):null]]);
  $('risk-score').value=a?.detector_score||0;
  $('risk-caption').textContent=a?`Score ${a.detector_score.toFixed(4)} · threshold ${a.detector_threshold.toFixed(4)} · ${a.flagged_for_review?'flagged for review':'below threshold; residual risk remains'}. Not a fraud probability.`:'No score available.';
  $('result-freshness').textContent=v?`Saved verification: ${v.verified_at}. ${v.sandbox_name}. Results remain visible while a new job runs; failed jobs do not replace this session’s published results.`:'No saved verification yet.';
  clear('metric-bars');clear('confusion');clear('partitions');
  if(t){
    $('training-date').textContent=`Trained ${new Date(t.created_at).toLocaleString()}`;
    [['Precision',t.test.precision],['Recall',t.test.recall],['Average precision',t.test.average_precision]].forEach(([label,value])=>{const row=el('div','','metric-bar');const title=el('div','','metric-label');title.append(el('span',label),el('b',pct(value)));const bar=el('progress','');bar.max=1;bar.value=value;bar.setAttribute('aria-label',`${label}: ${pct(value)}`);row.append(title,bar);$('metric-bars').append(row);});
    [['true_positives','Fraud → flagged'],['false_negatives','Fraud → missed'],['false_positives','Non-fraud → flagged'],['true_negatives','Non-fraud → not flagged']].forEach(([key,label])=>{const cell=el('div','','cell');cell.append(el('strong',fmt(t.test[key])),el('span',label));$('confusion').append(cell);});
    Object.entries(t.partitions).forEach(([name,data])=>{const div=el('div','','partition');div.append(el('span',name.toUpperCase()),el('strong',`${fmt(data.rows)} rows`),el('span',`${fmt(data.fraud_count)} fraud labels`));$('partitions').append(div);});
    $('dataset-info').textContent=`Source: ULB/Worldline, September 2013 · ${fmt(t.raw_rows)} raw rows → ${fmt(t.retained_rows)} retained · ${fmt(t.duplicates_removed)} duplicates removed · frozen threshold ${t.threshold.toFixed(4)}. Training and investigation timestamps are independent.`;
  }else{$('dataset-info').textContent='Train the detector to populate measured results.';$('training-date').textContent='';}
  badge('verification-state',v?(v.passed?'GATE PASSED':'GATE FAILED'):'NO VERIFICATION',v&&!v.passed);
  $('verification-summary').textContent=v?`${Object.values(v.checks).filter(Boolean).length}/${Object.keys(v.checks).length} checks passed. ${v.native_ocsf_event_count} native OCSF events, including ${v.native_denials} denials. These are saved observations, not live monitoring.`:'Run the full workflow to collect containment evidence.';
  const probes=clear('probes');(p?.probes||[]).forEach(probe=>{const li=el('li','');li.append(el('span',probe.name.replaceAll('_',' ')),el('b',`${probe.passed?'PASS':'FAIL'} · ${probe.observed}`));probes.append(li);});
  const checks=clear('checks');Object.entries(v?.checks||{}).forEach(([name,pass])=>{const li=el('li','');li.append(el('span',name.replaceAll('_',' ')),el('b',pass?'PASS':'FAIL'));checks.append(li);});
}
function renderJob(job){
  $('job-title').textContent=job?labels[job.action]:'Ready to run';badge('job-state',job?job.status.toUpperCase():'IDLE',job?.status==='failed');
  $('job-meta').textContent=job?`Started ${new Date(job.started_at).toLocaleString()}${job.sandbox?' · '+job.sandbox:''}${job.finished_at?' · finished '+new Date(job.finished_at).toLocaleTimeString():''}`:'No job has started in this server session.';
  const steps=clear('pipeline-steps');
  const planned=(!job||job.action==='full')?Object.keys(stageNames):job.action==='investigate'?['services','investigate']:job.action==='services'?['services']:[job.action];
  planned.forEach((id,index)=>{const actual=job?.steps.findLast(s=>s.id===id);const status=actual?.status||'pending';const step=el('div','',`step ${status}`);step.append(el('span',`${String(index+1).padStart(2,'0')} / ${status}`),el('strong',stageNames[id]));steps.append(step);});
  $('job-error').hidden=!job?.error;$('job-error').textContent=job?.error||'';
  const log=$('logs'),atBottom=log.scrollHeight-log.scrollTop-log.clientHeight<40;
  log.textContent=job?.logs.join('\n')||'Job output will appear here.';$('log-count').textContent=job?`(${job.logs.length} recent lines)`:'';
  if(atBottom)log.scrollTop=log.scrollHeight;
}
function render(state){
  current=state;token=state.token;
  $('connection').textContent=state.job?.status==='running'?'LOCAL BACKEND · JOB RUNNING':'LOCAL BACKEND · CONNECTED';
  const readiness=clear('readiness');[['dataset','Dataset present'],['detector','Detector bundle'],['ollama_port','Ollama listener'],['gateway_port','Gateway listener']].forEach(([key,label])=>{const item=el('div','','ready-item');item.append(el('span',label),el('b',state.readiness[key]?'Detected':'Missing'));readiness.append(item);});
  document.querySelectorAll('[data-action]').forEach(button=>button.disabled=pending||state.job?.status==='running');
  const next=JSON.stringify(state.results);if(next!==reportKey){reportKey=next;renderReports(state.results);}
  const nextJob=JSON.stringify(state.job);if(nextJob!==jobKey){jobKey=nextJob;renderJob(state.job);}
  const history=clear('history');state.history.slice().reverse().forEach(job=>history.append(el('li',`${labels[job.action]} · ${job.status} · ${new Date(job.started_at).toLocaleString()}${job.sandbox?' · '+job.sandbox:''}`)));
}
async function refresh(){try{const response=await fetch('/api/state',{cache:'no-store'});if(!response.ok)throw Error(`Backend status ${response.status}`);render(await response.json());}catch(error){$('connection').textContent='BACKEND DISCONNECTED';document.querySelectorAll('[data-action]').forEach(button=>button.disabled=true);$('request-error').hidden=false;$('request-error').textContent=`Cannot reach the local backend: ${error.message}. Last results shown below may be stale.`;}finally{setTimeout(refresh,2000);}}
document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{
  if(pending||!token)return;pending=true;$('request-error').hidden=true;
  document.querySelectorAll('[data-action]').forEach(b=>b.disabled=true);
  try{const response=await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json','X-FinGuard-Token':token},body:JSON.stringify({action:button.dataset.action})});const data=await response.json();if(!response.ok)throw Error(data.error||'Job could not start');renderJob(data);$('logs-details').open=true;$('job-title').scrollIntoView({behavior:'smooth',block:'center'});}
  catch(error){$('request-error').hidden=false;$('request-error').textContent=error.message;}
  finally{pending=false;}
}));
const captions={components:'The Python agent runs inside the sandbox. The detector and Ollama inference service run on the trusted host.','end-to-end':'The label-blind investigation follows chronological training and offline evaluation. Test metrics are context, not a runtime acceptance threshold.',investigation:'Conceptual tool sequence. Each proposed call is validated. Completion requires evidence and an allowed simulated note.',deployment:'Direct probes run under a test policy. Inference runs after the policy is narrowed. The final gate checks the collected evidence.'};
document.querySelectorAll('[data-diagram]').forEach(button=>button.addEventListener('click',()=>{const key=button.dataset.diagram;$('diagram').src=`/assets/${key}.svg`;$('diagram').alt=button.textContent+' diagram';$('diagram-caption').textContent=captions[key];$('svg-link').href=`/assets/${key}.svg`;$('png-link').href=`/assets/${key}.png`;$('mermaid-link').href=`/diagrams/${key}.mmd`;document.querySelectorAll('[data-diagram]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));}));
renderJob(null);refresh();
