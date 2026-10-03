# FinGuard architecture and processes

Generated from `docs/diagrams/*.mmd` by `scripts/build-visual-guide.py`. Open [the interactive visual guide](visual-guide.html) for component details and measured results.

The diagrams describe the OpenShell path. Direct Python CLI commands remain outside this boundary. Qwen inference runs on the trusted Mac; its Python agent loop runs in the sandbox. TransactionBank tools are in-process operations, not calls to live banking APIs.

## Components and trust boundaries

```mermaid
flowchart TB
    subgraph host[Trusted Mac host]
      data[ULB historical transactions] --> detector[CPU fraud detector]
      detector --> export[Export one held-out row and score]
      model[Ollama and Qwen3 8B on Metal]
      operator[Operator CLI] --> gateway[OpenShell gateway with mTLS]
    end
    subgraph docker[Docker Desktop Linux runtime]
      supervisor[OpenShell supervisor]
      subgraph workload[Restricted agent workload]
        evidence[Read-only evidence without labels]
        loop[Python tool-calling loop]
        guard[Argument validation and FinGuard Guard]
        bank[TransactionBank with transaction scope]
        output[Simulated case and report]
        evidence --> bank
        loop --> guard --> bank --> output
        bank --> loop
      end
      supervisor -. filesystem and network enforcement .-> workload
    end
    export -->|Baked into image| evidence
    gateway -. control plane .-> supervisor
    loop -->|POST /api/chat through enforced channel| model
    model -->|Tool-call proposals| loop
    supervisor --> audit[Native OCSF audit]
    output --> collect[Operator collection and verification]
    audit --> collect
```

[SVG](assets/components.svg) · [PNG](assets/components.png) · [Mermaid source](diagrams/components.mmd)

## Data to investigation

```mermaid
flowchart TB
    raw[Validate source checksum and schema] --> clean[Deduplicate and sort by time]
    clean --> train[Train on earliest 60 percent]
    train --> val[Choose threshold on next 20 percent]
    val --> freeze[Freeze detector and threshold]
    freeze --> test[Evaluate final 20 percent offline]
    freeze --> score[Score held-out features without labels]
    score --> select[Select highest score for demonstration]
    select --> export[Export one row and score]
    export --> sandbox[Build and verify OpenShell sandbox]
    sandbox --> agent[Qwen gathers policy, evidence and score]
    agent --> gate{Required evidence and allowed action?}
    gate -->|Yes| note[Record simulated note]
    gate -->|No| retry[Return denial or review result]
    retry -->|Within bounded loop| agent
    retry -->|No completion or error| incomplete[Incomplete or error report]
    note --> collect[Collect report and native audit]
    collect --> verify[Evaluate local verification gate]
    test -. detector metrics only .-> verify
```

[SVG](assets/end-to-end.svg) · [PNG](assets/end-to-end.png) · [Mermaid source](diagrams/end-to-end.mmd)

## Tool calling sequence

```mermaid
sequenceDiagram
    autonumber
    participant O as Operator
    participant A as Agent loop in sandbox
    participant M as Host Qwen via Ollama
    participant G as Validation and Guard
    participant B as TransactionBank
    O->>A: Run finguard.contained
    A->>M: POST /api/chat through OpenShell
    M-->>A: Proposed tool calls
    loop Required policy, transaction evidence and risk score
        A->>G: Validate tool and arguments
        G->>B: Execute allowed action for assigned transaction
        B-->>A: Evidence without Class label
    end
    A->>M: Continue conversation with tool results
    M-->>A: Propose submit_case
    A->>G: Check required evidence and action policy
    alt Evidence present and action allowed
        G->>B: Append simulated case note in memory
        B-->>A: Simulated case result
        A-->>O: Completed report and application events
    else Missing evidence or policy denial or review
        G-->>A: Do not execute submission
        Note over A,M: Retry within limits or finish incomplete
    end
    Note over O,B: Conceptual successful flow, tool grouping and model turns can vary
```

[SVG](assets/investigation.svg) · [PNG](assets/investigation.png) · [Mermaid source](diagrams/investigation.mmd)

## Testing to local deployment

```mermaid
flowchart TB
    setup[Verify pinned binaries and prepare local mTLS] --> build[Build minimal image with no raw labels or host secrets]
    build --> baseline[Plain Docker control with same UID]
    baseline --> create[Create sandbox with test policy]
    create --> audit[Enable native OCSF and observe activation]
    audit --> probes[Run nine direct I/O probes and process checks]
    probes --> narrow[Remove test health permission and wait for policy]
    narrow --> inference[Run real Qwen investigation]
    inference --> collect[Collect probes, policy, report, receiver and native audit]
    collect --> gate{All verification checks pass?}
    gate -->|Yes| ready[Verified local software deployment]
    gate -->|No| fail[Nonzero exit with evidence retained]
    ready --> rerun[Repeat investigation in existing sandbox]
    rerun --> collect
    note[Commands stop on execution errors; probe outcomes are checked by the final gate]
    note -.-> gate
```

[SVG](assets/deployment.svg) · [PNG](assets/deployment.png) · [Mermaid source](diagrams/deployment.mmd)

## Reading the evidence

Detector metrics come from the chronological held-out test partition. Agent completion means required evidence was gathered and a permitted simulated note was recorded. Nine direct I/O probes test specific runtime controls. These are separate measurements. The end-to-end chart's detector-metrics arrow represents documentation context; the runtime gate does not enforce a minimum detector precision or recall.

The test receiver is removed from the network allowlist before the investigation. Probe results are assessed at the final verification gate, not a separate pre-investigation approval gate. Reruns reuse prior probe evidence for the same sandbox; they do not rerun all probes.

See [OpenShell operations](OPENSHELL.md), [dataset methodology](ULB.md), and [visual documentation maintenance](VISUALS.md).
