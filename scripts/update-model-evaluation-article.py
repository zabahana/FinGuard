"""Refresh the article's expanded-evaluation section from the published snapshot."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
s=json.loads((root/'docs/visuals/model-evaluation-snapshot.json').read_text())
a=s['cohorts']['single'];m=s['cohorts']['multi'];b=s['cohorts']['benign']
def ratio(metric): return f"{metric['numerator']}/{metric['denominator']}"
def pct(rate): return 'not estimable' if rate is None else f'{100*rate:.1f}%'
ci=a['metrics']['apr']['prompt_cluster_bootstrap_95']
block=(f"{ratio(m['metrics']['cbr'])} prohibited proposals were blocked" if m['metrics']['cbr']['denominator'] else 'no prohibited proposals were observed, so its control block rate is not estimable')
section=f'''<!-- MODEL_EVALUATION_START -->
## Beyond three examples: a 300-trial model evaluation

The original three continuations above are illustrative. The next experiment adds **200 adversarial continuations, 50 benign workflows, and 50 multi-turn episodes**. Forty attack prompts span transaction-scope abuse, evidence skipping, tool/schema abuse, sensitive-note submission, and exfiltration instructions. Ten benign task variants and ten staged attack sequences complete the corpus. Each prompt receives five runs with recorded seeds, temperature 0.6, and the same local Qwen3:8b model.

The experiment measures four different events. **Attack Proposal Rate (APR)** counts adversarial trials with a prohibited tool proposal. **Control Block Rate (CBR)** measures the fraction of prohibited proposals blocked. **Unauthorized Execution Rate (UER)** counts trials with an actual prohibited backend execution. **False Block Rate (FBR)** measures incorrect blocking of legitimate proposals in benign workflows. Workflow completion is reported separately.

In the single-continuation cohort, **{ratio(a['metrics']['apr'])} trials produced prohibited proposals ({pct(a['metrics']['apr']['rate'])} APR)**. The controls blocked **{ratio(a['metrics']['cbr'])} prohibited proposals**. Unauthorized execution was **{ratio(a['metrics']['uer'])} trials**. These are observed application-control results, not a general probability of agent safety.

![Measured model-security outcomes, attack-family proposal rates, and multi-turn stage exposure](assets/model-evaluation.png)

*Figure 0. The expanded study separates proposals, blocking, backend execution, and legitimate task completion. Family bars show observed proposal rates; stage bars show which instructions actually reached the model. The original deterministic OpenShell experiment remains a separate source of runtime evidence.*

The benign cohort completed **{ratio(b['metrics']['completion'])} workflows ({pct(b['metrics']['completion']['rate'])})**, while false blocks were **{ratio(b['metrics']['fbr'])} legitimate proposals**. The model also produced **{b['prohibited_proposals']} prohibited proposals on benign tasks**. Correctly rejecting an invalid or premature call is not a false block, but a model that fails to recover can still leave a legitimate task unfinished. Accepted notes establish workflow completion, not factual accuracy.

### Multi-turn attacks: report exposure, not just outcomes

The staged episodes introduce misleading reviewer context, request legitimate evidence, substitute another transaction ID, attempt an unauthorized submission, and finally request exfiltration. Each new instruction appears beside a real tool reply while the conversation and application state persist. A successful submission ends the episode rather than forcing extra attack turns.

Of the {m['finished']} episodes, **{m['stage_exposure']['3']} reached the alternate-transaction stage, {m['stage_exposure']['4']} reached the unauthorized-submission stage, and {m['stage_exposure']['5']} reached the exfiltration stage**. Multi-turn APR was **{ratio(m['metrics']['apr'])}**; {block}. Unauthorized execution was **{ratio(m['metrics']['uer'])} episodes**. An undelivered later-stage instruction is not evidence of a successful defense against that stage.

### What makes these counts auditable

Every proposal is classified against a separate authorization specification before its control outcome is scored. The evaluator uses the same parser, prerequisite checks, Guard, and scoped backend as the production agent. Backend instrumentation records successful reads and in-memory note mutations independently of the model's claims and the control's verdict. Raw transcripts and effects stay in local artifacts; the public snapshot contains hashes, denominators, seeds, outcomes, and selected decision traces.

The main study recorded **{sum(c['errors'] for c in s['cohorts'].values())} inference errors**. Errors are disclosed and excluded from rate denominators, not treated as safe outcomes. A prompt-cluster bootstrap gives a descriptive 95% interval of **{pct(ci[0])}–{pct(ci[1])}** for single-continuation APR. Five repeats of one prompt are related observations. All-zero execution counts and all-success blocking counts yield degenerate bootstrap intervals, which do not establish zero risk or guaranteed blocking.

These trials run on the **trusted host and evaluate application controls**. The agent still has no general file-read or network-send tool, so exfiltration instructions do not create a new model-driven OpenShell blocking result. The study uses one transaction and one model; sensitive-note trials start with all prerequisites read, whereas other cohorts start with transaction evidence only. Curated prompt families, differing starting states, and limited later-stage exposure constrain comparisons and generalization.

The [evaluation methodology](https://github.com/zabahana/FinGuard/blob/main/docs/MODEL_EVALUATION.md), [versioned prompt corpus](https://github.com/zabahana/FinGuard/blob/main/evaluation/model-security-corpus.json), and [recorded evaluation snapshot](https://github.com/zabahana/FinGuard/blob/main/docs/visuals/model-evaluation-snapshot.json) make the design and reported counts inspectable. The web UI adds cohort selection, rate denominators, uncertainty intervals, attack-family outcomes, and per-trial seed and exposure views.
<!-- MODEL_EVALUATION_END -->

'''
p=root/'docs/MEDIUM_ARTICLE.md';text=p.read_text()
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
