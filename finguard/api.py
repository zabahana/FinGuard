"""Optional local synthetic API. Bind to loopback; this is not a production bank API."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .models import Action, Verdict
from .runner import Runner

app = FastAPI(title="FinGuard Synthetic Bank", version="0.1.0")


class CaseNote(BaseModel):
    customer_id: str
    text: str = Field(min_length=1, max_length=4000)


def execute(action):
    # This API is stateless; multi-step semantic history is enforced by the agent Runner.
    runner = Runner("adaptive")
    decision, result = runner.act(action)
    if decision.verdict != Verdict.ALLOW:
        raise HTTPException(403, decision.reason)
    return result


@app.get("/health")
def health():
    return {"status": "ok", "synthetic": True, "backend": "virtual_simulation"}


@app.get("/api/risk-score")
def risk_score(customer_id: str):
    return execute(Action("api", "/api/risk-score", customer_id=customer_id))


@app.get("/api/transaction-history")
def transactions(customer_id: str):
    return execute(Action("api", "/api/transaction-history", customer_id=customer_id))


@app.post("/api/case-management")
def case_note(note: CaseNote):
    execute(Action("api", "/api/case-management", "POST", customer_id=note.customer_id, payload=note.text))
    return {"status": "validated", "persisted": False, "synthetic": True}
