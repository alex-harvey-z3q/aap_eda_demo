# EDA/AAP Request Routing

This project demonstrates a pattern for AI-assisted automation:

```text
ServiceNow/mock ticket
  -> Python OpenAI classifier
  -> classified event
  -> Event-Driven Ansible rulebook as governance gate
  -> AAP job template/workflow
```

The Python layer classifies and enriches the request. Event-Driven Ansible applies
deterministic policy. AAP executes the workflow that passes that policy.

```text
OpenAI/Python: "This looks like a restart request for foo in prod."
EDA rulebook:  "Prod restart requires approval, so do not run restart yet."
AAP:           "Run the approved automation."
```

## Architecture

```text
+------------------+      +----------------------+      +----------------------+
| Mock ticket JSON | ---> | Python classifier    | ---> | Classified EDA event |
| ServiceNow shape |      | OpenAI or rule       |      | intent/risk/context  |
+------------------+      +----------------------+      +----------+-----------+
                                                                 |
                                                                 v
+------------------+      +----------------------+      +----------------------+
| AAP workflow/job | <--- | EDA governance gate  | <--- | ansible-rulebook     |
| template launch  |      | approve/route/review |      | webhook + rules      |
+------------------+      +----------------------+      +----------------------+
```

| Layer | Local implementation |
| --- | --- |
| Mock ServiceNow ticket | [`samples/restart_service.json`](samples/restart_service.json) |
| OpenAI/rule classifier | [`eda_aap_demo/openai_classifier.py`](eda_aap_demo/openai_classifier.py), [`eda_aap_demo/classifiers.py`](eda_aap_demo/classifiers.py) |
| Classified event builder | [`eda_aap_demo/eda_event.py`](eda_aap_demo/eda_event.py) |
| EDA governance rulebook | [`rulebooks/route_operational_requests.yml`](rulebooks/route_operational_requests.yml) |
| AAP launch action | `run_job_template` actions in the rulebook |
| Legacy local simulation | [`eda_aap_demo/router.py`](eda_aap_demo/router.py), [`eda_aap_demo/workflows.py`](eda_aap_demo/workflows.py), [`eda_aap_demo/pipeline.py`](eda_aap_demo/pipeline.py) |

## EDA

EDA is the governance gate between AI classification and automation execution.
It owns the final decision:

- unknown intent -> manual review
- low classifier confidence -> manual review
- protected environment such as `prod` or `production` -> approval workflow
- urgent/high/critical priority -> approval workflow
- known low-risk request -> launch matching AAP job template

That keeps the AI service from becoming the authority that launches automation.
The classifier produces a signal; the rulebook enforces policy.

## Classified Event Contract

Example:

```json
{
  "schema_version": "aap_eda_poc.v1",
  "request_id": "REQ-0001",
  "source": "mock_ticket",
  "request_text": "Restart the foo service in the bar environment",
  "environment": "bar",
  "application": "foo",
  "requested_by": "test.user@example.com",
  "priority": "low",
  "intent": "restart_service",
  "action": "restart",
  "confidence": 0.95,
  "risk_signals": []
}
```

## Run Locally

Requires Python 3.10+.

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

For OpenAI classification, set an API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Run the original local-only simulation:

```bash
python -m eda_aap_demo samples/restart_service.json
```

For offline development, use the deterministic classifier:

```bash
python -m eda_aap_demo --classifier rule samples/restart_service.json
```

Emit the classified event that the EDA rulebook expects:

```bash
python -m eda_aap_demo --classifier rule --emit-eda-event samples/restart_service.json
```

## Run With Event-Driven Ansible

Install the EDA dependency:

```bash
make install-eda
```

Start the rulebook webhook listener. For real AAP execution, pass controller
connection details:

```bash
make run-eda CONTROLLER_ARGS="--controller-url https://controller.example.com --controller-token $AAP_TOKEN"
```

In another terminal, classify and POST the sample request into EDA:

```bash
python -m eda_aap_demo \
  --classifier rule \
  --post-eda-webhook http://127.0.0.1:5000/endpoint \
  samples/restart_service.json
```

The rulebook receives the POST body under `event.payload`, evaluates the
classified intent and governance fields, then chooses manual review, approval,
or direct AAP workflow launch.

The referenced AAP job templates must exist in the `Default` organization, and
they need Prompt on Launch for variables if they should receive the event fields
as extra vars.

## Project Layout

- `eda_aap_demo/cli.py` provides the command-line entry point.
- `eda_aap_demo/openai_classifier.py` uses OpenAI structured output for intent classification.
- `eda_aap_demo/classifiers.py` provides the deterministic rule classifier.
- `eda_aap_demo/eda_event.py` builds and posts EDA event payloads.
- `rulebooks/route_operational_requests.yml` contains the real EDA governance rules.
- `samples/` contains mock ticket and classified event examples.
- `tests/` covers classification, routing, and the EDA event contract.

## Quality Gates

Install development dependencies:

```bash
make install-dev
```

Run all local checks:

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

## Mocks

External systems and infrastructure actions are not called by default:

- The ticket source is local JSON, not ServiceNow.
- OpenAI classifies intent but does not choose the final workflow in the EDA path.
- The deterministic classifier is available with `--classifier rule`.
- The EDA rulebook owns manual-review, approval, and workflow-routing policy.
- The rulebook only launches real AAP templates when run with controller credentials.
- No inventory, playbooks, job templates, or infrastructure actions are included in this repo.

## Production Considerations

For a production implementation, you would add:

- a real event source such as ServiceNow webhooks or integration middleware
- authentication, authorization, audit logging, and approval gates
- tested EDA rulebooks and event schemas
- AAP workflow/job template integration using supported controller APIs
- inventory scoping, RBAC, credential management, and environment guardrails
- classifier evaluation, prompt/version governance, and fallback paths
- observability, retries, idempotency controls, and incident traceability
