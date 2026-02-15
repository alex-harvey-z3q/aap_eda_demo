from __future__ import annotations

import json
import os
from typing import Any, cast

from eda_aap_demo.classifiers import RequestClassifier, RuleBasedClassifier
from eda_aap_demo.models import ClassifiedIntent, IntentName, OperationalRequest

WORKFLOW_BY_INTENT: dict[str, str] = {
    "restart_service": "aap_restart_service",
    "check_service_status": "aap_check_service_status",
    "collect_logs": "aap_collect_logs",
    "run_health_check": "aap_run_health_check",
}


INTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "restart_service",
                "check_service_status",
                "collect_logs",
                "run_health_check",
                "unknown_request",
            ],
        },
        "action": {
            "type": "string",
            "enum": [
                "restart",
                "check_status",
                "collect_logs",
                "run_health_check",
                "unknown",
            ],
        },
        "confidence": {
            "type": "number",
        },
        "requires_approval": {
            "type": "boolean",
        },
        "target_workflow": {
            "type": ["string", "null"],
            "enum": [
                "aap_restart_service",
                "aap_check_service_status",
                "aap_collect_logs",
                "aap_run_health_check",
                None,
            ],
        },
    },
    "required": [
        "intent",
        "action",
        "confidence",
        "requires_approval",
        "target_workflow",
    ],
    "additionalProperties": False,
}


class OpenAIClassifier(RequestClassifier):
    """OpenAI-backed classifier using the Responses API with structured JSON output."""

    def __init__(
        self,
        model: str | None = None,
        client: Any | None = None,
        fallback: RequestClassifier | None = None,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.client = client or self._build_client()
        self.fallback = fallback or RuleBasedClassifier()

    def classify(self, request: OperationalRequest) -> ClassifiedIntent:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Classify a mock operational request for synthetic EDA/AAP routing. "
                        "Return only the structured fields. Choose unknown_request when the "
                        "request does not clearly match a supported operational intent. "
                        "Require approval for production/prod environments, high/critical/urgent "
                        "priority, unknown requests, or ambiguous requests."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request_text": request.request_text,
                            "environment": request.environment,
                            "application": request.application,
                            "priority": request.priority,
                        }
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "operational_intent",
                    "strict": True,
                    "schema": INTENT_SCHEMA,
                }
            },
        )

        data = json.loads(response.output_text)
        return self._to_classified_intent(request, data)

    @staticmethod
    def _build_client() -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI classifier requires the 'openai' package. "
                "Install it with: python -m pip install -r requirements.txt"
            ) from exc
        return OpenAI()

    def _to_classified_intent(
        self, request: OperationalRequest, data: dict[str, Any]
    ) -> ClassifiedIntent:
        fallback_result = self.fallback.classify(request)
        intent = self._valid_intent(data.get("intent"))
        if intent == "unknown_request":
            target_workflow = None
        else:
            target_workflow = WORKFLOW_BY_INTENT.get(intent, fallback_result.target_workflow)

        return ClassifiedIntent(
            intent=intent,
            application=request.application,
            environment=request.environment,
            action=str(data.get("action") or fallback_result.action),
            confidence=self._clamp_confidence(data.get("confidence")),
            requires_approval=bool(
                data.get("requires_approval") or fallback_result.requires_approval
            ),
            target_workflow=target_workflow,
        )

    @staticmethod
    def _valid_intent(value: Any) -> IntentName:
        valid_intents = {
            "restart_service",
            "check_service_status",
            "collect_logs",
            "run_health_check",
            "unknown_request",
        }
        if value in valid_intents:
            return cast(IntentName, value)
        return "unknown_request"

    @staticmethod
    def _clamp_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.2
        return max(0.0, min(1.0, confidence))
