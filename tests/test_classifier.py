import unittest

from eda_aap_demo.classifiers import RuleBasedClassifier
from eda_aap_demo.models import OperationalRequest


def make_request(request_text: str, priority: str = "low", environment: str = "bar"):
    return OperationalRequest(
        request_id="REQ-TEST",
        source="mock_ticket",
        request_text=request_text,
        environment=environment,
        application="foo",
        requested_by="test.user@example.com",
        priority=priority,
    )


class RuleBasedClassifierTests(unittest.TestCase):
    def setUp(self):
        self.classifier = RuleBasedClassifier()

    def test_classifies_restart_service(self):
        result = self.classifier.classify(make_request("Restart the foo service"))

        self.assertEqual(result.intent, "restart_service")
        self.assertEqual(result.action, "restart")
        self.assertEqual(result.target_workflow, "aap_restart_service")
        self.assertGreaterEqual(result.confidence, 0.9)
        self.assertFalse(result.requires_approval)

    def test_classifies_status_check(self):
        result = self.classifier.classify(make_request("Check service status for foo"))

        self.assertEqual(result.intent, "check_service_status")
        self.assertEqual(result.target_workflow, "aap_check_service_status")

    def test_classifies_log_collection(self):
        result = self.classifier.classify(make_request("Please collect logs for foo"))

        self.assertEqual(result.intent, "collect_logs")
        self.assertEqual(result.target_workflow, "aap_collect_logs")

    def test_classifies_health_check(self):
        result = self.classifier.classify(make_request("Run a health check for foo"))

        self.assertEqual(result.intent, "run_health_check")
        self.assertEqual(result.target_workflow, "aap_run_health_check")

    def test_unknown_request_requires_review(self):
        result = self.classifier.classify(make_request("Please make foo faster"))

        self.assertEqual(result.intent, "unknown_request")
        self.assertEqual(result.action, "unknown")
        self.assertIsNone(result.target_workflow)
        self.assertTrue(result.requires_approval)

    def test_production_requests_require_approval(self):
        result = self.classifier.classify(
            make_request("Restart the foo service", environment="production")
        )

        self.assertEqual(result.intent, "restart_service")
        self.assertTrue(result.requires_approval)


if __name__ == "__main__":
    unittest.main()
