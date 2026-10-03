"""Application-level policy simulation; NOT an OS sandbox or OpenShell implementation."""
import re
from .bank import contains_sensitive
from .models import Decision, Verdict


class RuntimePolicy:
    def evaluate(self, action, session):
        customer = session.task.customer_id
        allowed = False
        if session.task.purpose == "ulb_transaction_review":
            allowed = (action.kind == "read" and action.method == "GET" and action.target ==
                       "/data/policies/fraud/transaction-review.txt") or (
                action.kind == "api" and action.customer_id == customer and
                (action.method, action.target) in {
                    ("GET", "/api/transaction-evidence"), ("GET", "/api/risk-score"),
                    ("POST", "/api/case-management")})
            return Decision(Verdict.ALLOW if allowed else Verdict.DENY,
                            "Transaction scope allowlist" if allowed else "Outside transaction scope",
                            "runtime_simulation", 0.0 if allowed else 1.0)
        if action.kind == "read":
            # Exact virtual paths deny traversal, symlink aliases and sibling customers.
            allowed = action.method == "GET" and action.target in {
                f"/data/customers/{customer}/profile.json",
                f"/data/customers/{customer}/complaint.txt",
                f"/data/transactions/{customer}.json",
                "/data/policies/fraud/account-takeover.txt",
            }
        elif action.kind == "api":
            allowed = action.customer_id == customer and (action.method, action.target) in {
                ("GET", "/api/risk-score"), ("GET", "/api/transaction-history"),
                ("POST", "/api/case-management"),
            }
        elif action.kind == "network":
            allowed = action.method == "POST" and action.target == "https://inference.local/v1/chat/completions"
        return Decision(Verdict.ALLOW if allowed else Verdict.DENY,
                        "Exact runtime allowlist match" if allowed else "Outside runtime allowlist",
                        "runtime_simulation", 0.0 if allowed else 1.0)


class RiskEngine:
    def evaluate(self, action, session):
        outbound = (action.kind == "network" or
                    (action.kind == "api" and action.method != "GET"))
        if outbound and (contains_sensitive(action.payload) or
                         re.search(r"\b\d{3}-\d{2}-\d{4}\b", action.payload)):
            return Decision(Verdict.DENY, "Sensitive identifier in outbound content", "semantic", 1.0)
        if action.kind == "policy":
            return Decision(Verdict.DENY, "Agents cannot expand policy", "semantic", 1.0)
        if outbound and session.sensitive_read:
            return Decision(Verdict.REVIEW, "Outbound action after sensitive read requires review", "semantic", 0.6)
        if outbound and session.denied_count >= 2:
            return Decision(Verdict.REVIEW, "Repeated denials before outbound action", "semantic", 0.7)
        return Decision(Verdict.ALLOW, "No semantic risk rule triggered", "semantic", 0.1)


class Guard:
    MODES = ("unrestricted", "runtime", "adaptive")

    def __init__(self, mode="adaptive"):
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode: {mode}")
        self.mode = mode
        self.runtime = RuntimePolicy()
        self.risk = RiskEngine()

    def decide(self, action, session):
        if self.mode == "unrestricted":
            return Decision(Verdict.ALLOW, "Unrestricted virtual baseline", "baseline", 0.0)
        # Adaptive decisions can only narrow the runtime allowlist.
        decision = self.runtime.evaluate(action, session)
        if decision.verdict == Verdict.ALLOW and self.mode == "adaptive":
            decision = self.risk.evaluate(action, session)
        if decision.verdict == Verdict.DENY:
            session.denied_count += 1
        return decision
