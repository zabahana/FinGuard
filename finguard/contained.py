"""Run the ULB agent against an exported transaction inside OpenShell."""
import json
from pathlib import Path

from .llm import OllamaClient
from .ulb import TransactionBank, investigate_transaction, TOOLS, POLICY_PATH


class FileTransactionBank(TransactionBank):
    def __init__(self, directory="/evidence"):
        self.directory = Path(directory)
        evidence = json.loads((self.directory / "transaction.json").read_text())
        super().__init__(evidence["row"], evidence["score"], evidence["threshold"])

    def execute(self, action):
        if action.kind == "read" and action.target == POLICY_PATH:
            return (self.directory / "policy.txt").read_text()
        return super().execute(action)


def main():
    bank = FileTransactionBank()
    client = OllamaClient(tools=TOOLS, endpoint="http://host.openshell.internal:11434/api/chat")
    report, events = investigate_transaction(transaction_id=bank.transaction_id, bank=bank, client=client)
    report.update(runtime="NVIDIA OpenShell", runtime_version="0.1.2",
                  evidence_source="operator-exported held-out transaction and trained detector score")
    root = Path("/output")
    (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (root / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    print(json.dumps(report, indent=2))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
