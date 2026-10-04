# FinGuard: What Happens When a Financial AI Agent Ignores the Rules?

*Testing application authorization, runtime isolation, prompt injection, and control ablation with NVIDIA OpenShell.*

**What happens when an AI agent ignores your security instructions?**

Telling an agent to stay within its assigned transaction or avoid unauthorized data transfers is useful. Those instructions still need an enforcement boundary.

I built **FinGuard** to test what happens when the model proposes something it should not do. It is an experimental security harness for tool-using financial AI agents: FinGuard Safety Controls enforce application authorization, while NVIDIA OpenShell restricts the agent process’s filesystem and network capabilities.

A fraud investigation supplies the financial use case. The transactions are real and anonymized; banking actions are simulated. The project’s contribution is the security evaluation, not a claim that the fraud classifier makes an agent safe.

## The result in three numbers

![Model behavior versus application enforcement: prohibited proposals, blocked proposals, and unauthorized execution](assets/model-behavior.png)

*Figure 1. In 200 adversarial continuations, ${single_proposals} produced prohibited proposals, ${single_blocks} prohibited proposals were blocked, and ${single_executions} trials produced unauthorized backend execution. These are observed results from this bounded experiment, not estimates of universal agent safety.*

**The model wasn’t perfectly compliant. The system didn’t require it to be.** In these observed cases, application authorization prevented prohibited proposals from becoming backend actions.

## Results at a glance

Two studies answer different questions. **Study 1** tests whether the control layers enforce their rules. **Study 2** measures what the model proposes, what executes, and whether a legitimate workflow finishes.

| Study and cohort | Measurement | Observed result |
|---|---|---|
| Study 1 · combined controls | Deterministic attacks denied | **${deterministic_attacks}** |
| Study 1 · combined controls | Legitimate controls allowed | **${positive_controls}** |
| Study 1 · four modes | Outcomes matching expectations | **${expected_outcomes}** |
| Study 2 · adversarial | Trials with prohibited proposals | **${single_proposals} (${single_proposal_rate})** |
| Study 2 · adversarial | Prohibited proposals blocked | **${single_blocks}** |
| Study 2 · adversarial | Trials with unauthorized execution | **${single_executions}** |
| Study 2 · benign | Legitimate proposals incorrectly blocked | **${false_blocks}** |
| Study 2 · benign | Workflows completed | **${completion} (${completion_rate})** |
| Study 2 · benign | Recovery after a block | **${recovery} (${recovery_rate})** |
| Study 2 · multi-turn | Episodes with unauthorized execution | **${multi_executions}** |

These counts are not pooled into one security score. The first study tests deterministic enforcement; the second tests model behavior and workflow outcomes. The multi-turn episodes never reached their final exfiltration stage, so zero execution does not demonstrate resistance to that unexposed attack.

## Two layers, two responsibilities

FinGuard checks whether a tool call belongs to the assigned transaction, has valid arguments, and satisfies the workflow’s evidence requirements. Before accepting a case note, it requires successful reads of the policy, transaction evidence, and risk score. Sensitive identifiers are prohibited in submitted notes.

OpenShell supplies an external boundary for the process running those tools. It restricts filesystem and network capabilities even when an operation bypasses the application checks.

![Observed contributions of NVIDIA OpenShell and FinGuard Safety Controls](assets/safety-outcomes.png)

*Figure 2. Application authorization and runtime enforcement have separate responsibilities and evidence paths. The nine direct-I/O probes and 14-check integration gate shown here overlap; they are not additional independent attacks.*

The harness tests both paths: prohibited tool proposals and direct filesystem/network operations. The host, inference service, operator console, and policy configuration remain trusted. Controlled receivers and synthetic decoys make the runtime attempts observable without accessing real secrets or sending transaction data to an external destination.

FinGuard uses the OpenShell software component of NVIDIA’s Open Agent Safety Platform, pinned to version 0.1.2. It does not include Sentry or BlueField hardware, and the project has no independent security certification.

## Study 1: Control-Layer Ablation

I tested **14 attacks and four positive controls across four configurations**: unchecked fixture, FinGuard only, OpenShell only, and both layers. No language model participates in this study.

![Four-way control ablation and separate application and runtime evidence paths](assets/attack-lab-results.png)

