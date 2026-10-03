# Research plan

## Source review

The saved FinGuard document proposes four levels: deterministic containment validation, six adversarial attack families, semantic policy-gap experiments, and an adaptive policy layer. The implementation includes the original local simulation, Qwen inference on Apple Silicon, a real ULB fraud detector, and a verified OpenShell 0.1.2 Docker deployment with bounded real I/O probes. Brev deployment, Sentry hardware and comprehensive agent-security evaluation remain future work. See OPENSHELL.md for the exact verified boundary and remaining limits.

The document leaves model/version, cloud provisioning, database schema, policy granularity, approval authority, scenario ground truth and statistical protocol unspecified. Initial decisions are Python 3.10+, virtual fixtures, deterministic actions, task scope C10452, and three comparison modes. SQLite/PostgreSQL persistence and an LLM are not needed for this first harness milestone; PostgreSQL remains the target service store.

## Hypotheses

- H1: real runtime containment reduces successful prohibited filesystem, network, process and credential actions.
- H2: stronger controls can impair legitimate task completion. Measure denial and review friction separately.
- H3: some harmful flows remain technically permitted by runtime rules; semantic controls can reduce these flows.

Current simulations verify the evaluation plumbing and demonstrate H2/H3 examples by construction. They do not empirically establish any hypothesis.

## Scenario coverage

The 18 templates include two legitimate workflows; complaint prompt injection; direct, DNS, WebSocket and inference-channel exfiltration; traversal, symlink aliases, environment and cross-customer reads; wire transfer, HTTP method and customer-scope abuse; policy expansion; subprocess and encoded leakage chains; and SSN disclosure into case notes.

The complaint stimulus documents the malicious instruction, but the current harness supplies the corresponding action directly. It does not ask a model to interpret the complaint. Redirects, alternate binaries, mounted volumes, raw sockets, actual process isolation and real privilege changes require Linux probes and are not implemented here.

## Metric contract

Every report includes raw counts alongside rates. Rates with no eligible observations are null. Security metrics use action-level denominators; completion uses legitimate scenario-level denominators. A review is neither an allow nor an explicit deny. Report both automatic completion and review workload to avoid overstating utility. Do not interpret virtual Python decision latency as detection latency or runtime overhead.

## Real experiment protocol

Pin the OS, kernel, GPU driver, OpenShell build, effective policy, model weights, inference server and harness revision. Archive hashes and full configuration for each run. Randomize condition order and use separate prompt-development and held-out scenario sets. Compare unrestricted isolated baseline, OpenShell only, and OpenShell plus FinGuard. Keep fixture content and task scope matched across conditions.

Record whether each malicious instruction induced a tool attempt, whether runtime denied it, whether sensitive bytes reached a controlled sink, and whether the legitimate task completed. Track confidence intervals over independent task/attack variants rather than repeated deterministic templates. Review ambiguous outcomes manually. Record review latency and decisions without automatically approving policy expansion.

## Acceptance gates

The local milestone must complete the example investigation, deny reference-prohibited actions in runtime mode, expose the semantic gap in runtime mode, hold or deny the covered semantic attacks in adaptive mode, preserve utility costs, and pass regression tests. These are implementation checks.

The real containment milestone requires independent evidence from OS operations and correlated enforcement telemetry, including failed startup controls and unexpected allow events. Keep runtime enforcement failures distinct from insufficient-policy failures. Any permissive diagnostic environment must be isolated and contain only synthetic data.
