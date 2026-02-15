from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

IntentName = Literal[
    "restart_service",
    "check_service_status",
    "collect_logs",
    "run_health_check",
    "unknown_request",
]


@dataclass(frozen=True)
class OperationalRequest:
    request_id: str
    source: str
    request_text: str
    environment: str
    application: str
    requested_by: str
    priority: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OperationalRequest:
        required_fields = [
            "request_id",
            "source",
            "request_text",
            "environment",
            "application",
            "requested_by",
            "priority",
        ]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")

        return cls(
            request_id=str(payload["request_id"]),
            source=str(payload["source"]),
            request_text=str(payload["request_text"]),
            environment=str(payload["environment"]),
            application=str(payload["application"]),
            requested_by=str(payload["requested_by"]),
            priority=str(payload["priority"]).lower(),
        )


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: IntentName
    application: str
    environment: str
    action: str
    confidence: float
    requires_approval: bool
    target_workflow: str | None


@dataclass(frozen=True)
class RouteDecision:
    selected_workflow: str
    reason: str


@dataclass(frozen=True)
class WorkflowResult:
    workflow_name: str
    steps: list[str]
    status: str
