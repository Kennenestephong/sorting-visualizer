from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MIN_SIZE = 10
MAX_SIZE = 200


class ArrayLoadError(Exception):
    """Raised when an array file cannot be loaded or is invalid."""


@dataclass(frozen=True)
class LoadedArray:
    data: list[int]
    fill: str


def save(path: str | Path, array: list[int], fill: str) -> None:
    payload = {"version": 1, "size": len(array), "fill": fill, "data": list(array)}
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load(path: str | Path) -> LoadedArray:
    p = Path(path)
    if not p.exists():
        raise ArrayLoadError(f"File not found: {p}")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ArrayLoadError(f"Invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or "data" not in payload:
        raise ArrayLoadError("Missing 'data' field")
    data = payload["data"]
    if not isinstance(data, list) or not all(
        isinstance(x, int) and not isinstance(x, bool) for x in data
    ):
        raise ArrayLoadError("'data' must be a list of integers")
    if not (MIN_SIZE <= len(data) <= MAX_SIZE):
        raise ArrayLoadError(f"Size must be between {MIN_SIZE} and {MAX_SIZE}")
    return LoadedArray(data=list(data), fill=str(payload.get("fill", "custom")))
