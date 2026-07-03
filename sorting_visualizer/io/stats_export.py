from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

FIELDNAMES = ["algorithm", "size", "fill", "comparisons", "writes", "time_ms"]


@dataclass(frozen=True)
class StatsRow:
    algorithm: str
    size: int
    fill: str
    comparisons: int
    writes: int
    time_ms: float


def export(path: str | Path, rows: list[StatsRow]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "algorithm": r.algorithm,
                    "size": r.size,
                    "fill": r.fill,
                    "comparisons": r.comparisons,
                    "writes": r.writes,
                    "time_ms": f"{r.time_ms:.1f}",
                }
            )
