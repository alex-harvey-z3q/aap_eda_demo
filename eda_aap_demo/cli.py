from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from eda_aap_demo.classifiers import RequestClassifier, RuleBasedClassifier
from eda_aap_demo.eda_event import build_eda_event, post_eda_event
from eda_aap_demo.openai_classifier import OpenAIClassifier
from eda_aap_demo.pipeline import process_request


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Route a mock operational request through synthetic EDA/AAP workflow logic."
    )
    parser.add_argument(
        "payload",
        nargs="?",
        help="Path to a JSON request payload. Reads from stdin when omitted.",
    )
    parser.add_argument(
        "--classifier",
        choices=("rule", "openai"),
        default=os.getenv("AAP_EDA_CLASSIFIER", "openai"),
        help="Classifier implementation to use. Defaults to AAP_EDA_CLASSIFIER or 'openai'.",
    )
    parser.add_argument(
        "--emit-eda-event",
        action="store_true",
        help="Classify the request and print the event payload expected by the EDA rulebook.",
    )
    parser.add_argument(
        "--post-eda-webhook",
        help="Classify the request and POST the EDA event to an ansible-rulebook webhook URL.",
    )
    args = parser.parse_args(argv)

    try:
        payload = _load_payload(args.payload)
        classifier = _build_classifier(args.classifier)
        if args.emit_eda_event or args.post_eda_webhook:
            event = build_eda_event(payload, classifier=classifier)
            if args.post_eda_webhook:
                status_code = post_eda_event(event, args.post_eda_webhook)
                result = {
                    "status": "posted",
                    "status_code": status_code,
                    "webhook_url": args.post_eda_webhook,
                    "event": event,
                }
            else:
                result = event
        else:
            result = process_request(payload, classifier=classifier)
    except (OSError, RuntimeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


def _load_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()

    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    return payload


def _build_classifier(name: str) -> RequestClassifier:
    if name == "openai":
        return OpenAIClassifier()
    return RuleBasedClassifier()
