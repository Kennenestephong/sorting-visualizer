from __future__ import annotations

import datetime
import os
import re
from pathlib import Path

from ..io.array_store import LoadedArray
from ..io.array_store import load as _load_array
from ..io.array_store import save as _save_array
from ..io.stats_export import StatsRow
from ..io.stats_export import export as _export_stats

_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class InvalidName(Exception):
    """Raised when a stored-array name is not a safe slug."""


def data_dir() -> Path:
    return Path(os.environ.get("SV_DATA_DIR", "data"))


def arrays_dir() -> Path:
    d = data_dir() / "arrays"
    d.mkdir(parents=True, exist_ok=True)
    return d


def exports_dir() -> Path:
    d = data_dir() / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _validate(name: str) -> None:
    if not _NAME_RE.match(name):
        raise InvalidName(f"invalid name: {name!r}")


def list_arrays() -> list[str]:
    return sorted(p.stem for p in arrays_dir().glob("*.json"))


def save_array(name: str, data: list[int], fill: str) -> None:
    _validate(name)
    _save_array(arrays_dir() / f"{name}.json", data, fill)


def load_array(name: str) -> LoadedArray:
    _validate(name)
    return _load_array(arrays_dir() / f"{name}.json")


def export_stats(rows: list[StatsRow]) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = exports_dir() / f"stats-{ts}.csv"
    _export_stats(path, rows)
    return path
