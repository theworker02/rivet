from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .vocation import QualificationState


@dataclass(frozen=True)
class QualificationRecord:
    skill_id: str
    score: float
    state: QualificationState
    validator: str
    timestamp: float
    signature: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


class PassportSigner:
    """Dependency-free HMAC signer; production deployments can replace this with device identity crypto."""

    def __init__(self, secret: bytes) -> None:
        self.secret = secret

    def sign(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self.secret, encoded, hashlib.sha256).hexdigest()

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        return hmac.compare_digest(self.sign(payload), signature)


@dataclass
class AgentPassport:
    agent_id: str
    platform: str
    primary_role: str | None = None
    secondary_roles: tuple[str, ...] = ()
    restrictions: tuple[str, ...] = ()
    qualifications: list[QualificationRecord] = field(default_factory=list)

    def issue(self, skill_id: str, score: float, state: QualificationState, validator: str, signer: PassportSigner, timestamp: float | None = None) -> QualificationRecord:
        if not 0.0 <= score <= 1.0:
            raise ValueError("qualification score must be between 0 and 1")
        issued = timestamp or time.time()
        unsigned = {"skill_id": skill_id, "score": score, "state": state.value, "validator": validator, "timestamp": issued}
        record = QualificationRecord(skill_id, score, state, validator, issued, signer.sign(unsigned))
        self.qualifications.append(record)
        return record

    def export(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "platform": self.platform,
            "primary_role": self.primary_role,
            "secondary_roles": list(self.secondary_roles),
            "restrictions": list(self.restrictions),
            "qualifications": [qualification.to_dict() for qualification in self.qualifications],
        }


class PassportVerifier:
    def __init__(self, signer: PassportSigner) -> None:
        self.signer = signer

    def verify(self, record: QualificationRecord) -> bool:
        unsigned = {"skill_id": record.skill_id, "score": record.score, "state": record.state.value, "validator": record.validator, "timestamp": record.timestamp}
        return self.signer.verify(unsigned, record.signature)
