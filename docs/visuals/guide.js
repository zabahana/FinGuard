/* Offline presentation only. No model execution, fetch, telemetry or live claims. */
'use strict';
const snapshot = JSON.parse(document.getElementById('snapshot').textContent);
const byId = id => document.getElementById(id);
const components = {
  detector: ['Trusted host / CPU', 'A dedicated model ranks transaction risk', 'HistGradientBoostingClassifier learns from the earliest training partition. Validation selects the operating threshold; the held-out test labels measure performance.', 'Checksum-verified ULB data during training; held-out features during scoring.', 'Uncalibrated score, frozen threshold, and one exported evidence record.', 'The agent cannot read training labels or detector artifacts inside its sandbox.', '../finguard/fraud.py'],
  model: ['Trusted host / Metal GPU', 'Qwen proposes the next tool call', 'Ollama serves the pretrained qwen3:8b model on the Mac. The Python agent loop sends the conversation through OpenShell’s allowed inference channel.', 'System instructions and permitted tool results.', 'Structured tool-call proposals, including a proposed case note.', 'Model weights and inference run outside the sandbox. The local host and Ollama are trusted; cloud inference is disabled.', '../finguard/llm.py'],
  agent: ['Restricted workload / Python', 'The application checks every proposed action', 'The adapter validates tool names and arguments. Runner applies the adaptive Guard. TransactionBank independently restricts actions to the assigned transaction.', 'Read-only exported evidence, review policy, and tool proposals.', 'A simulated note in memory, report.json, and application events.jsonl.', 'Evidence must be gathered before submission. Policy permission does not prove the note is factually correct. No live bank API is connected.', '../finguard/ulb.py'],
  runtime: ['Docker Linux / OpenShell 0.1.2', 'Enforcement sits outside the agent loop', 'The mTLS gateway controls a supervisor and separate workload. Required Landlock, non-root execution, seccomp and network policy restrict the runtime.', 'Minimal image, composed filesystem policy, and explicit network rules.', 'A restricted workload and native enforcement events.', 'Deployment allows only POST /api/chat to host.openshell.internal:11434 for the configured Python executable. Sentry hardware is not present.', '../integration/openshell/policy.yaml'],
  audit: ['Trusted operator / verification', 'Independent evidence supports bounded claims', 'The collector joins direct probe outcomes, receiver observations, active policy, runtime configuration, model completion, and native supervisor OCSF events.', 'Runtime evidence from the same sandbox and a same-UID plain Docker filesystem control.', 'Timestamped verification.json and a reproducible evidence bundle.', 'Nine passing probes cover specific operations. Existing-sandbox reruns reuse those probe results; they do not constitute continuous red teaming.', '../scripts/verify-openshell.py'],
};
function selectComponent(key) {
  const item = components[key];
  ['component-location','component-title','component-body','component-input','component-output','component-limit'].forEach((id,index) => byId(id).textContent = item[index]);
  byId('component-code').href = item[6];
  document.querySelectorAll('[data-component]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.component === key)));
}
document.querySelectorAll('[data-component]').forEach(button => button.addEventListener('click', () => selectComponent(button.dataset.component)));
selectComponent('detector');
const diagrams = {
  components: ['Components and trust boundaries', 'The host handles scoring and model inference; the sandbox contains the Python agent and in-process transaction tools. Dotted arrows indicate control and enforcement.'],
  'end-to-end': ['Data preparation through investigation', 'Chronological training and offline evaluation feed a label-blind demonstration. Detector metrics provide context; runtime verification does not gate on a precision or recall target.'],
  investigation: ['Conceptual tool-calling sequence', 'The model proposes calls; application checks determine execution. Grouping and turn counts can vary. Completion requires successful evidence reads and an allowed simulated submission.'],
  deployment: ['Testing to local deployment', 'Probe outcomes are checked at the final gate. Test-only network access is removed before model execution. Existing-sandbox reruns collect new investigation evidence while reusing earlier probes.'],
};
function selectDiagram(key) {
  byId('diagram').src = `assets/${key}.svg`;
  byId('diagram').alt = diagrams[key][0];
  byId('diagram-caption').textContent = diagrams[key][1];
  byId('diagram-svg').href = `assets/${key}.svg`;
  byId('diagram-png').href = `assets/${key}.png`;
  byId('diagram-source').href = `diagrams/${key}.mmd`;
  document.querySelectorAll('[data-diagram]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.diagram === key)));
}
document.querySelectorAll('[data-diagram]').forEach(button => button.addEventListener('click', () => selectDiagram(button.dataset.diagram)));
selectDiagram('components');
byId('toggle-size').addEventListener('click', () => {
  const actual = document.querySelector('.diagram-scroll').classList.toggle('actual');
  byId('toggle-size').textContent = actual ? 'Fit diagram' : 'Show actual size';
  byId('toggle-size').setAttribute('aria-pressed', String(actual));
});
function element(tag, text, className) { const node = document.createElement(tag); node.textContent = text; if (className) node.className = className; return node; }
const number = value => value.toLocaleString('en-US');
const percent = value => (value * 100).toFixed(2) + '%';
byId('snapshot-date').textContent = `Saved verification: ${snapshot.verified_at} · Detector trained: ${snapshot.training_at}`;
[[percent(snapshot.test.precision),'Held-out detector precision'],[percent(snapshot.test.recall),'Held-out detector recall'],[`${snapshot.probes.filter(p => p.passed).length} / ${snapshot.probes.length}`,'Containment probes matching expectations']].forEach(([value,label]) => {
  const div = element('div','','metric'); div.append(element('strong',value),element('span',label)); byId('metrics').append(div);
});
Object.entries(snapshot.partitions).forEach(([name,partition]) => {
  const row = element('div','','bar-row'); const label = element('div','','bar-label');
  label.append(element('span',name),element('span',`${number(partition.rows)} · ${number(partition.fraud_count)} fraud labels`));
  const track = element('div','','track'); const fill = element('div','','fill'); fill.style.width = `${partition.rows / snapshot.retained_rows * 100}%`; track.append(fill); row.append(label,track); byId('split-bars').append(row);
});
byId('data-caption').textContent = `Source: training_report.json · September 2013 transactions · ${number(snapshot.raw_rows)} raw rows → ${number(snapshot.retained_rows)} after removing ${number(snapshot.duplicates_removed)} duplicates. Bar length is share of retained rows (0–100%).`;
[['true_positives','Fraud → flagged'],['false_negatives','Fraud → not flagged'],['false_positives','Non-fraud → flagged'],['true_negatives','Non-fraud → not flagged']].forEach(([key,label]) => { const div=element('div','','outcome'); div.append(element('strong',number(snapshot.test[key])),element('span',label)); byId('confusion').append(div); });
[['Model',snapshot.agent.model],['Outcome',snapshot.agent.status],['Transaction',snapshot.agent.transaction_id],['Score / threshold',`${snapshot.agent.detector_score.toFixed(4)} / ${snapshot.threshold.toFixed(4)}`],['Model / tool calls',`${snapshot.agent.model_calls} / ${snapshot.agent.tool_calls}`],['Bank case persisted',String(snapshot.agent.case_persisted)],['Test average precision',snapshot.test.average_precision.toFixed(4)]].forEach(([label,value]) => byId('agent-summary').append(element('dt',label),element('dd',value)));
snapshot.probes.forEach(probe => {const li=element('li',''); li.append(element('span',probe.name.replaceAll('_',' ')),element('b',`${probe.passed ? 'PASS' : 'FAIL'} · ${probe.observed}`)); byId('probes').append(li);});
const checks=Object.entries(snapshot.verification.checks);
byId('gate-summary').textContent = `${snapshot.verification.passed ? 'PASS' : 'FAIL'} · ${checks.filter(([,v])=>v).length}/${checks.length} verification checks · ${snapshot.verification.native_ocsf_event_count} native audit events, ${snapshot.verification.native_denials} denials`;
checks.forEach(([name,passed])=>byId('gate-checks').append(element('li',`${passed ? 'PASS' : 'FAIL'} — ${name.replaceAll('_',' ')}`)));
snapshot.sources.forEach(source=>byId('sources').append(element('p',`${source.path}\nSHA-256 ${source.sha256}`)));