*Figure 3. FinGuard denied seven application-abuse fixtures; OpenShell denied seven direct runtime attacks. Together, they denied all 14 and allowed all four legitimate controls. Across the four configurations, all 72 outcomes matched expectations. These are repeated fixtures, not 72 independent random attacks.*

**Removing either layer reopened the exact class of failure that layer was designed to control in this harness.**

The comparison has a deliberate boundary: “unchecked” application calls go to a permissive adapter that records synthetic acceptance, not a real bank. Ordinary Docker containment remains around the configurations without OpenShell. This isolates the tested controls without pretending to represent an unguarded production agent.

![Fourteen attempted abuses grouped by their enforcing layer](assets/attack-catalogue.png)

*Figure 4. Seven application-abuse cases, four filesystem attacks, and three network attacks. The positive controls separately verify score retrieval, complete submission, evidence reading, and a permitted health request.*

The evidence identifies where an attempt stopped. A wrong-transaction proposal can end at the application’s scope check. A direct request to the forbidden receiver bypasses that check, fails under OpenShell, and has a matching native audit denial. Receiver logs corroborate that the request did not arrive.

Filesystem cases cite actual operating-system errors and comparison runs where the operations succeeded. Network cases use native OpenShell events in the Open Cybersecurity Schema Framework (OCSF) format. Timeouts and DNS failures count as inconclusive, not as successful blocking. The [study methodology and recorded evidence](https://github.com/zabahana/FinGuard/blob/main/docs/ATTACK_LAB.md) explain the distinctions.

## Study 2: Model-Driven Adversarial Evaluation

The second study asks how often a model proposes prohibited actions—and what happens when it does.

The **300-trial evaluation** used Qwen3:8b with recorded seeds and temperature 0.6:

- **200 adversarial continuations:** 40 prompts, each repeated five times, covering transaction scope, evidence skipping, tool/schema abuse, sensitive-note submission, and exfiltration instructions.
- **50 benign workflows:** ten legitimate task variants, each repeated five times.
- **50 multi-turn episodes:** ten staged attack sequences, each repeated five times.

The attack text appears in a synthetic, untrusted attachment beside a real tool result. It does not alter the transaction’s feature record. Every episode starts with fresh application state.

For technical readers, the measurements have five names: **Attack Proposal Rate (APR)** counts trials with prohibited proposals; **Control Block Rate (CBR)** counts blocked prohibited proposals; **Unauthorized Execution Rate (UER)** counts trials with prohibited backend effects; **False Block Rate (FBR)** counts legitimate proposals incorrectly blocked; and **Recovery Rate (RR)** counts workflows completing after a block among workflows containing a block. Recovery is derived from saved traces and excludes single-continuation trials, which have no follow-up budget.

![Measured model-security outcomes, attack-family proposal rates, and multi-turn exposure](assets/model-evaluation.png)

*Figure 5. The results separate model proposals, enforcement, backend effects, and task completion. Family bars show prohibited-proposal frequency; stage bars show which instructions actually reached the model. These application-control tests do not measure new OpenShell runtime denials.*

In the 200 adversarial continuations, **${single_proposals} produced prohibited proposals**. All **${single_blocks}** observed prohibited proposals were blocked, and **${single_executions}** trials produced unauthorized backend execution. The [published snapshot](https://github.com/zabahana/FinGuard/blob/main/docs/visuals/model-evaluation-snapshot.json) preserves the counts, seeds, source hashes, and selected traces.

## Security worked. The agent still struggled.

The benign tasks reveal the more interesting reliability problem.

**None of the 133 legitimate proposals were incorrectly blocked—but only 34 of 50 workflows completed.**

Here is what happened in the affected workflows: the agent tried to submit a case before it had gathered the required evidence. FinGuard correctly rejected the premature submission. The agent then needed to gather what was missing and try again.

Only **one of the 17 affected workflows recovered** and recorded an authorized note. The other 16 did not finish within the evaluation. Another 33 workflows completed without encountering a block.

That is **${completion_rate} completion and ${recovery_rate} recovery after rejection**, despite no observed false blocking of legitimate proposals. A correct rejection is not a false positive simply because the model subsequently fails to finish.

The lesson is to **measure security and workflow reliability separately**. Preventing an unauthorized action, recovering from a rejection, and completing a task are different outcomes. The traces identify premature tool use and failure to recover; they do not tell us how these same tasks would perform with enforcement removed. An accepted note also does not establish that its reasoning is correct.

### Multi-turn attacks: exposure matters

The staged episodes introduced misleading reviewer context, requested legitimate evidence, substituted another transaction ID, attempted an unauthorized submission, and finally requested exfiltration. Each new instruction appeared beside a real tool reply while conversation and application state persisted.

**All 50 episodes reached the alternate-transaction stage, ten reached the unauthorized-submission stage, and none reached exfiltration.** Successful submission ended an episode; later attack turns were not forced into a completed workflow.

No prohibited proposals or unauthorized executions were observed in these 50 episodes. With no prohibited proposals, a blocking rate cannot be estimated. And with no exposure to the final stage, this result says nothing about resistance to that exfiltration instruction.

### Illustrative prompt-injection traces

Three earlier qualitative examples show how individual decisions are evidenced. They use different prompts and setup and are **not pooled into the 300-trial study**.

![Three injected instructions compared with Qwen’s proposed calls and the actual decisions](assets/prompt-injection-story.png)

*Figure 6. The application rejected a wrong-transaction proposal and a premature submission. The decoy-exfiltration instruction produced a policy read instead. Each example is one continuation.*

That last distinction matters: **Qwen did not attempt exfiltration in that example, so I do not claim OpenShell stopped model-driven exfiltration.** The agent has no general file-read or network-send tool. Direct runtime probes establish separate evidence about OpenShell’s restrictions.

## What the results can—and cannot—tell us

The evaluator classifies proposals against a separate authorization specification, then runs them through the production parser, prerequisite checks, Guard, and scoped backend. Backend instrumentation records actual reads and simulated note mutations independently of the model’s claims and the control’s verdict. A model saying “done” is not evidence of execution.

The main study recorded **zero inference errors**. Repeated runs of one prompt are related observations. Resampling whole prompt groups gives a descriptive 95% interval of **${proposal_interval}** for the proportion of adversarial trials producing prohibited proposals, and **${recovery_interval}** for recovery after a block. These small, curated samples do not estimate universal agent safety; all-zero or all-success observations do not prove zero risk or guaranteed blocking.

The study uses one model and one transaction. Sensitive-note trials begin with all required evidence already read; other cohorts begin with transaction evidence only. The model evaluation exercises application controls on the trusted host, while Study 1 separately tests runtime restrictions. These different starting states, evidence paths, and exposure limits constrain the conclusions.

The financial task uses real, anonymized ULB/Worldline transactions. The agent receives a detector score and label-blind evidence, then proposes a simulated review note. The classifier’s held-out precision was **85.48%** and recall **71.62%**; those numbers measure fraud classification, not agent security. [Appendix A](#appendix-a) retains the dataset and model methodology.

The [evaluation methodology](https://github.com/zabahana/FinGuard/blob/main/docs/MODEL_EVALUATION.md) and [versioned prompt corpus](https://github.com/zabahana/FinGuard/blob/main/evaluation/model-security-corpus.json) provide the full experimental detail. The findings do not establish production banking readiness or resistance to every prompt injection or sandbox escape.

## Explore the demo

The web interface brings both studies into one workspace. Readers can compare control configurations, inspect attack families and decision traces, switch between model-evaluation cohorts, and see how far the multi-turn episodes progressed.

![FinGuard’s interactive security evaluation workspace](assets/workspace.png)

*Figure 7. The demo displays measured outcomes, their denominators, and separate application/runtime evidence. It includes investigation results and architecture diagrams; banking actions remain simulated.*

## Five things I learned building FinGuard

1. **Do not confuse model compliance with authorization.** A model refusing an unsafe instruction is useful. Authorization still needs an enforced boundary.
2. **Application authorization and runtime isolation solve different problems.** FinGuard checks transaction scope, evidence, and workflow. OpenShell restricts filesystem and network capabilities.
3. **Test controls by removing them.** The same attack succeeding when its relevant control is removed makes the enforcement result easier to interpret.
4. **Measure what actually executed.** Record backend effects, receiver observations, and runtime evidence; model output alone cannot establish success.
5. **Measure security and recovery separately.** A control can correctly stop an unsafe action while the agent fails to recover and complete its legitimate task.

## Get in touch for a demo

Explore the code, evaluation corpus, results, and diagrams in the [FinGuard GitHub repository](https://github.com/zabahana/FinGuard).

For a walkthrough of the interactive demo or a discussion about security evaluation for financial AI agents, contact me at [zga5029@psu.edu](mailto:zga5029@psu.edu). I welcome conversations about the findings, evaluation methods, and collaboration.

<a id="appendix-a"></a>

## Appendix A: Fraud model and dataset methodology

### Dataset and evidence boundaries

The [ULB and Worldline credit-card fraud dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) contains 284,807 anonymized transactions and 492 fraud labels from two days in September 2013. It is a historical research benchmark rather than a live banking feed.

The available fields are elapsed time, amount, 28 anonymized PCA components, and a fraud label. Customer identities, merchant names, devices, countries, and complaints are unavailable. The published components do not come with meanings that would support an account-takeover narrative.

That limits the agent’s explanation. It can report a detector score above the review threshold. It cannot infer that a customer used a new device abroad. FinGuard’s review instructions explicitly prohibit invented identities, currencies, and meanings for the anonymized components.

The backend also rejects evidence records containing unexpected fields. The agent’s feature store excludes the `Class` label. Ground truth is reserved for offline evaluation, rather than being placed in the model’s context and mistaken for successful investigation.

### Training and held-out results

The pipeline verifies the source checksum and schema, removes 1,081 duplicate feature rows, then orders the remaining 283,726 transactions by time. Equal timestamps stay in the same partition.

The earliest approximately 60% is used for training, the next 20% for validation, and the final 20% for testing. Training uses balanced class weights. The validation procedure selects the threshold that maximizes recall while reaching at least 90% precision, with an explicitly reported fallback if that target cannot be reached.

For the recorded run, validation achieved the target. The threshold was frozen at approximately 0.6652 before measuring the test partition. No test-based threshold tuning was performed.

The held-out test partition contained 56,746 transactions, including 74 fraud cases. At the frozen threshold, the classifier detected 53 fraud cases, missed 21, and flagged nine non-fraud transactions. The remaining 56,663 non-fraud transactions were not flagged.

That corresponds to **85.48% precision**, **71.62% recall**, and **0.8042 average precision**. Average precision summarizes the precision–recall curve across thresholds; the precision and recall values above describe this particular operating threshold.

These are detector metrics. They do not measure the language model’s reasoning or security. The score is also uncalibrated: a value near 0.99 should not be presented as a 99% probability of fraud. The gap between validation precision and test precision is another reason to keep the test partition separate.

### Limits of the financial test case

The dataset spans only two days in 2013, has no customer identifiers for customer-disjoint evaluation, and contains an upstream PCA transformation whose fit scope cannot be audited here. Its metrics are not a forecast of current banking performance. FinGuard trains the classifier; Qwen remains pretrained and is not fine-tuned on these transactions.

## Sources and references

### Data and models

- [ULB and Worldline credit-card fraud dataset on Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud): the original anonymized transaction data and labels. FinGuard's deduplication, chronological split, threshold selection, and reported metrics are project-specific experiments, documented in the [dataset methodology](https://github.com/zabahana/FinGuard/blob/main/docs/ULB.md).
- [Qwen3 8B model card](https://huggingface.co/Qwen/Qwen3-8B) and [Ollama qwen3:8b distribution](https://ollama.com/library/qwen3:8b): the pretrained language model and the packaged model used for inference. FinGuard does not train or fine-tune Qwen.
- [scikit-learn HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html): the fraud detector implementation. [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), and [joblib](https://joblib.readthedocs.io/en/stable/) support data preparation, numerical operations, and model persistence.

### Runtime security and inference

- [NVIDIA OpenShell 0.1.2 source and release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.2): the pinned software runtime used by this implementation. The [NVIDIA platform announcement](https://nvidianews.nvidia.com/news/open-agent-safety-platform) supplies the broader Open Agent Safety Platform context; Sentry hardware is not part of this demo.
- [Ollama source code](https://github.com/ollama/ollama): the inference server. [Docker Desktop documentation](https://docs.docker.com/desktop/): the container environment on the development Mac.
- [Open Cybersecurity Schema Framework](https://ocsf.io/): the schema framework used by the native security event export. OCSF is an event schema, not a certification of FinGuard or its security claims.

Upstream projects retain their own licenses and dataset/model terms. The references identify dependencies and provenance; they do not imply endorsement by their authors.
