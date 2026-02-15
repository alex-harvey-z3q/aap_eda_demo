from __future__ import annotations

from eda_aap_demo.models import ClassifiedIntent, RouteDecision


class EdaRouter:
    """Mock EDA-style routing rules for classified operational intents."""

    def route(self, classified: ClassifiedIntent) -> RouteDecision:
        if classified.intent == "unknown_request":
            return RouteDecision(
                selected_workflow="manual_review",
                reason="Unknown or unsupported request intent",
            )

        if classified.requires_approval:
            return RouteDecision(
                selected_workflow="approval_required",
                reason="Request matched automation intent but requires approval",
            )

        if not classified.target_workflow:
            return RouteDecision(
                selected_workflow="manual_review",
                reason="No workflow mapped for classified intent",
            )

        return RouteDecision(
            selected_workflow=classified.target_workflow,
            reason=f"Intent '{classified.intent}' matched EDA routing rule",
        )
