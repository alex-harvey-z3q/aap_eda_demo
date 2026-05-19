from __future__ import annotations

import json
from typing import Any
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from eda_aap_demo.classifiers import RequestClassifier, RuleBasedClassifier
from eda_aap_demo.models import OperationalRequest

EDA_EVENT_SCHEMA_VERSION = "aap_eda_poc.v1"


def build_eda_event(
    payload: dict[str, Any],
    classifier: RequestClassifier | None = None,
) -> dict[str, Any]:
    request = OperationalRequest.from_dict(payload)
    classifier = classifier or RuleBasedClassifier()
    classified = classifier.classify(request)

    return {
        "schema_version": EDA_EVENT_SCHEMA_VERSION,
        "request_id": request.request_id,
        "source": request.source,
        "request_text": request.request_text,
        "environment": request.environment,
        "application": request.application,
        "requested_by": request.requested_by,
        "priority": request.priority,
        "intent": classified.intent,
        "action": classified.action,
        "confidence": classified.confidence,
        "risk_signals": _risk_signals(request, classified.confidence),
    }


def _risk_signals(request: OperationalRequest, confidence: float) -> list[str]:
    signals = []
    if request.environment.lower() in {"prod", "production"}:
        signals.append("protected_environment")
    if request.priority in {"high", "critical", "urgent"}:
        signals.append("high_priority")
    if confidence < 0.85:
        signals.append("low_confidence")
    return signals


def post_eda_event(event: dict[str, Any], webhook_url: str) -> int:
    parsed_url = urllib_parse.urlparse(webhook_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("EDA webhook URL must use http or https")

    body = json.dumps(event).encode("utf-8")
    request = urllib_request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib_request.urlopen(request, timeout=10) as response:  # nosec B310
        return int(response.status)
