from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from eda_aap_demo.classifiers import RequestClassifier, RuleBasedClassifier
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
    args = parser.parse_args(argv)

    try:
        payload = _load_payload(args.payload)
        classifier = _build_classifier(args.classifier)
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
