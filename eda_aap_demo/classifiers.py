from __future__ import annotations

from abc import ABC, abstractmethod

from eda_aap_demo.models import ClassifiedIntent, IntentName, OperationalRequest


class RequestClassifier(ABC):
    """Classifier interface for deterministic or future LLM-backed classifiers."""

    @abstractmethod
    def classify(self, request: OperationalRequest) -> ClassifiedIntent:
        raise NotImplementedError


class RuleBasedClassifier(RequestClassifier):
    """Simple deterministic classifier suitable for local demos and unit tests."""

    _INTENT_RULES: tuple[tuple[IntentName, str, tuple[str, ...], float], ...] = (
        ("restart_service", "restart", ("restart", "reboot", "bounce"), 0.95),
        (
            "check_service_status",
            "check_status",
            ("status", "is running", "check service", "service health"),
            0.9,
        ),
        (
            "collect_logs",
            "collect_logs",
            ("collect logs", "logs", "log bundle", "diagnostics"),
            0.88,
        ),
        (
            "run_health_check",
            "run_health_check",
            ("health check", "smoke test", "validate health", "run checks"),
            0.9,
        ),
    )

    def classify(self, request: OperationalRequest) -> ClassifiedIntent:
        text = request.request_text.lower()

        for intent, action, keywords, confidence in self._INTENT_RULES:
            if any(keyword in text for keyword in keywords):
                return ClassifiedIntent(
                    intent=intent,
                    application=request.application,
                    environment=request.environment,
                    action=action,
                    confidence=confidence,
                    requires_approval=self._requires_approval(request),
                    target_workflow=self._workflow_for_intent(intent),
                )

        return ClassifiedIntent(
            intent="unknown_request",
            application=request.application,
            environment=request.environment,
            action="unknown",
            confidence=0.2,
            requires_approval=True,
            target_workflow=None,
        )

    @staticmethod
    def _requires_approval(request: OperationalRequest) -> bool:
        high_risk_priorities = {"high", "critical", "urgent"}
        protected_environments = {"prod", "production"}
        return (
            request.priority in high_risk_priorities
            or request.environment.lower() in protected_environments
        )

    @staticmethod
    def _workflow_for_intent(intent: IntentName) -> str | None:
        workflows = {
            "restart_service": "aap_restart_service",
            "check_service_status": "aap_check_service_status",
            "collect_logs": "aap_collect_logs",
            "run_health_check": "aap_run_health_check",
        }
        return workflows.get(intent)
