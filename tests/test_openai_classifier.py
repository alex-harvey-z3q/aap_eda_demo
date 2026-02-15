import json
import unittest

from eda_aap_demo.models import OperationalRequest
from eda_aap_demo.openai_classifier import OpenAIClassifier


class FakeResponses:
    def __init__(self, output):
        self.output = output
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return type("FakeResponse", (), {"output_text": json.dumps(self.output)})()


class FakeClient:
    def __init__(self, output):
        self.responses = FakeResponses(output)


def make_request():
    return OperationalRequest(
        request_id="REQ-TEST",
        source="mock_ticket",
        request_text="Restart the foo service in the bar environment",
        environment="bar",
        application="foo",
        requested_by="test.user@example.com",
        priority="low",
    )


class OpenAIClassifierTests(unittest.TestCase):
    def test_maps_structured_response_to_classified_intent(self):
        client = FakeClient(
            {
                "intent": "restart_service",
                "action": "restart",
                "confidence": 0.93,
                "requires_approval": False,
                "target_workflow": "aap_restart_service",
            }
        )

        result = OpenAIClassifier(client=client).classify(make_request())

        self.assertEqual(result.intent, "restart_service")
        self.assertEqual(result.action, "restart")
        self.assertEqual(result.confidence, 0.93)
        self.assertEqual(result.target_workflow, "aap_restart_service")
        self.assertFalse(result.requires_approval)

    def test_normalizes_workflow_from_classified_intent(self):
        client = FakeClient(
            {
                "intent": "restart_service",
                "action": "restart",
                "confidence": 0.93,
                "requires_approval": False,
                "target_workflow": "aap_collect_logs",
            }
        )

        result = OpenAIClassifier(client=client).classify(make_request())

        self.assertEqual(result.intent, "restart_service")
        self.assertEqual(result.target_workflow, "aap_restart_service")

    def test_uses_responses_api_with_json_schema(self):
        client = FakeClient(
            {
                "intent": "restart_service",
                "action": "restart",
                "confidence": 0.93,
                "requires_approval": False,
                "target_workflow": "aap_restart_service",
            }
        )

        OpenAIClassifier(model="test-model", client=client).classify(make_request())

        request = client.responses.last_request
        self.assertEqual(request["model"], "test-model")
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertTrue(request["text"]["format"]["strict"])


if __name__ == "__main__":
    unittest.main()
