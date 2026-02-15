from __future__ import annotations

from collections.abc import Callable

from eda_aap_demo.models import ClassifiedIntent, WorkflowResult

WorkflowHandler = Callable[[ClassifiedIntent], WorkflowResult]


def aap_restart_service(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="aap_restart_service",
        steps=[
            f"Validate application '{intent.application}' in environment '{intent.environment}'",
            "Check mock maintenance window",
            "Simulate restarting service",
            "Simulate post-restart status check",
        ],
        status="completed",
    )


def aap_check_service_status(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="aap_check_service_status",
        steps=[
            f"Validate service target for '{intent.application}'",
            f"Simulate status check in '{intent.environment}'",
            "Return mock service status",
        ],
        status="completed",
    )


def aap_collect_logs(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="aap_collect_logs",
        steps=[
            f"Validate log source for '{intent.application}'",
            f"Simulate collecting logs from '{intent.environment}'",
            "Package mock log bundle",
        ],
        status="completed",
    )


def aap_run_health_check(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="aap_run_health_check",
        steps=[
            f"Validate health-check profile for '{intent.application}'",
            f"Simulate health checks in '{intent.environment}'",
            "Return mock health summary",
        ],
        status="completed",
    )


def manual_review(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="manual_review",
        steps=[
            "Flag request for human review",
            "Do not run automation",
        ],
        status="manual_review_required",
    )


def approval_required(intent: ClassifiedIntent) -> WorkflowResult:
    return WorkflowResult(
        workflow_name="approval_required",
        steps=[
            "Create mock approval task",
            "Pause before automation",
        ],
        status="approval_required",
    )


WORKFLOW_REGISTRY: dict[str, WorkflowHandler] = {
    "aap_restart_service": aap_restart_service,
    "aap_check_service_status": aap_check_service_status,
    "aap_collect_logs": aap_collect_logs,
    "aap_run_health_check": aap_run_health_check,
    "manual_review": manual_review,
    "approval_required": approval_required,
}


class MockAapExecutor:
    """Executes mock workflow handlers by name."""

    def __init__(self, registry: dict[str, WorkflowHandler] | None = None) -> None:
        self._registry = registry or WORKFLOW_REGISTRY

    def execute(self, workflow_name: str, intent: ClassifiedIntent) -> WorkflowResult:
        handler = self._registry.get(workflow_name)
        if not handler:
            return WorkflowResult(
                workflow_name=workflow_name,
                steps=[f"No mock handler registered for '{workflow_name}'"],
                status="failed",
            )
        return handler(intent)
