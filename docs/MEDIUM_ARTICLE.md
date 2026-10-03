# Securing a Fraud Investigation Agent with NVIDIA OpenShell and FinGuard Safety Controls

*Applying the OpenShell software component of NVIDIA Open Agent Safety Platform, application policy guards, and native OCSF audit evidence to a local fraud investigation workflow.*

A fraud score is the beginning of an investigation. An analyst still needs to inspect evidence, understand the operating threshold, and decide what deserves review. An AI agent can help assemble that evidence, but giving it tools creates another engineering problem: deciding what it can read, where it can send data, and which actions it can execute.

FinGuard explores those questions in a local research implementation. It combines historical credit-card transactions, a trained fraud classifier, a Qwen tool-calling agent, and NVIDIA OpenShell. The pipeline runs on an Apple Silicon Mac, with Docker Desktop providing the Linux environment for the sandbox.

The result is a working investigation workflow with measured detector performance and independently checked runtime restrictions. Its banking actions are simulated. It neither moves money nor connects to a production case-management service.

## What the two control layers achieved together

OpenShell supplied an enforcement boundary outside the agent loop. FinGuard supplied transaction scope, tool validation, and evidence requirements inside the application. Their integration completed a real-data investigation while producing independently observable evidence of specific runtime restrictions.

![Observed contributions of NVIDIA OpenShell and FinGuard Safety Controls and their combined outcome](assets/safety-outcomes.png)

*Figure 1. OpenShell and FinGuard address different responsibilities. The nine direct I/O probes test runtime behavior; the completed investigation demonstrates the application workflow. The 14-check integration gate combines those observations with policy, runtime, receiver, and native audit evidence. The counts overlap and must not be added as independent tests.*

The major takeaway is that **useful agent execution and externally enforced restrictions can coexist in the same workflow**. The application can require evidence before accepting a note, while the runtime restricts file and network access even when direct operations bypass the application Guard.

This demonstration did not measure the incremental safety benefit of combining the layers against an OpenShell-only or FinGuard-only baseline. It also did not establish universal prompt-injection resistance or obtain an independent certification. FinGuard Safety Controls is the name of this project's application controls; model instructions against invented facts remain weaker than enforced code checks.

## The architecture separates scoring from investigation

FinGuard gives the classifier and language model different jobs.

The classifier is scikit-learn’s `HistGradientBoostingClassifier`. It trains and scores transactions on the CPU. Its output is an uncalibrated risk score and a threshold selected during validation.

Qwen3 8B runs through Ollama on the Mac’s Metal GPU. It receives a task, requests evidence through tools, and proposes an analyst note. Qwen is a pretrained model in this implementation; it is not fine-tuned on the transaction dataset.

The Python agent loop runs inside OpenShell’s restricted workload. Model inference stays on the trusted Mac host. That distinction matters: the sandbox contains the process choosing and executing tools, while a narrowly allowed network route connects it to the local inference server.

![FinGuard components and trust boundaries](assets/components.png)

*Figure 2. The host scores transactions and serves model inference. The restricted workload contains the agent loop and transaction tools. The operator collects application results and native runtime evidence separately.*

