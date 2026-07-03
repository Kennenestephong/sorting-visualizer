# A-01 Sorting Visualizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PySide6 desktop app that visualizes four sorting algorithms step-by-step, with a 4-way race mode, operation counters, and JSON/CSV file I/O, packaged in Docker.

**Architecture:** Three layers with one-way dependencies (UI → core → events). Algorithms are pure-Python generators that `yield` events (`Compare`/`Swap`/`Overwrite`/`MarkSorted`). A runner materializes the full event log; a `Timeline` applies/reverts events to a mutable `State`, enabling step-forward/step-back and synchronized race playback. The UI is a thin layer driven by a `QTimer` over the timeline index.

**Tech Stack:** Python 3.12, PySide6 (LGPL), pytest, pytest-qt. Qt "offscreen" platform for headless tests.

**Design spec:** `docs/superpowers/specs/2026-07-02-a01-sorting-visualizer-design.md`

**Refinements vs spec (discovered during planning):**
- Algorithm registry is a plain dict in `core/algorithms/__init__.py` (no separate `base.py` / decorator) — simpler and explicit.
- Tests use the Qt **offscreen** platform (`QT_QPA_PLATFORM=offscreen`, set in `conftest.py`) instead of `xvfb`. Headless tests then need no X server at all. `xvfb`/X-forwarding is only relevant for running the real GUI in Docker (documented in README).
- `State` carries a `highlight_kind` (`"compare"`/`"move"`) so the widget can color compares (yellow) vs moves (red).

**Convention:** Every commit ends with the trailer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` (shown in each commit step).

---

## File Structure

```
sorting_visualizer/
  __init__.py
  app.py                      # QApplication entry point
  core/
    __init__.py
    events.py                 # Compare, Swap, Overwrite, MarkSorted, Event
    fill.py                   # FillMode, generate()
    stats.py                  # Stats, compute()
    runner.py                 # State, Recording, record(), apply(), revert(), Timeline
    algorithms/
      __init__.py             # ALGORITHMS registry + Algorithm type alias
      bubble.py insertion.py merge.py quick.py
  io/
    __init__.py
    array_store.py            # save(), load(), LoadedArray, ArrayLoadError
    stats_export.py           # StatsRow, export()
  ui/
    __init__.py
    bar_widget.py             # BarWidget, bar_role(), COLORS
    controls.py               # ControlPanel (signals)
    single_view.py            # SingleView
    race_view.py              # RaceView
    main_window.py            # MainWindow
tests/
  __init__.py
  core/  io/  ui/  data/
conftest.py                   # sets QT_QPA_PLATFORM=offscreen
pyproject.toml                # pytest config
requirements.txt
Dockerfile  .dockerignore  README.md
```

---

## Task 0: Project scaffolding

**Files:**
- Create: `requirements.txt`, `pyproject.toml`, `conftest.py`
- Create: `sorting_visualizer/__init__.py`, `sorting_visualizer/core/__init__.py`, `sorting_visualizer/core/algorithms/__init__.py`, `sorting_visualizer/io/__init__.py`, `sorting_visualizer/ui/__init__.py`
- Create: `tests/__init__.py`, `tests/core/__init__.py`, `tests/io/__init__.py`, `tests/ui/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
PySide6>=6.10
pytest>=8
pytest-qt>=4.4
```

> Note: PySide6 ships abi3 wheels (cp310-abi3) that work on Python 3.10–3.14. The floor
> `>=6.10` is required because earlier releases have no wheels for Python 3.13/3.14.

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 3: Create `conftest.py`** (repo root)

```python
import os

# Run Qt headless in tests: no display / no xvfb needed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
```

- [ ] **Step 4: Create empty package files**

Create each of these as an empty file (0 bytes):
`sorting_visualizer/__init__.py`, `sorting_visualizer/core/__init__.py`,
`sorting_visualizer/core/algorithms/__init__.py`, `sorting_visualizer/io/__init__.py`,
`sorting_visualizer/ui/__init__.py`, `tests/__init__.py`, `tests/core/__init__.py`,
`tests/io/__init__.py`, `tests/ui/__init__.py`.

- [ ] **Step 5: Create virtualenv and install deps**

Run:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: installs succeed. (On Linux/macOS use `.venv/bin/python`.)

- [ ] **Step 6: Verify pytest collects nothing yet**

Run: `.venv/Scripts/python -m pytest`
Expected: "no tests ran" (exit code 5) — confirms config loads.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pyproject.toml conftest.py sorting_visualizer tests
git commit -m "chore: scaffold project structure and test config" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 1: Events

**Files:**
- Create: `sorting_visualizer/core/events.py`
- Test: `tests/core/test_events.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.events import Compare, Swap, Overwrite, MarkSorted


def test_events_are_frozen_and_carry_fields():
    assert Compare(1, 2).i == 1 and Compare(1, 2).j == 2
    assert Swap(3, 4).j == 4
    ow = Overwrite(0, 9, 5)
    assert (ow.i, ow.value, ow.old) == (0, 9, 5)
    assert MarkSorted(7).i == 7


