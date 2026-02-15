# AI-Assisted EDA/AAP Routing Demo

Small proof-of-concept project that demonstrates AI-assisted routing of mock operational requests into Event-Driven Ansible/AAP-style workflows.

This is a local, safe, synthetic demo. It does not integrate with ServiceNow, real Ansible Automation Platform, real Event-Driven Ansible, or real infrastructure.

## Architecture

```text
+------------------+      +----------------------+      +----------------------+
| Mock ticket JSON | ---> | Request classifier   | ---> | Structured intent    |
|                  |      | rule or OpenAI       |      | intent/action/etc.   |
+------------------+      +----------------------+      +----------+-----------+
                                                                 |
                                                                 v
+------------------+      +----------------------+      +----------------------+
| JSON result      | <--- | Mock AAP workflow    | <--- | EDA-style router     |
| status + steps   |      | simulated handlers   |      | workflow selection   |
+------------------+      +----------------------+      +----------------------+
```

The code is intentionally small and interview-demo friendly:

- `eda_aap_demo/classifiers.py` contains the classifier abstraction and deterministic rule-based classifier.
- `eda_aap_demo/openai_classifier.py` contains an optional OpenAI-backed classifier.
- `eda_aap_demo/router.py` contains EDA-style routing rules.
- `eda_aap_demo/workflows.py` contains mock AAP workflow handlers.
- `eda_aap_demo/pipeline.py` wires the flow together.
- `eda_aap_demo/cli.py` provides the command-line entry point.
- `tests/` covers classification and routing behavior.

## Conceptual Mapping

In a real platform, a ServiceNow ticket or service request could emit an event containing request details. Event-Driven Ansible would evaluate rulebooks against that event, select an automation target, and invoke an AAP job template or workflow.

This demo maps those ideas as follows:

| Real-world concept | Demo component |
| --- | --- |
| ServiceNow ticket | Mock JSON payload |
| AI/NLP request understanding | Rule-based or OpenAI-backed classifier |
| Structured operational intent | `ClassifiedIntent` |
| EDA rulebook routing | `EdaRouter` |
| AAP workflow/job template | Mock workflow handlers |
| Job output | JSON result printed by CLI |

## Run The Demo

Requires Python 3.10+.

Run locally with the default deterministic classifier:

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

## Run With OpenAI Classification

Install the optional dependency:

```bash
python -m pip install -r requirements.txt
```

Set your API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Run the same payload through the OpenAI-backed classifier:

```bash
python -m eda_aap_demo --classifier openai samples/restart_service.json
```

The default OpenAI model is `gpt-5-mini`. Override it with either:

```bash
OPENAI_MODEL=gpt-5.2 python -m eda_aap_demo --classifier openai samples/restart_service.json
```

or:

```bash
python -m eda_aap_demo --classifier openai --model gpt-5.2 samples/restart_service.json
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

## What Is Mocked

Everything operational is mocked:

- Ticket source is local JSON, not ServiceNow.
- Default classification is deterministic keyword matching.
- OpenAI classification is optional and only runs when `--classifier openai` is selected.
- EDA routing is plain Python rules, not a live EDA rulebook.
- AAP workflow execution only returns simulated steps.
- No inventory, playbooks, job templates, or infrastructure actions are used.

## Productionisation Considerations

To turn this concept into a production design, you would need:

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

The OpenAI classifier still only routes into mocked workflows. It does not call ServiceNow, EDA, AAP, or infrastructure.
