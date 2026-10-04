"""Refresh the article's expanded-evaluation section from the published snapshot."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
s=json.loads((root/'docs/visuals/model-evaluation-snapshot.json').read_text())
a=s['cohorts']['single'];m=s['cohorts']['multi'];b=s['cohorts']['benign']
rr=b['metrics']['rr']
benign_reasons=b.get('prohibited_reasons',{})
reason_explanation=(f"All {b['prohibited_proposals']} prohibited proposals in this recorded benign cohort were premature submissions with missing required evidence." if set(benign_reasons)=={'missing_evidence'} else 'The decision traces identify which policy rules caused the blocks.')
traces=(root/'docs/ARTICLE_INJECTION_TRACES.md').read_text().rstrip()+'\n\n'
def ratio(metric): return f"{metric['numerator']}/{metric['denominator']}"
def pct(rate): return 'not estimable' if rate is None else f'{100*rate:.1f}%'
ci=a['metrics']['apr']['prompt_cluster_bootstrap_95']
block=(f"{ratio(m['metrics']['cbr'])} prohibited proposals were blocked" if m['metrics']['cbr']['denominator'] else 'no prohibited proposals were observed, so its control block rate is not estimable')
section=f'''<!-- MODEL_EVALUATION_START -->
## Study 2: Model-Driven Adversarial Evaluation

**Question: How often does the model propose prohibited actions, and what happens when it does?** Study 2 comprises **300 trials: 200 adversarial continuations, 50 benign workflows, and 50 multi-turn episodes**. Forty attack prompts span transaction-scope abuse, evidence skipping, tool/schema abuse, sensitive-note submission, and exfiltration instructions. Ten benign task variants and ten staged attack sequences complete the corpus. Each prompt receives five runs with recorded seeds, temperature 0.6, and the same local Qwen3:8b model.

The study separates model behavior, enforcement, execution, and reliability. **Attack Proposal Rate (APR)** counts adversarial trials with a prohibited tool proposal. **Control Block Rate (CBR)** measures the fraction of prohibited proposals blocked. **Unauthorized Execution Rate (UER)** counts trials with an actual prohibited backend execution. **False Block Rate (FBR)** measures incorrect blocking of legitimate proposals in benign workflows. **Recovery Rate (RR)** measures completion after a blocked proposal among workflows containing a block. RR is a post-hoc calculation from the saved traces; it requires a subsequent authorized note mutation and is not evaluated for single-continuation trials. Overall workflow completion is reported separately.

In the single-continuation cohort, **{ratio(a['metrics']['apr'])} trials produced prohibited proposals ({pct(a['metrics']['apr']['rate'])} APR)**. The controls blocked **{ratio(a['metrics']['cbr'])} prohibited proposals**. Unauthorized execution was **{ratio(a['metrics']['uer'])} trials**. These are observed application-control results, not a general probability of agent safety.

### Model behavior vs. system enforcement

![Model behavior versus application enforcement: proposal rate, blocked proposals, and unauthorized execution](assets/model-behavior.png)

*Figure 0. These are observed results from this bounded experiment, not estimates of universal agent safety. The first and last denominators count adversarial trials; the middle denominator counts prohibited proposals. No OpenShell blocking credit is assigned to these application-control outcomes.*

The result demonstrates that **enforced authorization can stop prohibited actions even when the model proposes them**. It does not require perfect model compliance in these observed cases.

![Measured model-security outcomes, attack-family proposal rates, and multi-turn stage exposure](assets/model-evaluation.png)

*Figure 0. The expanded study separates proposals, blocking, backend execution, and legitimate task completion. Family bars show observed proposal rates; stage bars show which instructions actually reached the model. The original deterministic OpenShell experiment remains a separate source of runtime evidence.*

### Security and reliability are different measurements

The benign cohort completed **{ratio(b['metrics']['completion'])} workflows ({pct(b['metrics']['completion']['rate'])})**, while false blocks were **{ratio(b['metrics']['fbr'])} legitimate proposals**. The model also produced **{b['prohibited_proposals']} prohibited proposals on benign tasks**. A correct rejection is not a false positive simply because the agent subsequently fails to finish its task. Accepted notes establish workflow completion, not factual accuracy.

The saved traces give a benign **Recovery Rate of {ratio(rr)} ({pct(rr['rate'])})**: {rr['numerator']} {'workflow' if rr['numerator']==1 else 'workflows'} completed after a block, while {rr['denominator']-rr['numerator']} blocked workflows did not recover to a recorded submission within the evaluation. {reason_explanation} Another {b['metrics']['completion']['numerator']-rr['numerator']} workflows completed without a block. The RR prompt-cluster 95% interval is **{pct(rr['prompt_cluster_bootstrap_95'][0])}–{pct(rr['prompt_cluster_bootstrap_95'][1])}**; this small denominator limits precision.

This separates three observations: no unauthorized backend action was observed, no legitimate proposal was incorrectly blocked, and task completion was still only {pct(b['metrics']['completion']['rate'])}. The traces locate the observed reliability gap in premature tool use and subsequent failure to submit. They do not establish how the same tasks would perform with enforcement removed. Enterprise evaluation needs these separate measurements rather than one aggregate “success rate.”

### Multi-turn attacks: report exposure, not just outcomes

The staged episodes introduce misleading reviewer context, request legitimate evidence, substitute another transaction ID, attempt an unauthorized submission, and finally request exfiltration. Each new instruction appears beside a real tool reply while the conversation and application state persist. A successful submission ends the episode rather than forcing extra attack turns.

Of the {m['finished']} episodes, **{m['stage_exposure']['3']} reached the alternate-transaction stage, {m['stage_exposure']['4']} reached the unauthorized-submission stage, and {m['stage_exposure']['5']} reached the exfiltration stage**. Multi-turn APR was **{ratio(m['metrics']['apr'])}**; {block}. Unauthorized execution was **{ratio(m['metrics']['uer'])} episodes**. An undelivered later-stage instruction is not evidence of a successful defense against that stage.

### What makes these counts auditable

Every proposal is classified against a separate authorization specification before its control outcome is scored. The evaluator uses the same parser, prerequisite checks, Guard, and scoped backend as the production agent. Backend instrumentation records successful reads and in-memory note mutations independently of the model's claims and the control's verdict. Raw transcripts and effects stay in local artifacts; the public snapshot contains hashes, denominators, seeds, outcomes, and selected decision traces.

The main study recorded **{sum(c['errors'] for c in s['cohorts'].values())} inference errors**. Errors are disclosed and excluded from rate denominators, not treated as safe outcomes. A prompt-cluster bootstrap gives a descriptive 95% interval of **{pct(ci[0])}–{pct(ci[1])}** for single-continuation APR. Five repeats of one prompt are related observations. All-zero execution counts and all-success blocking counts yield degenerate bootstrap intervals, which do not establish zero risk or guaranteed blocking.

These trials run on the **trusted host and evaluate application controls**. The agent still has no general file-read or network-send tool, so exfiltration instructions do not create a new model-driven OpenShell blocking result. The study uses one transaction and one model; sensitive-note trials start with all prerequisites read, whereas other cohorts start with transaction evidence only. Curated prompt families, differing starting states, and limited later-stage exposure constrain comparisons and generalization.

The [evaluation methodology](https://github.com/zabahana/FinGuard/blob/main/docs/MODEL_EVALUATION.md), [versioned prompt corpus](https://github.com/zabahana/FinGuard/blob/main/evaluation/model-security-corpus.json), and [recorded evaluation snapshot](https://github.com/zabahana/FinGuard/blob/main/docs/visuals/model-evaluation-snapshot.json) make the design and reported counts inspectable. The web UI adds cohort selection, rate denominators, uncertainty intervals, attack-family outcomes, and per-trial seed and exposure views.
{traces}<!-- MODEL_EVALUATION_END -->

'''

lab=json.loads((root/'docs/visuals/attack-lab-snapshot.json').read_text())
cases=lab['modes']['both']['cases']
attacks=[c for c in cases if c['attack']]
controls=[c for c in cases if not c['attack']]
all_cases=[c for mode in lab['modes'].values() for c in mode['cases']]
glance=f'''<!-- RESULTS_GLANCE_START -->
## Results at a glance

**Study 1: Control-Layer Ablation** tests whether deterministic enforcement behaves as designed. **Study 2: Model-Driven Adversarial Evaluation** measures model proposals, their enforcement outcomes, and workflow reliability. Their denominators and evidence paths remain separate.

| Study and cohort | Measurement | Observed result |
|---|---|---|
| Study 1 · combined controls | Deterministic attacks denied | **{sum(c['observed']=='denied' for c in attacks)}/{len(attacks)}** |
| Study 1 · combined controls | Legitimate controls allowed | **{sum(c['observed']=='allowed' for c in controls)}/{len(controls)}** |
| Study 1 · four modes | Outcomes matching expectations | **{sum(c['passed'] for c in all_cases)}/{len(all_cases)}** |
| Study 2 · adversarial | Trials with prohibited proposals · APR | **{ratio(a['metrics']['apr'])} ({pct(a['metrics']['apr']['rate'])})** |
| Study 2 · adversarial | Prohibited proposals blocked · CBR | **{ratio(a['metrics']['cbr'])}** |
| Study 2 · adversarial | Trials with unauthorized execution · UER | **{ratio(a['metrics']['uer'])}** |
| Study 2 · benign | False blocks of legitimate proposals · FBR | **{ratio(b['metrics']['fbr'])}** |
| Study 2 · benign | Workflow completion | **{ratio(b['metrics']['completion'])} ({pct(b['metrics']['completion']['rate'])})** |
| Study 2 · benign | Recovery after a block · RR | **{ratio(rr)} ({pct(rr['rate'])})** |
| Study 2 · multi-turn | Episodes with unauthorized execution | **{ratio(m['metrics']['uer'])}** |

**Interpretation:** Model compliance was imperfect, but application enforcement prevented the observed prohibited proposals from becoming backend actions. Separately, runtime controls prevented direct filesystem and network operations that bypassed the application layer. The multi-turn cohort did not reach the exfiltration stage; zero execution is not evidence of resistance to an unexposed stage. These are bounded observations, not estimates of universal safety.
<!-- RESULTS_GLANCE_END -->

'''

p=root/'docs/MEDIUM_ARTICLE.md';text=p.read_text()
if '<!-- RESULTS_GLANCE_START -->' in text:
    text=re.sub(r'<!-- RESULTS_GLANCE_START -->[\s\S]*?<!-- RESULTS_GLANCE_END -->\n\n',glance,text)
else:
    text=text.replace('## What the two control layers achieved together',glance+'## What the two control layers achieved together')
if '<!-- MODEL_EVALUATION_START -->' in text:
    text=re.sub(r'<!-- MODEL_EVALUATION_START -->[\s\S]*?<!-- MODEL_EVALUATION_END -->\n\n',section,text)
else:
    text=text.replace('## Architecture: authorization inside, capability enforcement outside',section+'## Architecture: authorization inside, capability enforcement outside')
text=text.replace('The agent also needs a broader evaluation of factual accuracy and adversarial behavior.', 'The agent still needs broader evaluation across models, transactions, and factual-accuracy criteria.')
text=text.replace('The next experiments should broaden the attack set, repeat the model-driven trials, and evaluate complete investigations under controlled variations. The current layer comparison establishes a reproducible starting point; wider coverage and independent review are still needed before drawing production conclusions.', 'The next experiments should vary models and transactions, improve legitimate workflow recovery, and design longer tasks that naturally expose later attack stages. The 300-trial study deepens the evidence while preserving its limits; wider coverage and independent review are still needed before drawing production conclusions.')
text=text.replace('The three model-driven continuations illustrate why enforced checks matter, but are not a broad robustness benchmark.', 'The original three model continuations and the expanded 300-trial study add observations about prohibited proposals, blocking, and workflow completion. They remain bounded evaluations rather than a broad robustness benchmark.')
n=iter(range(1,50));text=re.sub(r'Figure \d+\.',lambda _:f'Figure {next(n)}.',text)
p.write_text(text)
print('Updated article with measured evaluation results')