NVIDIA describes its [Open Agent Safety Platform](https://nvidianews.nvidia.com/news/open-agent-safety-platform) as combining OpenShell software with the Sentry reference system design. FinGuard integrates the software runtime, pinned to [OpenShell 0.1.2](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.2). It does not include the Sentry watchdog or BlueField hardware.

## Real data changes what an agent can honestly say

The [ULB and Worldline credit-card fraud dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) contains 284,807 anonymized transactions and 492 fraud labels from two days in September 2013. It is a historical research benchmark rather than a live banking feed.

The available fields are elapsed time, amount, 28 anonymized PCA components, and a fraud label. Customer identities, merchant names, devices, countries, and complaints are unavailable. The published components do not come with meanings that would support an account-takeover narrative.

That limits the agent’s explanation. It can report a detector score above the review threshold. It cannot infer that a customer used a new device abroad. FinGuard’s review instructions explicitly prohibit invented identities, currencies, and meanings for the anonymized components.

The backend also rejects evidence records containing unexpected fields. The agent’s feature store excludes the `Class` label. Ground truth is reserved for offline evaluation, rather than being placed in the model’s context and mistaken for successful investigation.

## Training follows the order of the transactions

The pipeline verifies the source checksum and schema, removes 1,081 duplicate feature rows, then orders the remaining 283,726 transactions by time. Equal timestamps stay in the same partition.

The earliest approximately 60% is used for training, the next 20% for validation, and the final 20% for testing. Training uses balanced class weights. The validation procedure selects the threshold that maximizes recall while reaching at least 90% precision, with an explicitly reported fallback if that target cannot be reached.

For the recorded run, validation achieved the target. The threshold was frozen at approximately 0.6652 before measuring the test partition. No test-based threshold tuning was performed.

![FinGuard data preparation and investigation process](assets/end-to-end.png)

*Figure 3. Detector evaluation and agent investigation use different evidence paths. Test labels support offline metrics; the investigation receives an exported feature row and score without its label.*

The held-out test partition contained 56,746 transactions, including 74 fraud cases. At the frozen threshold, the classifier detected 53 fraud cases, missed 21, and flagged nine non-fraud transactions. The remaining 56,663 non-fraud transactions were not flagged.

That corresponds to **85.48% precision**, **71.62% recall**, and **0.8042 average precision**. Average precision summarizes the precision–recall curve across thresholds; the precision and recall values above describe this particular operating threshold.

These are detector metrics. They do not measure the language model’s reasoning or security. The score is also uncalibrated: a value near 0.99 should not be presented as a 99% probability of fraud. The gap between validation precision and test precision is another reason to keep the test partition separate.

## Four tools make the investigation inspectable

The transaction agent has four tools:

- `read_policy` retrieves the review instructions.
- `transaction_evidence` returns the assigned transaction’s available features.
- `risk_score` returns its detector score, threshold, and review flag.
- `submit_case` records a simulated analyst note.

The model proposes calls, but the application validates names, arguments, and transaction scope. FinGuard’s Runner applies the adaptive Guard, and the backend independently restricts access to the assigned transaction.

Submission requires successful reads of the policy, transaction evidence, and risk score. If evidence is missing, the application returns a denial and identifies what remains to be collected. Model prose alone cannot certify completion. The loop is bounded; failure to produce a permitted submission results in an incomplete or error report.

![Sequence of a guarded FinGuard investigation](assets/investigation.png)

*Figure 4. The conceptual tool sequence. Calls may be grouped differently across runs. The transaction tools execute inside Python rather than calling a live banking API.*

The recorded demonstration investigated `ULB-235645`, selected as the highest-scoring held-out transaction without consulting labels. Its detector score was approximately 0.9997, above the 0.6652 threshold. Qwen completed the workflow in two model calls and four tool calls, recommending review while acknowledging the limits of the anonymized evidence.

This was an intentionally high-risk example. One completed investigation does not establish performance across the dataset. It does show that the model can use the tools, gather the required evidence, and reach an allowed simulated submission.

## Runtime restrictions need a separate test

Application checks describe intended behavior, but the process also needs an external execution boundary. FinGuard’s OpenShell integration places code and evidence under read-only policy and provides writable output and temporary directories. The workload runs as a non-root user, with no effective capabilities, no-new-privileges, an active seccomp filter, and Landlock required at startup.

During an investigation, the deployment network policy permits the configured Python executable to make only `POST /api/chat` requests to the local inference endpoint. The host remains trusted, and Ollama is configured with cloud inference disabled.

FinGuard tests the boundary using direct Python filesystem and network operations that bypass its own Guard and Runner. The nine checks cover an allowed evidence read; denied direct, traversal, and symlink reads of a synthetic decoy; a denied evidence write; an allowed test health request; and denied requests using a forbidden HTTP path, method, or port.

All nine matched their expected outcomes in the recorded run. A same-UID control in plain Docker confirmed that the decoy was readable and the evidence writable without OpenShell. This helps distinguish runtime enforcement from ordinary file permissions. DNS errors and timeouts count as inconclusive, not successful blocking.

## Moving from the test policy to the deployment policy

The test policy temporarily permits a controlled health endpoint so the probes can compare allowed and forbidden requests. Before Qwen runs, the workflow removes that permission and waits for the narrower deployment policy to load.

![FinGuard testing and local deployment process](assets/deployment.png)

*Figure 5. The workflow collects evidence and evaluates a final verification gate. It stops on command errors; it does not automatically relax policy. Probe outcomes are assessed by the final gate.*

Verification combines several observations: the direct probe results, the filesystem control, the active policy, workload configuration, the completed investigation, controlled receiver logs, and native OpenShell audit events in OCSF format.

The captured verification passed all 14 checks. Its native audit snapshot contained 26 events, including three denials that corroborated the tested HTTP and port restrictions. These observations come from the full web-triggered run verified on October 3, 2026 at 14:02 UTC. Application events and native runtime audit events remain separate artifacts; a Python policy decision is not relabeled as a supervisor event.

The existing sandbox can run another investigation with:

```sh
sh scripts/investigate-openshell.sh
```

That command assumes the dataset and model preparation are complete and the local services and sandbox are available. It collects a new report and rechecks the evidence bundle. It reuses the earlier containment probes for that sandbox; a fresh full workflow is needed to repeat those probes.

## Explore the working web demo

FinGuard includes a working local web demo for exploring the complete investigation process. The interface brings the components into one operator workspace, with separate controls for preparing data, training the detector, checking local services, and rerunning an investigation. A full-workflow button executes the complete path through a fresh sandbox.

```sh
.venv/bin/python -m finguard.web
```

The workspace opens at `http://127.0.0.1:8766`. Its progress view follows actual command stages and exposes the execution log. Detector charts, investigation notes, containment outcomes, and verification checks are populated from the generated reports. The architecture view provides the four diagrams above, with editable Mermaid sources and downloadable images.

![FinGuard local web workspace with real pipeline controls and measured results](assets/workspace.png)

*Figure 6. Screenshot of the working FinGuard web demo, showing pipeline controls, measured detector results, and execution progress. These controls ran the full workflow described in this article. The demo runs locally; a public hosted version is not currently provided.*

The demo lets you follow a transaction from detector scoring to a generated review note, inspect the containment checks, and explore the architecture diagrams. It is intended for research and demonstrations, with simulated banking actions.

The backend permits one job at a time and archives the previous OpenShell artifacts before a new job writes results. A failed job retains the previously published results and displays the error. This prevents a stale successful report from being presented as the outcome of a failed execution.

The console itself is a trusted host application. It binds to loopback, checks request origin and a session token for job submission, and accepts named actions rather than arbitrary shell commands. It is not a remotely authenticated banking dashboard. The model's investigation still crosses the separately enforced OpenShell boundary.

## What this implementation establishes

FinGuard now demonstrates real transaction scoring, local language-model tool use, restricted execution, and evidence collection in one reproducible workflow. The reports keep three questions separate: how well the detector identifies fraud, whether the agent completes the required workflow, and whether specific runtime restrictions hold.

Several questions remain open. The dataset spans only two days in 2013, has no customer identifiers for customer-disjoint evaluation, and contains an upstream PCA transformation whose fit scope cannot be audited here. Its metrics are not a forecast of current banking performance.

The agent also needs a broader evaluation of factual accuracy and adversarial behavior. A sandbox cannot guarantee that an allowed note is correct, and nine probes cannot establish resistance to every escape or prompt injection. Production work would additionally require service-side banking authorization, durable case storage, human review, and durable audit delivery.

The useful next experiment is to evaluate those layers independently: vary the agent’s inputs, preserve the external runtime restrictions, and measure both investigation quality and policy failures. That would build on a working system whose evidence is already inspectable.

## Get in touch for a demo

Interested in trying FinGuard, seeing a walkthrough of the web interface, or discussing agent security for financial workflows? Email me at [zga5029@psu.edu](mailto:zga5029@psu.edu) to arrange a demo and discuss local setup, evaluation, or collaboration. You can also leave a comment on this article to start the conversation.
