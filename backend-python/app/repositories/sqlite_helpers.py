from datetime import datetime
from enum import Enum
import json
from typing import Any


def enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def datetime_value(value: datetime) -> str:
    return value.isoformat()


def json_value(value: dict[str, Any] | list[Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def json_object(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return json.loads(value)


def json_array(value: str) -> list[float]:
    loaded = json.loads(value)
    return [float(item) for item in loaded]

