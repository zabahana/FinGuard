from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(frozen=True)
class Task:
    customer_id: str = "C10452"
    purpose: str = "account_takeover_investigation"


@dataclass(frozen=True)
class Action:
    kind: str
    target: str
    method: str = "GET"
    customer_id: str = "C10452"
    payload: str = ""


@dataclass(frozen=True)
class Decision:
    verdict: Verdict
    reason: str
    layer: str
    risk: float


@dataclass
class Session:
    task: Task = field(default_factory=Task)
    denied_count: int = 0
    sensitive_read: bool = False
