import time
from dataclasses import asdict
from .bank import Bank, contains_sensitive
from .models import Session, Verdict
from .policy import Guard


class Runner:
    def __init__(self, mode="adaptive", session=None, bank=None):
        self.guard = Guard(mode)
        self.session = session or Session()
        self.bank = bank if bank is not None else Bank()
        self.events = []

    def act(self, action):
        start = time.perf_counter_ns()
        decision = self.guard.decide(action, self.session)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        result = None
        if decision.verdict == Verdict.ALLOW:
            result = self.bank.execute(action)
            if action.kind == "read" and contains_sensitive(result):
                self.session.sensitive_read = True
        # Never persist raw payloads or tool results in the trace.
        self.events.append({"sequence": len(self.events) + 1,
                            "kind": action.kind, "target": action.target.split("?")[0],
                            "method": action.method, "decision": asdict(decision),
                            "executed": decision.verdict == Verdict.ALLOW,
                            "decision_latency_ms": elapsed_ms})
        return decision, result
