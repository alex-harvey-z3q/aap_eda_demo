import unittest

from eda_aap_demo.eda_event import EDA_EVENT_SCHEMA_VERSION, build_eda_event, post_eda_event


class EdaEventTests(unittest.TestCase):
    def test_builds_classified_event_for_rulebook_webhook(self):
        event = build_eda_event(
            {
                "request_id": "REQ-0001",
                "source": "mock_ticket",
                "request_text": "Restart the foo service in the bar environment",
                "environment": "bar",
                "application": "foo",
                "requested_by": "test.user@example.com",
                "priority": "low",
            }
        )

        self.assertEqual(event["schema_version"], EDA_EVENT_SCHEMA_VERSION)
        self.assertEqual(event["request_id"], "REQ-0001")
        self.assertEqual(event["intent"], "restart_service")
        self.assertEqual(event["action"], "restart")
        self.assertEqual(event["risk_signals"], [])
        self.assertNotIn("target_workflow", event)
        self.assertNotIn("requires_approval", event)

    def test_event_marks_production_as_risk_signal_without_deciding_approval(self):
        event = build_eda_event(
            {
                "request_id": "REQ-0002",
                "source": "mock_ticket",
                "request_text": "Restart the foo service",
                "environment": "production",
                "application": "foo",
                "requested_by": "test.user@example.com",
                "priority": "low",
            }
        )

        self.assertEqual(event["intent"], "restart_service")
        self.assertEqual(event["risk_signals"], ["protected_environment"])
        self.assertNotIn("requires_approval", event)

    def test_event_marks_high_priority_as_risk_signal(self):
        event = build_eda_event(
            {
                "request_id": "REQ-0003",
                "source": "mock_ticket",
                "request_text": "Collect logs for foo",
                "environment": "bar",
                "application": "foo",
                "requested_by": "test.user@example.com",
                "priority": "urgent",
            }
        )

        self.assertEqual(event["intent"], "collect_logs")
        self.assertEqual(event["risk_signals"], ["high_priority"])

    def test_post_event_rejects_non_http_webhook_urls(self):
        with self.assertRaisesRegex(ValueError, "http or https"):
            post_eda_event({}, "file:///tmp/event.json")


if __name__ == "__main__":
    unittest.main()
