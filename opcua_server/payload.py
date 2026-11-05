import json
from typing import Any, Dict


def parse_payload(val: Any) -> Dict[str, Any]:
    """Return the gateway's JSON payload as a dict, or {} for any other value."""
    try:
        parsed = json.loads(val)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
