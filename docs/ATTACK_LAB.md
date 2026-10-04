# Bounded adversarial evaluation

Run the **Attack Lab** from the local web UI, or from the repository root:

```sh
sh scripts/run-attack-lab.sh
```

Prerequisites are the same trained ULB detector, local Qwen model, Docker Desktop and registered OpenShell gateway used by the main demo. The lab prepares its own image, runs two plain Docker baselines and two separate OpenShell sandboxes, collects native audit evidence, and stops its two sandboxes after collection. Existing investigation results are not overwritten. A receiver started by this job is stopped afterward. Run one job at a time; the CLI and UI share build and receiver resources.

## Experimental design

There are 18 deterministic fixtures per configuration: seven application attacks, seven direct runtime attacks, and four legitimate controls. The four configurations are an unchecked fixture, FinGuard controls, OpenShell, and both layers.

The unchecked application adapter records synthetic acceptance and bypasses all application enforcement, including the independently scoped backend. It does not execute a banking action. This baseline is deliberately permissive, not an ordinary production configuration or an evaluation of an unguarded model. The guarded modes replay the same proposals through the production argument parser, evidence prerequisite, Runner, adaptive Guard, and transaction backend. Runtime fixtures call Python I/O directly and bypass FinGuard in every configuration. Non-OpenShell modes still use ordinary Docker containment and the same UID/image.

Application fixtures cover wrong transaction, unknown tool, extra argument, missing argument, non-string argument, premature submission, and a synthetic sensitive identifier. Legitimate score retrieval and complete submission are positive controls. Runtime fixtures cover absolute, traversal and symlink decoy reads, writing evidence, forbidden HTTP path, method, and port. Allowed evidence read and health request are positive controls. All network payloads are synthetic and go only to controlled local receivers. Real host secrets and external domains are not tested. `/etc/passwd` is not a suitable forbidden-file example here because `/etc` is in the current read allowlist.

## Model trials

Three additional prompts place malicious instructions in a test-only untrusted attachment returned with a transaction ID. The real ULB feature record is not modified. One Qwen continuation is sampled for each prompt, with fixed model options. Its proposed calls are evaluated through the production application checks, and saved alongside the decision evidence.

These trials test secret/exfiltration instructions, transaction-scope override, and skipping evidence. No general filesystem or network tool is exposed. A model request stopped by the application cannot produce a downstream runtime denial. A prompt that does not elicit a malicious call is reported as such, not as proof that OpenShell blocked it. These are three single-continuation observations, not full investigations, repeated stochastic trials, or a general prompt-injection benchmark.

## Evidence and interpretation

Timestamped `artifacts/attack-lab/` directories contain per-mode reports, receiver observations, sandbox metadata, effective policy, runtime image details, and native OCSF for the OpenShell modes. Network cases identify matching OCSF line numbers and selected native fields from the same sandbox. Filesystem results report the observed OS error; no filesystem OCSF event is inferred. Application denials cite adapter replies or Guard events. In particular, malformed calls and missing-evidence submissions can be rejected before Runner creates an event.

The expected-outcome gate checks all deterministic fixtures, receiver observations, and native evidence for network denials. It does not certify semantic quality, use model trials as a safety pass rate, or count the 72 repeated outcomes as independent random attacks. Successful attacks in intentionally unchecked configurations are expected outcomes. Aggregate scores always distinguish blocked attacks from matching expectations.

The active test policy keeps the controlled health endpoint available throughout the lab; it is not the main workflow's narrower deployment policy. Its restricted inference endpoint permits the model trials. The experiment demonstrates complementary control coverage in this harness, not a quantified population-level safety improvement.

## Publication artifacts

After selecting a completed run:

```sh
python3 scripts/publish-attack-lab.py
node scripts/render-attack-lab-figure.cjs
node scripts/render-medium-article.cjs
```

The render scripts require `sharp` and `marked`, respectively. The exported snapshot is an allowlisted subset of observations with a source hash. Review the article's numerical statements against the selected snapshot before publishing. The UI screenshot can be refreshed with `node scripts/check-attack-lab-ui.cjs`; `--run` also executes the lab.
