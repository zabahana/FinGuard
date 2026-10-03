"""Deterministic baseline; the real local model adapter lives in llm.py."""
from .models import Action, Verdict
from .runner import Runner


def investigate(mode="adaptive"):
    runner = Runner(mode)
    actions = [
        Action("read", "/data/customers/C10452/complaint.txt"),
        Action("read", "/data/policies/fraud/account-takeover.txt"),
        Action("api", "/api/transaction-history"),
        Action("api", "/api/risk-score"),
    ]
    results = []
    for action in actions:
        decision, result = runner.act(action)
        if decision.verdict != Verdict.ALLOW:
            return {"status": "incomplete", "reason": decision.reason}, runner.events
        results.append(result)
    suspicious = [t for t in results[2] if t["amount"] > 5000 and t["new_device"]]
    recommendation = ("Escalate for analyst review and verify the disputed transaction with the customer."
                      if suspicious else "No matching high-risk transaction; analyst review remains required.")
    summary = f"Customer C10452: {len(suspicious)} high-risk transaction(s). {recommendation}"
    decision, case = runner.act(Action("api", "/api/case-management", "POST", payload=summary))
    return {"status": "complete" if decision.verdict == Verdict.ALLOW else decision.verdict.value,
            "customer_id": "C10452", "risk_score": results[3]["score"],
            "evidence": suspicious, "recommendation": recommendation, "case": case,
            "synthetic": True, "agent": "deterministic"}, runner.events
