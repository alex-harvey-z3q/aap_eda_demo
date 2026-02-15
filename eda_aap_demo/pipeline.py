from __future__ import annotations

from typing import Any

from eda_aap_demo.classifiers import RequestClassifier, RuleBasedClassifier
from eda_aap_demo.models import OperationalRequest
from eda_aap_demo.router import EdaRouter
from eda_aap_demo.workflows import MockAapExecutor


def process_request(
    payload: dict[str, Any],
    classifier: RequestClassifier | None = None,
    router: EdaRouter | None = None,
    executor: MockAapExecutor | None = None,
) -> dict[str, Any]:
    request = OperationalRequest.from_dict(payload)
    classifier = classifier or RuleBasedClassifier()
    router = router or EdaRouter()
    executor = executor or MockAapExecutor()

    classified = classifier.classify(request)
    route = router.route(classified)
    workflow_result = executor.execute(route.selected_workflow, classified)

    return {
        "request_id": request.request_id,
        "classified_intent": classified.intent,
        "application": classified.application,
        "environment": classified.environment,
        "action": classified.action,
        "confidence": classified.confidence,
        "requires_approval": classified.requires_approval,
        "selected_workflow": route.selected_workflow,
        "routing_reason": route.reason,
        "simulated_workflow_steps": workflow_result.steps,
        "final_status": workflow_result.status,
    }
