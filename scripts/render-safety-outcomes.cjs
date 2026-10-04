/* Publication figure from the article's saved evidence snapshot. Requires sharp. */
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
const s = JSON.parse(fs.readFileSync(path.join(root, 'docs/visuals/snapshot.json'), 'utf8'));
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const t = (x, y, text, size=23, color='#263e34', weight=400) => `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(text)}</text>`;
const passed = s.probes.filter(p=>p.passed).length;
const checks = Object.values(s.verification.checks).filter(Boolean).length;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1110" viewBox="0 0 1200 1110" role="img" aria-labelledby="title description">
<title id="title">What OpenShell and FinGuard achieved together</title><desc id="description">OpenShell enforced runtime boundaries, FinGuard constrained the investigation workflow, and their integration completed a real-data investigation with independent containment evidence. Results cover a local demonstration, not certification or a comparative safety benchmark.</desc>
<rect width="1200" height="1110" fill="#fafcf9"/>
<g font-family="Arial, sans-serif">
${t(48,54,'FINGUARD / OBSERVED OUTCOMES',17,'#246548',600)}
${t(48,110,'One investigation. Two layers of control.',40,'#163425',700)}
${t(48,151,'Separate responsibilities, connected by a verifiable execution record.',23,'#617168')}
<rect x="48" y="190" width="536" height="450" rx="7" fill="#edf5ee" stroke="#cfddd1"/>
<rect x="616" y="190" width="536" height="450" rx="7" fill="#ffffff" stroke="#cfddd1"/>
${t(76,233,'EXTERNAL RUNTIME BOUNDARY',16,'#246548',600)}
${t(76,277,'NVIDIA OpenShell',31,'#163425',700)}
${t(76,318,'Controls what the process can access.',22)}
${t(76,369,'• Read-only evidence; restricted file access',21)}
${t(76,405,'• Network destination, method and path rules',21)}
${t(76,441,'• Restricted identity and process controls',21)}
${t(76,477,'• Native supervisor audit evidence',21)}
<path d="M76 507H556" stroke="#cfddd1"/>
${t(76,550,`${passed} / ${s.probes.length} direct I/O probes matched expectations`,23,'#163425',700)}
${t(76,589,`${s.verification.native_denials} native network denials corroborated blocking`,20)}
${t(76,616,'Probes bypassed the FinGuard Guard and Runner.',18,'#617168')}
${t(644,233,'APPLICATION WORKFLOW CONTROLS',16,'#246548',600)}
${t(644,277,'FinGuard Safety Controls',31,'#163425',700)}
${t(644,318,'Controls which proposed actions execute.',22)}
${t(644,369,'• Validate tool names and arguments',21)}
${t(644,405,'• Restrict tools to the assigned transaction',21)}
${t(644,441,'• Require evidence before case submission',21)}
${t(644,477,'• Keep labels out; bound the agent loop',21)}
<path d="M644 507H1124" stroke="#cfddd1"/>
${t(644,550,`${s.agent.model_calls} model calls · ${s.agent.tool_calls} tool calls · ${s.agent.status}`,23,'#163425',700)}
${t(644,589,'Required evidence gathered; simulated note recorded.',20)}
${t(644,616,'Completion does not certify reasoning quality.',18,'#617168')}
<path d="M316 640V674H884V640M600 674V696" fill="none" stroke="#246548" stroke-width="2"/>
<path d="M593 689L600 698L607 689" fill="none" stroke="#246548" stroke-width="2"/>
<rect x="48" y="709" width="1104" height="206" rx="7" fill="#193f2d"/>
${t(76,748,'ACHIEVED TOGETHER',16,'#cde4d4',600)}
${t(76,790,'A real-data investigation completed within tested boundaries.',29,'#ffffff',700)}
${t(76,833,'Application evidence + independent runtime observations + native audit',23,'#e0eee4')}
${t(76,875,`${checks} / ${Object.keys(s.verification.checks).length} integration checks passed`,26,'#ffffff',700)}
${t(640,875,'Local software deployment · banking actions simulated',18,'#e0eee4')}
${t(48,958,'Takeaway: make useful agent work observable and constrain its execution.',25,'#163425',600)}
${t(48,1000,'No certification, general prompt-injection guarantee, or population-level safety estimate.',20,'#617168')}
${t(48,1034,'The 14 checks combine evidence above; they are not 14 additional independent attack tests.',19,'#617168')}
${t(48,1075,`Source: saved FinGuard reports · verified ${s.verified_at} · OpenShell 0.1.2`,16,'#617168')}
</g></svg>`;
const target = path.join(root,'docs/assets/safety-outcomes');
fs.writeFileSync(target+'.svg',svg);
sharp(Buffer.from(svg)).resize(2400,2220).png().toFile(target+'.png').then(()=>console.log('Rendered safety-outcomes.svg and .png')).catch(error=>{console.error(error);process.exitCode=1;});
