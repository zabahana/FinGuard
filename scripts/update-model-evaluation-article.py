"""Render the editorial Medium template with the existing studies' measured values.

No inference is run. Edit docs/MEDIUM_ARTICLE.template.md to retain narrative
changes when refreshing the reported results.
"""
import json
from pathlib import Path
from string import Template

root=Path(__file__).resolve().parents[1]
study=json.loads((root/'docs/visuals/model-evaluation-snapshot.json').read_text())
lab=json.loads((root/'docs/visuals/attack-lab-snapshot.json').read_text())
a=study['cohorts']['single']['metrics']
b=study['cohorts']['benign']['metrics']
m=study['cohorts']['multi']['metrics']
def ratio(metric): return f"{metric['numerator']}/{metric['denominator']}"
def percent(value): return 'not estimable' if value is None else f'{value*100:g}%'
def interval(metric):
    bounds=metric['prompt_cluster_bootstrap_95']
    return 'not estimable' if bounds is None else f'{bounds[0]*100:.1f}%–{bounds[1]*100:.1f}%'
cases=lab['modes']['both']['cases']
attacks=[c for c in cases if c['attack']]
controls=[c for c in cases if not c['attack']]
all_cases=[c for mode in lab['modes'].values() for c in mode['cases']]
values={
    'single_proposals':ratio(a['apr']),'single_proposal_rate':percent(a['apr']['rate']),
    'single_blocks':ratio(a['cbr']),'single_executions':ratio(a['uer']),
    'false_blocks':ratio(b['fbr']),'completion':ratio(b['completion']),
    'completion_rate':percent(b['completion']['rate']),
    'recovery':ratio(b['rr']),'recovery_rate':f"{b['rr']['rate']*100:.1f}%" if b['rr']['rate'] is not None else 'not estimable',
    'multi_executions':ratio(m['uer']),
    'proposal_interval':interval(a['apr']),'recovery_interval':interval(b['rr']),
    'deterministic_attacks':f"{sum(c['observed']=='denied' for c in attacks)}/{len(attacks)}",
    'positive_controls':f"{sum(c['observed']=='allowed' for c in controls)}/{len(controls)}",
    'expected_outcomes':f"{sum(c['passed'] for c in all_cases)}/{len(all_cases)}",
}
# This narrative describes this recorded study. Require editorial review before
# automatically substituting a different run into its qualitative findings.
if study['run_id']!='main-20261003-213305':
    raise SystemExit('New run detected: review the Medium narrative and template before updating its results')
source=Template((root/'docs/MEDIUM_ARTICLE.template.md').read_text()).substitute(values)
(root/'docs/MEDIUM_ARTICLE.md').write_text(source)
print('Updated Medium article from editorial template and recorded study')