def test_events_equal_by_value():
    assert Compare(1, 2) == Compare(1, 2)
    assert Swap(1, 2) != Swap(2, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_events.py -v`
Expected: FAIL — `ModuleNotFoundError: sorting_visualizer.core.events`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/events.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Compare:
    i: int
    j: int


@dataclass(frozen=True)
class Swap:
    i: int
    j: int


@dataclass(frozen=True)
class Overwrite:
    i: int
    value: int
    old: int


@dataclass(frozen=True)
class MarkSorted:
    i: int


Event = Union[Compare, Swap, Overwrite, MarkSorted]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_events.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/events.py tests/core/test_events.py
git commit -m "feat: add sorting event model" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Array fill generator

**Files:**
- Create: `sorting_visualizer/core/fill.py`
- Test: `tests/core/test_fill.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.fill import FillMode, generate


def test_random_is_permutation_of_1_to_n():
    out = generate(50, FillMode.RANDOM, seed=1)
    assert sorted(out) == list(range(1, 51))


def test_reversed_is_descending():
    assert generate(5, FillMode.REVERSED) == [5, 4, 3, 2, 1]


def test_nearly_sorted_is_mostly_sorted():
    out = generate(100, FillMode.NEARLY_SORTED, seed=1)
    misplaced = sum(1 for i, v in enumerate(out) if v != i + 1)
    assert 0 < misplaced <= 20  # a few swaps only


def test_seed_is_reproducible():
    assert generate(30, FillMode.RANDOM, seed=7) == generate(30, FillMode.RANDOM, seed=7)


def test_small_sizes_do_not_crash():
    assert generate(0, FillMode.NEARLY_SORTED) == []
    assert generate(1, FillMode.NEARLY_SORTED) == [1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_fill.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/fill.py`:
```python
from __future__ import annotations

import random
from enum import Enum


class FillMode(str, Enum):
    RANDOM = "random"
    REVERSED = "reversed"
    NEARLY_SORTED = "nearly_sorted"


def generate(size: int, mode: FillMode, seed: int | None = None) -> list[int]:
    if size < 0:
        raise ValueError("size must be non-negative")
    rng = random.Random(seed)
    base = list(range(1, size + 1))
    if mode == FillMode.RANDOM:
        rng.shuffle(base)
    elif mode == FillMode.REVERSED:
        base.reverse()
    elif mode == FillMode.NEARLY_SORTED:
        if size >= 2:
            swaps = max(1, size // 20)
            for _ in range(swaps):
                i = rng.randrange(size)
                j = rng.randrange(size)
                base[i], base[j] = base[j], base[i]
    return base
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_fill.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/fill.py tests/core/test_fill.py
git commit -m "feat: add array fill generator" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Bubble sort

**Files:**
- Create: `sorting_visualizer/core/algorithms/bubble.py`
- Test: `tests/core/test_bubble.py`

**Shared test idea (used in Tasks 3–6):** applying every event in order to a copy of the input must produce the sorted array. This validates `Swap`/`Overwrite` correctness independent of the UI.

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms.bubble import bubble_sort
from sorting_visualizer.core.events import Compare, Swap, MarkSorted


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_bubble_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2]
    events = list(bubble_sort(data))
    assert _replay(data, events) == sorted(data)


def test_bubble_only_emits_expected_event_types():
    for e in bubble_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_bubble_handles_empty_and_single():
    assert list(bubble_sort([])) == []
    assert _replay([9], list(bubble_sort([9]))) == [9]


def test_bubble_does_not_mutate_input():
    data = [3, 1, 2]
    list(bubble_sort(data))
    assert data == [3, 1, 2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_bubble.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/algorithms/bubble.py`:
```python
from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def bubble_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    n = len(data)
    for i in range(n):
        for j in range(n - 1 - i):
            yield Compare(j, j + 1)
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                yield Swap(j, j + 1)
        yield MarkSorted(n - 1 - i)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_bubble.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/algorithms/bubble.py tests/core/test_bubble.py
git commit -m "feat: add bubble sort algorithm" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Insertion sort

**Files:**
- Create: `sorting_visualizer/core/algorithms/insertion.py`
- Test: `tests/core/test_insertion.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms.insertion import insertion_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Swap


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_insertion_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2]
    assert _replay(data, list(insertion_sort(data))) == sorted(data)


def test_insertion_only_emits_expected_event_types():
    for e in insertion_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_insertion_handles_empty_and_single():
    assert list(insertion_sort([])) == []
    assert _replay([9], list(insertion_sort([9]))) == [9]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_insertion.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/algorithms/insertion.py`:
```python
from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def insertion_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    n = len(data)
    for i in range(1, n):
        j = i
        while j > 0:
            yield Compare(j - 1, j)
            if data[j - 1] > data[j]:
                data[j - 1], data[j] = data[j], data[j - 1]
                yield Swap(j - 1, j)
                j -= 1
            else:
                break
    for k in range(n):
        yield MarkSorted(k)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_insertion.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/algorithms/insertion.py tests/core/test_insertion.py
git commit -m "feat: add insertion sort algorithm" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Merge sort

**Files:**
- Create: `sorting_visualizer/core/algorithms/merge.py`
- Test: `tests/core/test_merge.py`

**Note:** Merge sort writes values into place rather than swapping, so it emits `Overwrite` (not `Swap`). The replay helper here applies `Overwrite`.

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms.merge import merge_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Overwrite):
            arr[e.i] = e.value
    return arr


def test_merge_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2, 9, 0]
    assert _replay(data, list(merge_sort(data))) == sorted(data)


def test_merge_overwrite_old_matches_prior_value():
    data = [3, 1, 2]
    arr = list(data)
    for e in merge_sort(data):
        if isinstance(e, Overwrite):
            assert arr[e.i] == e.old  # old reflects current cell before write
            arr[e.i] = e.value


def test_merge_only_emits_expected_event_types():
    for e in merge_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Overwrite, MarkSorted))


def test_merge_handles_empty_and_single():
    assert list(merge_sort([])) == []
    assert _replay([9], list(merge_sort([9]))) == [9]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_merge.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/algorithms/merge.py`:
```python
from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Overwrite


def merge_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    yield from _msort(data, 0, len(data) - 1)
    for k in range(len(data)):
        yield MarkSorted(k)


def _msort(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    yield from _msort(data, lo, mid)
    yield from _msort(data, mid + 1, hi)
    yield from _merge(data, lo, mid, hi)


def _merge(data: list[int], lo: int, mid: int, hi: int) -> Iterator[Event]:
    left = data[lo : mid + 1]
    right = data[mid + 1 : hi + 1]
    i = j = 0
    k = lo
    while i < len(left) and j < len(right):
        yield Compare(lo + i, mid + 1 + j)
        if left[i] <= right[j]:
            old, data[k] = data[k], left[i]
            yield Overwrite(k, left[i], old)
            i += 1
        else:
            old, data[k] = data[k], right[j]
            yield Overwrite(k, right[j], old)
            j += 1
        k += 1
    while i < len(left):
        old, data[k] = data[k], left[i]
        yield Overwrite(k, left[i], old)
        i += 1
        k += 1
    while j < len(right):
        old, data[k] = data[k], right[j]
        yield Overwrite(k, right[j], old)
        j += 1
        k += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_merge.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/algorithms/merge.py tests/core/test_merge.py
git commit -m "feat: add merge sort algorithm" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Quick sort

**Files:**
- Create: `sorting_visualizer/core/algorithms/quick.py`
- Test: `tests/core/test_quick.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms.quick import quick_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Swap


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_quick_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2, 9, 0, 7]
    assert _replay(data, list(quick_sort(data))) == sorted(data)


def test_quick_never_swaps_element_with_itself():
    for e in quick_sort([3, 1, 2, 3, 1]):
        if isinstance(e, Swap):
            assert e.i != e.j


def test_quick_only_emits_expected_event_types():
    for e in quick_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_quick_handles_empty_and_single():
    assert list(quick_sort([])) == []
    assert _replay([9], list(quick_sort([9]))) == [9]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_quick.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/algorithms/quick.py`:
```python
from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def quick_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    yield from _qsort(data, 0, len(data) - 1)
    for k in range(len(data)):
        yield MarkSorted(k)


def _qsort(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    if lo >= hi:
        return
    pivot_index = yield from _partition(data, lo, hi)
    yield from _qsort(data, lo, pivot_index - 1)
    yield from _qsort(data, pivot_index + 1, hi)


def _partition(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    pivot = data[hi]
    i = lo
    for j in range(lo, hi):
        yield Compare(j, hi)
        if data[j] < pivot:
            if i != j:
                data[i], data[j] = data[j], data[i]
                yield Swap(i, j)
            i += 1
    if i != hi:
        data[i], data[hi] = data[hi], data[i]
        yield Swap(i, hi)
    return i
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_quick.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/algorithms/quick.py tests/core/test_quick.py
git commit -m "feat: add quick sort algorithm" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Algorithm registry

**Files:**
- Modify: `sorting_visualizer/core/algorithms/__init__.py` (currently empty)
- Test: `tests/core/test_registry.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms import ALGORITHMS


def test_registry_has_the_four_algorithms_in_order():
    assert list(ALGORITHMS.keys()) == ["bubble", "insertion", "merge", "quick"]


def test_registry_values_are_callable_generators():
    for name, fn in ALGORITHMS.items():
        events = list(fn([3, 1, 2]))
        assert events, f"{name} produced no events"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_registry.py -v`
Expected: FAIL — `ImportError: cannot import name 'ALGORITHMS'`

- [ ] **Step 3: Write minimal implementation**

Replace the contents of `sorting_visualizer/core/algorithms/__init__.py`:
```python
from __future__ import annotations

from collections.abc import Callable, Iterator

from ..events import Event
from .bubble import bubble_sort
from .insertion import insertion_sort
from .merge import merge_sort
from .quick import quick_sort

Algorithm = Callable[[list[int]], Iterator[Event]]

ALGORITHMS: dict[str, Algorithm] = {
    "bubble": bubble_sort,
    "insertion": insertion_sort,
    "merge": merge_sort,
    "quick": quick_sort,
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_registry.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/algorithms/__init__.py tests/core/test_registry.py
git commit -m "feat: add algorithm registry" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Stats

**Files:**
- Create: `sorting_visualizer/core/stats.py`
- Test: `tests/core/test_stats.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.stats import Stats, compute


def test_compute_counts_comparisons_and_writes():
    events = [Compare(0, 1), Swap(0, 1), Compare(1, 2), Overwrite(2, 5, 3), MarkSorted(0)]
    result = compute(events)
    assert result == Stats(comparisons=2, writes=2)


def test_compute_empty():
    assert compute([]) == Stats(comparisons=0, writes=0)


def test_marksorted_and_compare_do_not_count_as_writes():
    assert compute([Compare(0, 1), MarkSorted(0)]).writes == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_stats.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/stats.py`:
```python
from __future__ import annotations

from dataclasses import dataclass

from .events import Compare, Event, Overwrite, Swap


@dataclass(frozen=True)
class Stats:
    comparisons: int
    writes: int


def compute(events: list[Event]) -> Stats:
    comparisons = sum(1 for e in events if isinstance(e, Compare))
    writes = sum(1 for e in events if isinstance(e, (Swap, Overwrite)))
    return Stats(comparisons=comparisons, writes=writes)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_stats.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/stats.py tests/core/test_stats.py
git commit -m "feat: add operation statistics" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Runner — State, Recording, record/apply/revert

**Files:**
- Create: `sorting_visualizer/core/runner.py`
- Test: `tests/core/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.runner import State, apply, record, revert


def test_record_captures_events_stats_and_time():
    rec = record(ALGORITHMS["bubble"], [3, 1, 2])
    assert rec.initial == [3, 1, 2]
    assert rec.events
    assert rec.stats.comparisons > 0
    assert rec.elapsed_ms >= 0.0


def test_apply_all_events_sorts_the_state():
    data = [5, 3, 4, 1, 2, 9, 0]
    rec = record(ALGORITHMS["quick"], data)
    state = State(data=list(rec.initial))
    for e in rec.events:
        apply(state, e)
    assert state.data == sorted(data)


def test_revert_all_in_reverse_restores_initial():
    # revert is the inverse of apply only in sequential use (the way Timeline
    # steps back): apply every event, then revert them in reverse order.
    # This must hold for merge sort too, which overwrites the same index
    # multiple times with differing `old` values.
    data = [5, 3, 4, 1, 2]
    rec = record(ALGORITHMS["merge"], data)
    state = State(data=list(rec.initial))
    for e in rec.events:
        apply(state, e)
    for e in reversed(rec.events):
        revert(state, e)
    assert state.data == list(rec.initial)
    assert state.sorted_idx == set()


def test_apply_sets_highlight_kind():
    state = State(data=[2, 1])
    apply(state, Compare(0, 1))
    assert state.highlight == (0, 1) and state.highlight_kind == "compare"
    apply(state, Swap(0, 1))
    assert state.highlight_kind == "move" and state.data == [1, 2]
    apply(state, MarkSorted(0))
    assert 0 in state.sorted_idx and state.highlight == ()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/core/runner.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_runner.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/runner.py tests/core/test_runner.py
git commit -m "feat: add runner with record/apply/revert" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Timeline

**Files:**
- Modify: `sorting_visualizer/core/runner.py` (append `Timeline`)
- Test: `tests/core/test_timeline.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.runner import Timeline, record


def _timeline(name, data):
    return Timeline(record(ALGORITHMS[name], data))


def test_forward_to_end_sorts():
    data = [5, 3, 4, 1, 2]
    tl = _timeline("bubble", data)
    while tl.step_forward():
        pass
    assert tl.at_end
    assert tl.state.data == sorted(data)


def test_step_back_is_inverse_of_step_forward():
    tl = _timeline("quick", [5, 3, 4, 1, 2])
    tl.step_forward()
    tl.step_forward()
    snapshot = list(tl.state.data)
    tl.step_forward()
    tl.step_back()
    assert tl.state.data == snapshot


def test_bounds_do_not_move_past_ends():
    tl = _timeline("insertion", [3, 1, 2])
    assert tl.step_back() is False  # already at start
    while tl.step_forward():
        pass
    assert tl.step_forward() is False  # already at end


def test_reset_returns_to_initial():
    data = [5, 3, 4, 1, 2]
    tl = _timeline("merge", data)
    tl.step_forward()
    tl.step_forward()
    tl.reset()
    assert tl.index == 0
    assert tl.state.data == data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/core/test_timeline.py -v`
Expected: FAIL — `ImportError: cannot import name 'Timeline'`

- [ ] **Step 3: Write minimal implementation**

Append to `sorting_visualizer/core/runner.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/core/test_timeline.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/core/runner.py tests/core/test_timeline.py
git commit -m "feat: add navigable timeline" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11: Array store (JSON I/O)

**Files:**
- Create: `sorting_visualizer/io/array_store.py`
- Test: `tests/io/test_array_store.py`

- [ ] **Step 1: Write the failing test**

```python
import json

import pytest

from sorting_visualizer.io.array_store import ArrayLoadError, LoadedArray, load, save


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "arr.json"
    data = list(range(1, 21))
    save(path, data, "random")
    loaded = load(path)
    assert isinstance(loaded, LoadedArray)
    assert loaded.data == data
    assert loaded.fill == "random"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ArrayLoadError):
        load(tmp_path / "nope.json")


def test_load_bad_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ArrayLoadError):
        load(p)


def test_load_missing_data_field_raises(tmp_path):
    p = tmp_path / "nodata.json"
    p.write_text(json.dumps({"size": 3}), encoding="utf-8")
    with pytest.raises(ArrayLoadError):
        load(p)


def test_load_rejects_size_out_of_range(tmp_path):
    p = tmp_path / "small.json"
    p.write_text(json.dumps({"data": [1, 2, 3]}), encoding="utf-8")  # < 10
    with pytest.raises(ArrayLoadError):
        load(p)


def test_load_rejects_non_integer_data(tmp_path):
    p = tmp_path / "floats.json"
    p.write_text(json.dumps({"data": [1.5] * 12}), encoding="utf-8")
    with pytest.raises(ArrayLoadError):
        load(p)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/io/test_array_store.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/io/array_store.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/io/test_array_store.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/io/array_store.py tests/io/test_array_store.py
git commit -m "feat: add JSON array store" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 12: Stats export (CSV)

**Files:**
- Create: `sorting_visualizer/io/stats_export.py`
- Test: `tests/io/test_stats_export.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.io.stats_export import StatsRow, export


def test_export_writes_header_and_rows(tmp_path):
    path = tmp_path / "stats.csv"
    rows = [
        StatsRow("bubble", 50, "random", 1225, 932, 1.4),
        StatsRow("quick", 50, "random", 286, 141, 0.3),
    ]
    export(path, rows)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "algorithm,size,fill,comparisons,writes,time_ms"
    assert lines[1] == "bubble,50,random,1225,932,1.4"
    assert lines[2] == "quick,50,random,286,141,0.3"


def test_export_empty_rows_writes_only_header(tmp_path):
    path = tmp_path / "empty.csv"
    export(path, [])
    assert path.read_text(encoding="utf-8").splitlines() == [
        "algorithm,size,fill,comparisons,writes,time_ms"
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/io/test_stats_export.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/io/stats_export.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/io/test_stats_export.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/io/stats_export.py tests/io/test_stats_export.py
git commit -m "feat: add CSV stats export" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 13: Bar widget + role coloring

**Files:**
- Create: `sorting_visualizer/ui/bar_widget.py`
- Test: `tests/ui/test_bar_widget.py`

**Note:** `bar_role` is pure logic (no Qt) and is the main unit under test. The widget itself gets a headless smoke test (offscreen platform, set by `conftest.py`).

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.runner import State
from sorting_visualizer.ui.bar_widget import COLORS, BarWidget, bar_role


def test_bar_role_prioritizes_sorted():
    state = State(data=[1, 2], sorted_idx={0}, highlight=(0,), highlight_kind="compare")
    assert bar_role(0, state) == "sorted"


def test_bar_role_reports_highlight_kind():
    state = State(data=[1, 2], highlight=(0, 1), highlight_kind="compare")
    assert bar_role(0, state) == "compare"
    assert bar_role(1, state) == "compare"


def test_bar_role_defaults_to_normal():
    assert bar_role(5, State(data=[1, 2, 3])) == "normal"


def test_every_role_has_a_color():
    for role in ("normal", "compare", "move", "sorted"):
        assert role in COLORS


def test_widget_accepts_state_without_crashing(qtbot):
    w = BarWidget()
    qtbot.addWidget(w)
    w.set_state(State(data=[3, 1, 2], highlight=(0, 1), highlight_kind="compare"))
    w.resize(200, 150)
    w.show()  # triggers paintEvent under offscreen platform
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_bar_widget.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/ui/bar_widget.py`:
```python
from __future__ import annotations

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from ..core.runner import State

COLORS = {
    "normal": "#B0B0B0",
    "compare": "#F2C037",
    "move": "#E5484D",
    "sorted": "#46A758",
}


def bar_role(index: int, state: State) -> str:
    if index in state.sorted_idx:
        return "sorted"
    if index in state.highlight:
        return state.highlight_kind or "normal"
    return "normal"


class BarWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = State(data=[])
        self.setMinimumSize(200, 150)

    def set_state(self, state: State) -> None:
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        data = self._state.data
        n = len(data)
        if n == 0:
            return
        w = self.width()
        h = self.height()
        max_val = max(data) or 1
        bar_w = w / n
        for i, val in enumerate(data):
            bar_h = int((val / max_val) * h)
            painter.fillRect(
                int(i * bar_w),
                h - bar_h,
                max(1, int(bar_w) - 1),
                bar_h,
                QColor(COLORS[bar_role(i, self._state)]),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_bar_widget.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/ui/bar_widget.py tests/ui/test_bar_widget.py
git commit -m "feat: add bar widget with role coloring" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 14: Control panel

**Files:**
- Create: `sorting_visualizer/ui/controls.py`
- Test: `tests/ui/test_controls.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.fill import FillMode
from sorting_visualizer.ui.controls import ControlPanel


def test_step_buttons_emit_signals(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.step_forward, timeout=1000):
        panel.forward_button.click()
    with qtbot.waitSignal(panel.step_back, timeout=1000):
        panel.back_button.click()


def test_size_spinner_emits_size_changed(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.size_changed, timeout=1000) as blocker:
        panel.size_spin.setValue(42)
    assert blocker.args == [42]


def test_fill_combo_emits_fill_changed(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.fill_changed, timeout=1000) as blocker:
        panel.fill_combo.setCurrentText(FillMode.REVERSED.value)
    assert blocker.args == [FillMode.REVERSED.value]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_controls.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/ui/controls.py`:
```python
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QWidget,
)
from PySide6.QtCore import Qt

from ..core.fill import FillMode
from ..io.array_store import MAX_SIZE, MIN_SIZE

DEFAULT_SIZE = 50
MIN_DELAY_MS = 5
MAX_DELAY_MS = 500
DEFAULT_DELAY_MS = 60


class ControlPanel(QWidget):
    play_toggled = Signal(bool)
    step_forward = Signal()
    step_back = Signal()
    reset_requested = Signal()
    speed_changed = Signal(int)  # delay in ms per step
    size_changed = Signal(int)
    fill_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None, show_array_controls: bool = True) -> None:
        super().__init__(parent)

        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        self.back_button = QPushButton("< Step")
        self.forward_button = QPushButton("Step >")
        self.reset_button = QPushButton("Reset")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(MIN_DELAY_MS, MAX_DELAY_MS)
        self.speed_slider.setValue(DEFAULT_DELAY_MS)

        layout = QHBoxLayout(self)
        for w in (self.play_button, self.back_button, self.forward_button, self.reset_button):
            layout.addWidget(w)
        layout.addWidget(QLabel("Speed"))
        layout.addWidget(self.speed_slider)

        # Size/fill only make sense where the array is chosen (single view).
        # Race view shares the array from MainWindow, so it omits them.
        if show_array_controls:
            self.size_spin = QSpinBox()
            self.size_spin.setRange(MIN_SIZE, MAX_SIZE)
            self.size_spin.setValue(DEFAULT_SIZE)
            self.fill_combo = QComboBox()
            self.fill_combo.addItems([m.value for m in FillMode])
            layout.addWidget(QLabel("Size"))
            layout.addWidget(self.size_spin)
            layout.addWidget(QLabel("Fill"))
            layout.addWidget(self.fill_combo)

        self.play_button.toggled.connect(self.play_toggled)
        self.back_button.clicked.connect(self.step_back)
        self.forward_button.clicked.connect(self.step_forward)
        self.reset_button.clicked.connect(self.reset_requested)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        if show_array_controls:
            self.size_spin.valueChanged.connect(self.size_changed)
            self.fill_combo.currentTextChanged.connect(self.fill_changed)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_controls.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/ui/controls.py tests/ui/test_controls.py
git commit -m "feat: add control panel" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 15: Single view

**Files:**
- Create: `sorting_visualizer/ui/single_view.py`
- Test: `tests/ui/test_single_view.py`

**Behavior:** Choose an algorithm; loading an array records it and builds a `Timeline`. Controls drive step/play/reset. A `QTimer` (interval = speed slider value) advances one step per tick and stops at the end. Stats label shows comparisons/writes/time. Exposes `stats_rows()` for CSV export.

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.ui.single_view import SingleView


def test_load_array_builds_timeline_at_start(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    assert view.timeline is not None
    assert view.timeline.index == 0


def test_step_forward_advances_one_event(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view.on_step_forward()
    assert view.timeline.index == 1


def test_changing_algorithm_rebuilds_and_resets(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view.on_step_forward()
    view.select_algorithm("quick")
    assert view.timeline.index == 0
    assert view.current_algorithm == "quick"


def test_stats_rows_reports_current_algorithm(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array(list(range(10, 0, -1)), "reversed")
    rows = view.stats_rows()
    assert len(rows) == 1
    assert rows[0].algorithm == view.current_algorithm
    assert rows[0].size == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_single_view.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/ui/single_view.py`:
```python
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from ..core.algorithms import ALGORITHMS
from ..core.runner import Timeline, record
from ..io.stats_export import StatsRow
from .bar_widget import BarWidget
from .controls import ControlPanel


class SingleView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[int] = []
        self._fill = "custom"
        self.current_algorithm = next(iter(ALGORITHMS))
        self.timeline: Timeline | None = None

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(list(ALGORITHMS.keys()))
        self.bars = BarWidget()
        self.controls = ControlPanel()
        self.stats_label = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.algo_combo)
        layout.addWidget(self.bars, stretch=1)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.controls)

        self.timer = QTimer(self)
        self.timer.setInterval(self.controls.speed_slider.value())

        self.algo_combo.currentTextChanged.connect(self.select_algorithm)
        self.controls.step_forward.connect(self.on_step_forward)
        self.controls.step_back.connect(self.on_step_back)
        self.controls.reset_requested.connect(self.on_reset)
        self.controls.play_toggled.connect(self.on_play_toggled)
        self.controls.speed_changed.connect(self.timer.setInterval)
        self.timer.timeout.connect(self._tick)

    def load_array(self, data: list[int], fill: str) -> None:
        self._data = list(data)
        self._fill = fill
        self._rebuild()

    def select_algorithm(self, name: str) -> None:
        self.current_algorithm = name
        self._rebuild()

    def _rebuild(self) -> None:
        if not self._data:
            return
        recording = record(ALGORITHMS[self.current_algorithm], self._data)
        self.timeline = Timeline(recording)
        self._refresh()

    def _refresh(self) -> None:
        if self.timeline is None:
            return
        self.bars.set_state(self.timeline.state)
        stats = self.timeline.recording.stats
        self.stats_label.setText(
            f"comparisons: {stats.comparisons}   writes: {stats.writes}   "
            f"time: {self.timeline.recording.elapsed_ms:.1f} ms"
        )

    def on_step_forward(self) -> None:
        if self.timeline and self.timeline.step_forward():
            self._refresh()

    def on_step_back(self) -> None:
        if self.timeline and self.timeline.step_back():
            self._refresh()

    def on_reset(self) -> None:
        if self.timeline:
            self.timeline.reset()
            self._refresh()

    def on_play_toggled(self, playing: bool) -> None:
        if playing:
            self.timer.start()
        else:
            self.timer.stop()

    def _tick(self) -> None:
        if self.timeline and not self.timeline.step_forward():
            self.timer.stop()
            self.controls.play_button.setChecked(False)
            return
        self._refresh()

    def stats_rows(self) -> list[StatsRow]:
        if self.timeline is None:
            return []
        stats = self.timeline.recording.stats
        return [
            StatsRow(
                algorithm=self.current_algorithm,
                size=len(self._data),
                fill=self._fill,
                comparisons=stats.comparisons,
                writes=stats.writes,
                time_ms=self.timeline.recording.elapsed_ms,
            )
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_single_view.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/ui/single_view.py tests/ui/test_single_view.py
git commit -m "feat: add single-algorithm view" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 16: Race view

**Files:**
- Create: `sorting_visualizer/ui/race_view.py`
- Test: `tests/ui/test_race_view.py`

**Behavior:** Four panels (one per algorithm, registry order), each with a `BarWidget` and a live operation counter. One shared `QTimer`; each tick advances every unfinished timeline by one step. Finished timelines stay put. Exposes `stats_rows()` returning all four rows.

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.ui.race_view import RaceView


def test_load_array_builds_four_timelines(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    assert set(view.timelines.keys()) == set(ALGORITHMS.keys())
    assert all(tl.index == 0 for tl in view.timelines.values())


def test_tick_advances_all_unfinished(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view._tick()
    assert all(tl.index == 1 for tl in view.timelines.values())


def test_run_to_completion_sorts_every_panel(qtbot):
    data = [5, 3, 4, 1, 2, 9, 0]
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array(data, "random")
    for _ in range(10_000):
        if all(tl.at_end for tl in view.timelines.values()):
            break
        view._tick()
    assert all(tl.state.data == sorted(data) for tl in view.timelines.values())


def test_stats_rows_has_four_rows(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array(list(range(20, 0, -1)), "reversed")
    rows = view.stats_rows()
    assert len(rows) == 4
    assert {r.algorithm for r in rows} == set(ALGORITHMS.keys())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_race_view.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/ui/race_view.py`:
```python
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ..core.algorithms import ALGORITHMS
from ..core.runner import Timeline, record
from ..io.stats_export import StatsRow
from .bar_widget import BarWidget
from .controls import ControlPanel


class _Panel(QWidget):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.bars = BarWidget()
        self.counter = QLabel(f"{name}: 0 ops")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(name))
        layout.addWidget(self.bars, stretch=1)
        layout.addWidget(self.counter)


class RaceView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[int] = []
        self._fill = "custom"
        self.timelines: dict[str, Timeline] = {}
        self._panels: dict[str, _Panel] = {}

        grid = QGridLayout()
        for idx, name in enumerate(ALGORITHMS):
            panel = _Panel(name)
            self._panels[name] = panel
            grid.addWidget(panel, idx // 2, idx % 2)

        # Race view shares the array from MainWindow; it only needs playback controls.
        self.controls = ControlPanel(show_array_controls=False)
        layout = QVBoxLayout(self)
        layout.addLayout(grid, stretch=1)
        layout.addWidget(self.controls)

        self.timer = QTimer(self)
        self.timer.setInterval(self.controls.speed_slider.value())
        self.controls.step_forward.connect(self._tick)
        self.controls.step_back.connect(self._tick_back)
        self.controls.reset_requested.connect(self.on_reset)
        self.controls.play_toggled.connect(self.on_play_toggled)
        self.controls.speed_changed.connect(self.timer.setInterval)
        self.timer.timeout.connect(self._auto_tick)

    def load_array(self, data: list[int], fill: str) -> None:
        self._data = list(data)
        self._fill = fill
        self.timelines = {
            name: Timeline(record(fn, self._data)) for name, fn in ALGORITHMS.items()
        }
        self._refresh()

    def _refresh(self) -> None:
        for name, tl in self.timelines.items():
            panel = self._panels[name]
            panel.bars.set_state(tl.state)
            panel.counter.setText(f"{name}: {tl.index} ops")

    def _tick(self) -> None:
        for tl in self.timelines.values():
            tl.step_forward()
        self._refresh()

    def _tick_back(self) -> None:
        for tl in self.timelines.values():
            tl.step_back()
        self._refresh()

    def _auto_tick(self) -> None:
        if all(tl.at_end for tl in self.timelines.values()):
            self.timer.stop()
            self.controls.play_button.setChecked(False)
            return
        self._tick()

    def on_reset(self) -> None:
        for tl in self.timelines.values():
            tl.reset()
        self._refresh()

    def on_play_toggled(self, playing: bool) -> None:
        if playing:
            self.timer.start()
        else:
            self.timer.stop()

    def stats_rows(self) -> list[StatsRow]:
        rows: list[StatsRow] = []
        for name, tl in self.timelines.items():
            stats = tl.recording.stats
            rows.append(
                StatsRow(
                    algorithm=name,
                    size=len(self._data),
                    fill=self._fill,
                    comparisons=stats.comparisons,
                    writes=stats.writes,
                    time_ms=tl.recording.elapsed_ms,
                )
            )
        return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_race_view.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/ui/race_view.py tests/ui/test_race_view.py
git commit -m "feat: add race view" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 17: Main window

**Files:**
- Create: `sorting_visualizer/ui/main_window.py`
- Test: `tests/ui/test_main_window.py`

**Behavior:** `QMainWindow` with a `QTabWidget` (Single / Race). On startup it generates an array from the control defaults and loads both views. A **File** menu wires: New array (regenerate), Open (JSON → both views), Save (current array → JSON), Export stats (active tab's rows → CSV). Size/fill changes regenerate the array.

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.io.array_store import load
from sorting_visualizer.ui.main_window import MainWindow


def test_startup_loads_both_views(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.single_view.timeline is not None
    assert len(win.race_view.timelines) == 4


def test_regenerate_changes_data_length(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.set_size(30)
    win.regenerate()
    assert len(win.current_array) == 30
    assert len(win.single_view.timeline.recording.initial) == 30


def test_save_and_reopen_roundtrip(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    path = tmp_path / "arr.json"
    win.save_array(path)
    loaded = load(path)
    assert loaded.data == win.current_array


def test_export_stats_writes_active_tab_rows(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    path = tmp_path / "stats.csv"
    win.export_stats(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("algorithm,")
    assert len(lines) >= 2  # header + at least one row
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_main_window.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/ui/main_window.py`:
```python
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from ..core.fill import FillMode, generate
from ..io.array_store import ArrayLoadError, load, save
from ..io.stats_export import export
from .controls import DEFAULT_SIZE
from .race_view import RaceView
from .single_view import SingleView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sorting Visualizer")
        self._size = DEFAULT_SIZE
        self._fill = FillMode.RANDOM
        self.current_array: list[int] = []

        self.single_view = SingleView()
        self.race_view = RaceView()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.single_view, "Single")
        self.tabs.addTab(self.race_view, "Race")
        self.setCentralWidget(self.tabs)

        # Size/fill are driven from the single view's control panel.
        self.single_view.controls.size_changed.connect(self.set_size)
        self.single_view.controls.fill_changed.connect(self.set_fill)

        self._build_menu()
        self.regenerate()

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("File")
        menu.addAction("New array", self.regenerate)
        menu.addAction("Open...", self._open_dialog)
        menu.addAction("Save...", self._save_dialog)
        menu.addAction("Export stats...", self._export_dialog)

    def set_size(self, size: int) -> None:
        self._size = size
        self.regenerate()

    def set_fill(self, fill: str) -> None:
        self._fill = FillMode(fill)
        self.regenerate()

    def regenerate(self) -> None:
        self.current_array = generate(self._size, self._fill)
        self._load_all(self.current_array, self._fill.value)

    def _load_all(self, data: list[int], fill: str) -> None:
        self.current_array = list(data)
        self.single_view.load_array(data, fill)
        self.race_view.load_array(data, fill)

    def save_array(self, path: str | Path) -> None:
        save(path, self.current_array, self._fill.value)

    def _active_rows(self):
        widget = self.tabs.currentWidget()
        return widget.stats_rows()

    def export_stats(self, path: str | Path) -> None:
        export(path, self._active_rows())

    # --- dialogs (thin wrappers with error handling) ---

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open array", "", "JSON (*.json)")
        if not path:
            return
        try:
            loaded = load(path)
        except ArrayLoadError as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
            return
        self._load_all(loaded.data, loaded.fill)

    def _save_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save array", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.save_array(path)
        except OSError as exc:
            QMessageBox.warning(self, "Save failed", str(exc))

    def _export_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export stats", "", "CSV (*.csv)")
        if not path:
            return
        try:
            self.export_stats(path)
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_main_window.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: add main window with file menu" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 18: Application entry point

**Files:**
- Create: `sorting_visualizer/app.py`
- Test: `tests/ui/test_app.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.app import build_window


def test_build_window_returns_main_window(qtbot):
    win = build_window()
    qtbot.addWidget(win)
    assert win.windowTitle() == "Sorting Visualizer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/ui/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/app.py`:
```python
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def build_window() -> MainWindow:
    return MainWindow()


def main() -> int:
    app = QApplication(sys.argv)
    window = build_window()
    window.resize(1000, 700)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/ui/test_app.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/app.py tests/ui/test_app.py
git commit -m "feat: add application entry point" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 19: Docker packaging + README

**Files:**
- Create: `Dockerfile`, `.dockerignore`, `README.md`

- [ ] **Step 1: Create `.dockerignore`**

```
.git
.venv
venv
__pycache__
*.pyc
.pytest_cache
docs
variants.pdf
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

# System libraries required by Qt (needed even for the offscreen platform).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libegl1 libglib2.0-0 libxkbcommon0 libdbus-1-3 libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the test suite headless as part of the build; build fails if tests are red.
ENV QT_QPA_PLATFORM=offscreen
RUN python -m pytest

# Default platform for the running app is the real X11 (overridable at run time).
ENV QT_QPA_PLATFORM=xcb
CMD ["python", "-m", "sorting_visualizer.app"]
```

- [ ] **Step 3: Create `README.md`**

````markdown
# Sorting Visualizer (A-01)

Desktop visualizer for four sorting algorithms (bubble, insertion, merge, quick):
step-by-step animation, a 4-way race mode, operation counters, and JSON/CSV file I/O.
Built with Python + PySide6.

## Run locally

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # Windows: .venv/Scripts/python
.venv/bin/python -m sorting_visualizer.app
```

## Tests

```bash
QT_QPA_PLATFORM=offscreen python -m pytest
```

## Docker

Build (runs the test suite as part of the build):

```bash
docker build -t sorting-visualizer .
```

Run the GUI — a desktop app needs the host display forwarded into the container:

- **Linux:**
  ```bash
  xhost +local:docker
  docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix sorting-visualizer
  ```
- **Windows / macOS:** run an X server (VcXsrv / XQuartz), then:
  ```bash
  docker run --rm -e DISPLAY=host.docker.internal:0 sorting-visualizer
  ```

Headless smoke run (no window, verifies it boots):

```bash
docker run --rm -e QT_QPA_PLATFORM=offscreen sorting-visualizer
```

## File formats

- **Array (JSON):** `{"version": 1, "size": 50, "fill": "random", "data": [...]}`
- **Stats (CSV):** `algorithm,size,fill,comparisons,writes,time_ms`
````

- [ ] **Step 4: Verify the image builds and tests pass inside it**

Run: `docker build -t sorting-visualizer .`
Expected: build completes; the `RUN python -m pytest` layer shows all tests passing.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore README.md
git commit -m "chore: add Docker packaging and README" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 20: Full suite green + integration data

**Files:**
- Create: `tests/data/reversed_20.json`
- Create: `tests/io/test_data_fixtures.py`

- [ ] **Step 1: Create fixture data file `tests/data/reversed_20.json`**

```json
{
  "version": 1,
  "size": 20,
  "fill": "reversed",
  "data": [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
}
```

- [ ] **Step 2: Write the integration test**

```python
from pathlib import Path

from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.runner import Timeline, record
from sorting_visualizer.io.array_store import load

DATA = Path(__file__).resolve().parents[1] / "data" / "reversed_20.json"


def test_loaded_fixture_sorts_with_every_algorithm():
    loaded = load(DATA)
    for name, fn in ALGORITHMS.items():
        tl = Timeline(record(fn, loaded.data))
        while tl.step_forward():
            pass
        assert tl.state.data == sorted(loaded.data), name
```

- [ ] **Step 3: Run the full suite**

Run: `.venv/Scripts/python -m pytest`
Expected: PASS — all tests across `tests/core`, `tests/io`, `tests/ui` green.

- [ ] **Step 4: Commit**

```bash
git add tests/data/reversed_20.json tests/io/test_data_fixtures.py
git commit -m "test: add end-to-end fixture integration test" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Push**

```bash
git push
```

---

## Self-Review (completed by plan author)

**Spec coverage:**
- 4 algorithms (bubble/insertion/merge/quick) → Tasks 3–6. ✅
- Step animation of comparisons/swaps → events + runner + bar widget (Tasks 1, 9, 13). ✅
- Step forward **and** back → Timeline (Task 10), wired in Task 15. ✅
- Race mode, all 4, one shared array, one timer → Task 16. ✅
- Size + fill (random/reversed/nearly_sorted) → fill (Task 2), controls (Task 14), main window (Task 17). ✅
- Operation counters → stats (Task 8), shown in Tasks 15–16. ✅
- File storage: array↔JSON, stats→CSV → Tasks 11–12, wired in Task 17. ✅
- Error handling (ArrayLoadError, OSError → QMessageBox; spinbox bounds) → Tasks 11, 17, 14. ✅
- Unit tests (core), integration/UI tests (pytest-qt), test data → all tasks + Task 20. ✅
- Docker with headless tests in build → Task 19. ✅

**Placeholder scan:** No TBD/TODO; every code step contains full code. ✅

**Type consistency:** `State` (data/sorted_idx/highlight/highlight_kind), `Recording` (initial/events/elapsed_ms/stats), `Stats` (comparisons/writes), `StatsRow` (algorithm/size/fill/comparisons/writes/time_ms), `Timeline` (index/state/step_forward/step_back/reset/at_end/length), `ALGORITHMS` dict — all names used consistently across Tasks 9–20. ✅
