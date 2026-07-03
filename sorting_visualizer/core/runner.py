from __future__ import annotations

import time
from dataclasses import dataclass, field

from .algorithms import Algorithm
from .events import Compare, Event, MarkSorted, Overwrite, Swap
from .stats import Stats, compute


@dataclass
class State:
    data: list[int]
    sorted_idx: set[int] = field(default_factory=set)
    highlight: tuple[int, ...] = ()
    highlight_kind: str = ""  # "compare" | "move" | ""


@dataclass(frozen=True)
class Recording:
    initial: list[int]
    events: list[Event]
    elapsed_ms: float
    stats: Stats


def record(algorithm: Algorithm, array: list[int]) -> Recording:
    start = time.perf_counter()
    events = list(algorithm(array))
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return Recording(
        initial=list(array),
        events=events,
        elapsed_ms=elapsed_ms,
        stats=compute(events),
    )


def apply(state: State, event: Event) -> None:
    if isinstance(event, Compare):
        state.highlight = (event.i, event.j)
        state.highlight_kind = "compare"
    elif isinstance(event, Swap):
        state.data[event.i], state.data[event.j] = state.data[event.j], state.data[event.i]
        state.highlight = (event.i, event.j)
        state.highlight_kind = "move"
    elif isinstance(event, Overwrite):
        state.data[event.i] = event.value
        state.highlight = (event.i,)
        state.highlight_kind = "move"
    elif isinstance(event, MarkSorted):
        state.sorted_idx.add(event.i)
        state.highlight = ()
        state.highlight_kind = ""


def revert(state: State, event: Event) -> None:
    if isinstance(event, Swap):
        state.data[event.i], state.data[event.j] = state.data[event.j], state.data[event.i]
    elif isinstance(event, Overwrite):
        state.data[event.i] = event.old
    elif isinstance(event, MarkSorted):
        state.sorted_idx.discard(event.i)
    state.highlight = ()
    state.highlight_kind = ""


class Timeline:
    """Navigable playback over a Recording's event log."""

    def __init__(self, recording: Recording) -> None:
        self.recording = recording
        self.index = 0  # number of events already applied
        self.state = State(data=list(recording.initial))

    @property
    def length(self) -> int:
        return len(self.recording.events)

    @property
    def at_end(self) -> bool:
        return self.index >= self.length

    def step_forward(self) -> bool:
        if self.index >= self.length:
            return False
        apply(self.state, self.recording.events[self.index])
        self.index += 1
        return True

    def step_back(self) -> bool:
        if self.index <= 0:
            return False
        self.index -= 1
        revert(self.state, self.recording.events[self.index])
        return True

    def reset(self) -> None:
        self.index = 0
        self.state = State(data=list(self.recording.initial))
