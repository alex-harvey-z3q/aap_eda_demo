import unittest

from eda_aap_demo.models import ClassifiedIntent
from eda_aap_demo.router import EdaRouter


def make_intent(
    intent="restart_service",
    requires_approval=False,
    target_workflow="aap_restart_service",
):
    return ClassifiedIntent(
        intent=intent,
        application="foo",
        environment="bar",
        action="restart",
        confidence=0.95,
        requires_approval=requires_approval,
        target_workflow=target_workflow,
    )


class EdaRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = EdaRouter()

    def test_routes_known_intent_to_target_workflow(self):
        route = self.router.route(make_intent())

        self.assertEqual(route.selected_workflow, "aap_restart_service")
        self.assertIn("matched EDA routing rule", route.reason)

    def test_routes_unknown_intent_to_manual_review(self):
        route = self.router.route(
            make_intent(
                intent="unknown_request",
                target_workflow=None,
            )
        )

        self.assertEqual(route.selected_workflow, "manual_review")

    def test_routes_approval_required_before_workflow(self):
        route = self.router.route(make_intent(requires_approval=True))

        self.assertEqual(route.selected_workflow, "approval_required")

    def test_routes_missing_workflow_to_manual_review(self):
        route = self.router.route(make_intent(target_workflow=None))

        self.assertEqual(route.selected_workflow, "manual_review")


if __name__ == "__main__":
    unittest.main()
