from __future__ import annotations

from ..core.events import Compare, Event, MarkSorted, Overwrite, Swap
from ..core.runner import Recording


def event_to_dict(event: Event) -> dict:
    if isinstance(event, Compare):
        return {"type": "compare", "i": event.i, "j": event.j}
    if isinstance(event, Swap):
        return {"type": "swap", "i": event.i, "j": event.j}
    if isinstance(event, Overwrite):
        return {"type": "overwrite", "i": event.i, "value": event.value, "old": event.old}
    if isinstance(event, MarkSorted):
        return {"type": "marksorted", "i": event.i}
    raise TypeError(f"unknown event type: {event!r}")


def event_from_dict(d: dict) -> Event:
    t = d["type"]
    if t == "compare":
        return Compare(d["i"], d["j"])
    if t == "swap":
        return Swap(d["i"], d["j"])
    if t == "overwrite":
        return Overwrite(d["i"], d["value"], d["old"])
    if t == "marksorted":
        return MarkSorted(d["i"])
    raise ValueError(f"unknown event dict type: {t!r}")


def recording_to_dict(rec: Recording) -> dict:
    return {
        "initial": list(rec.initial),
        "events": [event_to_dict(e) for e in rec.events],
        "stats": {"comparisons": rec.stats.comparisons, "writes": rec.stats.writes},
        "elapsed_ms": rec.elapsed_ms,
    }
