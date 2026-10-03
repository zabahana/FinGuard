"""Build offline documentation from an explicit allowlist of local report fields.

No raw transactions, model conversations, recommendations, credentials or native
logs are published. Missing artifacts fail the build instead of inventing data.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read(relative):
    return json.loads((ROOT / relative).read_text())


def main():
    sources = ["artifacts/ulb/training_report.json", "artifacts/openshell/verification.json",
               "artifacts/openshell/output/report.json", "artifacts/openshell/output/containment.json"]
    training, verification, agent, containment = map(read, sources)
    snapshot = {
        "training_at": training["created_at"], "verified_at": verification["verified_at"],
        "raw_rows": training["raw_rows"], "retained_rows": training["retained_rows"],
        "duplicates_removed": training["duplicates_removed"],
        "partitions": {key: {field: value[field] for field in ("rows", "fraud_count")}
                       for key, value in training["partitions"].items()},
        "threshold": training["threshold"],
        "test": {key: training["test"][key] for key in ("precision", "recall", "average_precision",
                 "true_positives", "false_positives", "false_negatives", "true_negatives")},
        "agent": {key: agent[key] for key in ("status", "model", "model_calls", "tool_calls",
                  "transaction_id", "detector_score", "detector_threshold", "case_persisted")},
        "verification": {key: verification[key] for key in ("passed", "checks", "native_ocsf_event_count", "native_denials", "scope")},
        "probes": [{key: probe[key] for key in ("name", "expected", "observed", "passed")}
                   for probe in containment["probes"]],
        "sources": [{"path": source, "sha256": hashlib.sha256((ROOT / source).read_bytes()).hexdigest()}
                    for source in sources],
    }
    serialized = json.dumps(snapshot, indent=2) + "\n"
    (DOCS / "visuals" / "snapshot.json").write_text(serialized)
    template = (DOCS / "visuals" / "template.html").read_text()
    assert template.count("__SNAPSHOT__") == 1
    (DOCS / "visual-guide.html").write_text(template.replace("__SNAPSHOT__", serialized.replace("<", "\\u003c")))
    diagrams = [("components", "Components and trust boundaries"), ("end-to-end", "Data to investigation"),
                ("investigation", "Tool calling sequence"), ("deployment", "Testing to local deployment")]
    text = ["# FinGuard architecture and processes\n",
            "Generated from `docs/diagrams/*.mmd` by `scripts/build-visual-guide.py`. "
            "Open [the interactive visual guide](visual-guide.html) for component details and measured results.\n",
            "The diagrams describe the OpenShell path. Direct Python CLI commands remain outside this boundary. "
            "Qwen inference runs on the trusted Mac; its Python agent loop runs in the sandbox. "
            "TransactionBank tools are in-process operations, not calls to live banking APIs.\n"]
    for name, title in diagrams:
        text.extend([f"## {title}\n", f"```mermaid\n{(DOCS / 'diagrams' / (name + '.mmd')).read_text().strip()}\n```\n",
                     f"[SVG](assets/{name}.svg) · [PNG](assets/{name}.png) · [Mermaid source](diagrams/{name}.mmd)\n"])
    text.extend(["## Reading the evidence\n",
                 "Detector metrics come from the chronological held-out test partition. Agent completion means "
                 "required evidence was gathered and a permitted simulated note was recorded. Nine direct I/O "
                 "probes test specific runtime controls. These are separate measurements. The end-to-end chart's "
                 "detector-metrics arrow represents documentation context; the runtime gate does not enforce a "
                 "minimum detector precision or recall.\n",
                 "The test receiver is removed from the network allowlist before the investigation. Probe results "
                 "are assessed at the final verification gate, not a separate pre-investigation approval gate. "
                 "Reruns reuse prior probe evidence for the same sandbox; they do not rerun all probes.\n",
                 "See [OpenShell operations](OPENSHELL.md), [dataset methodology](ULB.md), "
                 "and [visual documentation maintenance](VISUALS.md).\n"])
    (DOCS / "ARCHITECTURE.md").write_text("\n".join(text))
    print("Built docs/visual-guide.html, docs/ARCHITECTURE.md and allowlisted snapshot.json")


if __name__ == "__main__":
    main()
