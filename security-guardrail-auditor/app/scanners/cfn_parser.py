from __future__ import annotations

import json
from typing import Any

import yaml


def parse_cfn_string(source: str, filename: str = "template.yaml") -> dict[str, Any]:
    """Parse CloudFormation JSON or YAML from a string."""
    if filename.lower().endswith(".json"):
        data = json.loads(source)
    else:
        data = yaml.safe_load(source)
    if not isinstance(data, dict):
        raise ValueError(f"CloudFormation template must be an object: {filename}")
    return data
