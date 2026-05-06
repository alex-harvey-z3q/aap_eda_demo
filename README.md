# EDA/AAP Request Routing

A local Python project for routing operational request payloads into Event-Driven Ansible/AAP-style workflows.

## Architecture

```text
+------------------+      +----------------------+      +----------------------+
| Mock ticket JSON | ---> | Request classifier   | ---> | Structured intent    |
|                  |      | OpenAI classifier    |      | intent/action        |
+------------------+      +----------------------+      +----------+-----------+
                                                                 |
                                                                 v
+------------------+      +----------------------+      +----------------------+
| JSON result      | <--- | Mock AAP workflow    | <--- | EDA-style router     |
| status + steps   |      | simulated handlers   |      | workflow selection   |
+------------------+      +----------------------+      +----------------------+
```

Project layout:

- `eda_aap_demo/classifiers.py` contains the classifier abstraction and deterministic rule-based fallback.
- `eda_aap_demo/openai_classifier.py` contains the OpenAI-backed classifier used by the CLI.
- `eda_aap_demo/router.py` contains EDA-style routing rules.
- `eda_aap_demo/workflows.py` contains mock AAP workflow handlers.
- `eda_aap_demo/pipeline.py` wires the flow together.
- `eda_aap_demo/cli.py` provides the command-line entry point.
- `tests/` covers classification and routing behavior.

## Platform Mapping

In a platform implementation, a ServiceNow ticket or service request can emit an event containing request details. Event-Driven Ansible evaluates rulebooks against that event, selects an automation target, and invokes an AAP job template or workflow.

This project uses the following local equivalents:

| Real-world concept | Local component |
| --- | --- |
| ServiceNow ticket | Mock JSON payload |
| Request classification | OpenAI-backed classifier |
| Structured operational intent | `ClassifiedIntent` |
| EDA rulebook routing | `EdaRouter` |
| AAP workflow/job template | Mock workflow handlers |
| Job output | JSON result printed by CLI |

## Run Locally

Requires Python 3.10+.

Install dependencies and set an OpenAI API key:

```bash
python -m pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
```

Run with the included sample payload:

```bash
python -m eda_aap_demo samples/restart_service.json
```

Or pipe JSON via stdin:

```bash
printf '%s\n' '{
  "request_id": "REQ-0001",
  "source": "mock_ticket",
  "request_text": "Restart the foo service in the bar environment",
  "environment": "bar",
  "application": "foo",
  "requested_by": "test.user@example.com",
  "priority": "low"
}' | python -m eda_aap_demo
```

## Model Selection

The default OpenAI model is `gpt-5-mini`. Override it with either:

```bash
OPENAI_MODEL=gpt-5.2 python -m eda_aap_demo samples/restart_service.json
```

or:

```bash
python -m eda_aap_demo --model gpt-5.2 samples/restart_service.json
```

For offline development, the deterministic classifier can still be selected explicitly:

```bash
python -m eda_aap_demo --classifier rule samples/restart_service.json
```

Example output:

```json
{
  "request_id": "REQ-0001",
  "classified_intent": "restart_service",
  "confidence": 0.95,
  "requires_approval": false,
  "selected_workflow": "aap_restart_service",
  "simulated_workflow_steps": [
    "Validate application 'foo' in environment 'bar'",
    "Check mock maintenance window",
    "Simulate restarting service",
    "Simulate post-restart status check"
  ],
  "final_status": "completed"
}
```

## Run Tests

```bash
python -m unittest discover
```

## Quality Gates

Install development dependencies:

```bash
make install-dev
```

Run all local quality gates:

```bash
make quality
```

Useful individual targets:

```bash
make format
make lint
make typecheck
make security
make test
```

## Local Boundaries

External systems and infrastructure actions are not called:

- Ticket source is local JSON, not ServiceNow.
- Request classification uses OpenAI by default.
- The deterministic rule classifier is available for offline development with `--classifier rule`.
- EDA routing is plain Python rules, not a live EDA rulebook.
- AAP workflow execution only returns simulated steps.
- No inventory, playbooks, job templates, or infrastructure actions are used.

## Production Considerations

For a production implementation, add:

- A real event source such as ServiceNow webhooks or an integration middleware.
- Authentication, authorization, audit logging, and approval gates.
- An EDA deployment with tested rulebooks and event schemas.
- AAP workflow/job template integration using supported APIs.
- Inventory scoping, RBAC, credential management, and environment guardrails.
- Robust intent extraction with validation, fallback paths, model evaluation, and prompt/version governance.
- Human-in-the-loop review for high-risk or low-confidence requests.
- Observability, retries, idempotency controls, and incident traceability.

## OpenAI Classifier

`RequestClassifier` is the shared interface for both classifier implementations. `OpenAIClassifier` uses the OpenAI Responses API with Structured Outputs so the model response is constrained to the same structured intent fields used by the rest of the pipeline.

The OpenAI classifier only selects structured intent for the local workflow router. It does not call ServiceNow, EDA, AAP, or infrastructure.
