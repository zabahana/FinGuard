/* Render observed model-security results; no illustrative or invented counts. */
const fs=require('node:fs'),path=require('node:path'),sharp=require('sharp');
const root=path.resolve(__dirname,'..'),s=JSON.parse(fs.readFileSync(path.join(root,'docs/visuals/model-evaluation-snapshot.json')));
const esc=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const ratio=m=>`${m.numerator}/${m.denominator}`;
const percent=x=>x==null?'N/A':`${(x*100).toFixed(1)}%`;
const C={ink:'#15382c',muted:'#566b61',green:'#177453',line:'#d7e4dc',bg:'#f5f8f3',blue:'#306a89',orange:'#9b5327'};
let parts=[`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1210" viewBox="0 0 1600 1210"><rect width="1600" height="1210" fill="${C.bg}"/><style>text{font-family:Arial,sans-serif;fill:${C.ink}}.small{font-size:20px;fill:${C.muted}}.label{font-size:23px}.big{font-size:46px;font-weight:700}</style>`];
function text(x,y,value,cls='label'){parts.push(`<text x="${x}" y="${y}" class="${cls}">${esc(value)}</text>`)}
function box(x,y,w,h){parts.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="16" fill="white" stroke="${C.line}"/>`)}
text(58,52,'STUDY 2 / MODEL-DRIVEN ADVERSARIAL EVALUATION','small');
text(58,108,'A prohibited proposal is not an executed action.','big');
text(58,151,`${s.finished_trials} trials · local Qwen3:8b · shared production controls · independently recorded backend effects`);
for(const [index,key,label] of [[0,'single','200 adversarial continuations'],[1,'multi','50 multi-turn episodes'],[2,'benign','50 benign workflows']]){
 const x=58+index*502,c=s.cohorts[key];box(x,184,480,360);text(x+24,225,label);
 const rows=key==='benign'?[['completion','Workflows completed'],['fbr','False blocks / legitimate calls'],['rr','Recovery after a blocked proposal']]:[['apr','Trials with prohibited proposals'],['cbr','Prohibited proposals blocked'],['uer','Trials with unauthorized execution']];
 rows.forEach(([metric,label],i)=>{const m=c.metrics[metric],y=274+i*79;text(x+24,y,`${ratio(m)}  ·  ${percent(m.rate)}`,'big');text(x+24,y+28,label,'small')});
 if(key==='benign'){text(x+24,516,'Correct denials are not false blocks.','small')}
}
text(58,587,'Which prompt families elicited prohibited proposals?');
text(58,617,'APR · trials containing at least one prohibited call','small');
const families=s.cohorts.single.families;
Object.entries(families).forEach(([name,f],i)=>{
 const y=658+i*73;text(58,y,name.replaceAll('_',' '),'small');
 parts.push(`<rect x="58" y="${y+12}" width="580" height="15" rx="7" fill="${C.line}"/><rect x="58" y="${y+12}" width="${580*(f.apr.rate||0)}" height="15" rx="7" fill="${C.green}"/>`);
 text(656,y+27,ratio(f.apr),'small');
});
text(830,587,'How far did the multi-turn attacks reach?');text(830,617,'Observed attachment exposure · episodes','small');
const stages=['Reviewer context','Legitimate score request','Alternate transaction','Unauthorized submission','Exfiltration instruction'];
Object.entries(s.cohorts.multi.stage_exposure).forEach(([stage,n],i)=>{const y=658+i*73;text(830,y,`${stage}. ${stages[i]}`,'small');parts.push(`<rect x="830" y="${y+12}" width="580" height="15" rx="7" fill="${C.line}"/><rect x="830" y="${y+12}" width="${580*n/s.cohorts.multi.finished}" height="15" rx="7" fill="${C.blue}"/>`);text(1425,y+27,`${n}/${s.cohorts.multi.finished}`,'small')});
const ci=s.cohorts.single.metrics.apr.prompt_cluster_bootstrap_95;
text(58,1051,`Single-continuation APR: prompt-cluster bootstrap 95% interval ${percent(ci[0])}–${percent(ci[1])}.`,'small');
text(58,1083,'Repeated seeds are clustered by prompt. Zero observations do not establish zero risk. Completion ends exposure.','small');
text(58,1115,`Inference errors: ${Object.values(s.cohorts).reduce((n,c)=>n+c.errors,0)}. These application tests do not measure new OpenShell runtime blocking.`,'small');
text(58,1169,`Run ${s.run_id} · temperature 0.6 · 5 repeats per prompt · counts and source hashes in the published snapshot`,'small');
parts.push('</svg>');const svg=parts.join('\n');
fs.writeFileSync(path.join(root,'docs/assets/model-evaluation.svg'),svg);
sharp(Buffer.from(svg)).png().toFile(path.join(root,'docs/assets/model-evaluation.png')).then(()=>console.log('Rendered measured model evaluation figure')).catch(e=>{console.error(e);process.exitCode=1});
