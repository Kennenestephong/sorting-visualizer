# Web Sorting Visualizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a web frontend (FastAPI + vanilla JS/Canvas) over the existing Qt-free `core`/`io`, with server-side JSON/CSV storage, served by Docker — without touching the desktop PySide6 version.

**Architecture:** New `sorting_visualizer/web/` package: a FastAPI server exposes the algorithm engine as JSON (a full event log per recording); the browser replays that log with a small JS mirror of the Python `Timeline`, drawing bars on a `<canvas>`. Reuses `core/` and `io/` unchanged. Docker switches to running the web server (uvicorn), needing no Qt libs or X server.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, httpx (TestClient), pytest; vanilla HTML/CSS/JS + Canvas.

**Design spec:** `docs/superpowers/specs/2026-07-02-web-sorting-visualizer-design.md`

**Environment (Windows):** use the existing venv Python `.venv/Scripts/python.exe` for all commands. The desktop deps are already installed; this plan adds web deps.

**Convention:** Every commit ends with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` (shown in each commit step).

**Do NOT touch:** `sorting_visualizer/ui/`, `sorting_visualizer/app.py`, or the existing 72 tests.

---

## File Structure

```
sorting_visualizer/web/
  __init__.py
  serialization.py     # Event/Recording <-> dict (pure, no FastAPI)
  storage.py           # server-side data/ dir: list/save/load arrays, export CSV (wraps io/)
  server.py            # FastAPI app: routes + static mount + main()
  static/
    index.html
    styles.css
    app.js
tests/web/
  __init__.py
  test_serialization.py
  test_storage.py
  test_api_engine.py     # /api/generate, /api/record, /api/race
  test_api_storage.py    # /api/arrays list/save/load, /api/export-stats
  test_static.py         # GET / and /static/app.js smoke
requirements-web.txt
Dockerfile               # MODIFIED -> web image
.dockerignore            # MODIFIED -> add data/
README.md                # MODIFIED -> add Web section
```

---

## Task 1: Web package scaffold + dependencies

**Files:**
- Create: `requirements-web.txt`, `sorting_visualizer/web/__init__.py`, `sorting_visualizer/web/static/.gitkeep`, `tests/web/__init__.py`

- [ ] **Step 1: Create `requirements-web.txt`**

```
fastapi>=0.110
uvicorn[standard]>=0.29
httpx>=0.27
pytest>=8
```

- [ ] **Step 2: Create empty package files**

Create as empty (0-byte) files: `sorting_visualizer/web/__init__.py`, `tests/web/__init__.py`, and `sorting_visualizer/web/static/.gitkeep`.

- [ ] **Step 3: Install web deps into the existing venv**

Run:
```
.venv/Scripts/python.exe -m pip install -r requirements-web.txt
```
Expected: fastapi, uvicorn, httpx install successfully.

- [ ] **Step 4: Verify imports**

Run:
```
.venv/Scripts/python.exe -c "import fastapi, uvicorn, httpx; print('web deps ok')"
```
Expected: prints `web deps ok`.

- [ ] **Step 5: Commit**

```bash
git add requirements-web.txt sorting_visualizer/web tests/web
git commit -m "chore: scaffold web package and dependencies" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Event/Recording serialization

**Files:**
- Create: `sorting_visualizer/web/serialization.py`
- Test: `tests/web/test_serialization.py`

- [ ] **Step 1: Write the failing test**

```python
from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.runner import record
from sorting_visualizer.web.serialization import (
    event_from_dict,
    event_to_dict,
    recording_to_dict,
)


def test_event_roundtrip_all_types():
    events = [Compare(0, 1), Swap(2, 3), Overwrite(4, 9, 5), MarkSorted(6)]
    for e in events:
        assert event_from_dict(event_to_dict(e)) == e


def test_event_to_dict_shapes():
    assert event_to_dict(Compare(0, 1)) == {"type": "compare", "i": 0, "j": 1}
    assert event_to_dict(Swap(0, 1)) == {"type": "swap", "i": 0, "j": 1}
    assert event_to_dict(Overwrite(2, 9, 5)) == {"type": "overwrite", "i": 2, "value": 9, "old": 5}
    assert event_to_dict(MarkSorted(3)) == {"type": "marksorted", "i": 3}


def test_recording_to_dict_structure():
    rec = record(ALGORITHMS["bubble"], [3, 1, 2])
    d = recording_to_dict(rec)
    assert d["initial"] == [3, 1, 2]
    assert isinstance(d["events"], list) and d["events"]
    assert set(d["stats"]) == {"comparisons", "writes"}
    assert d["elapsed_ms"] >= 0.0


def test_recording_events_replay_to_sorted_via_dicts():
    rec = record(ALGORITHMS["merge"], [5, 3, 4, 1, 2])
    d = recording_to_dict(rec)
    arr = list(d["initial"])
    for ed in d["events"]:
        e = event_from_dict(ed)
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
        elif isinstance(e, Overwrite):
            arr[e.i] = e.value
    assert arr == sorted(d["initial"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_serialization.py -v`
Expected: FAIL — `ModuleNotFoundError: sorting_visualizer.web.serialization`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/web/serialization.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_serialization.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/web/serialization.py tests/web/test_serialization.py
git commit -m "feat: add web event/recording serialization" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Server-side storage

**Files:**
- Create: `sorting_visualizer/web/storage.py`
- Test: `tests/web/test_storage.py`

- [ ] **Step 1: Write the failing test**

```python
import csv

import pytest

from sorting_visualizer.io.array_store import ArrayLoadError
from sorting_visualizer.io.stats_export import StatsRow
from sorting_visualizer.web import storage


def test_save_then_load_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    data = list(range(1, 21))
    storage.save_array("myarr", data, "random")
    assert storage.list_arrays() == ["myarr"]
    loaded = storage.load_array("myarr")
    assert loaded.data == data
    assert loaded.fill == "random"


def test_load_missing_raises_array_load_error(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    with pytest.raises(ArrayLoadError):
        storage.load_array("nope")


def test_invalid_name_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    with pytest.raises(storage.InvalidName):
        storage.save_array("../evil", [1] * 12, "random")
    with pytest.raises(storage.InvalidName):
        storage.load_array("bad name")


def test_export_stats_writes_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    rows = [StatsRow("bubble", 20, "random", 100, 50, 1.2)]
    path = storage.export_stats(rows)
    assert path.exists()
    assert path.parent == tmp_path / "exports"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "algorithm,size,fill,comparisons,writes,time_ms"
    assert lines[1] == "bubble,20,random,100,50,1.2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/web/storage.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_storage.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/web/storage.py tests/web/test_storage.py
git commit -m "feat: add server-side array/stats storage" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Engine API endpoints (generate / record / race)

**Files:**
- Create: `sorting_visualizer/web/server.py`
- Test: `tests/web/test_api_engine.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.web.serialization import event_from_dict
from sorting_visualizer.web.server import app

client = TestClient(app)


def _replay(initial, events):
    from sorting_visualizer.core.events import Overwrite, Swap

    arr = list(initial)
    for ed in events:
        e = event_from_dict(ed)
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
        elif isinstance(e, Overwrite):
            arr[e.i] = e.value
    return arr


def test_generate_returns_array_of_size():
    r = client.post("/api/generate", json={"size": 30, "fill": "random"})
    assert r.status_code == 200
    assert len(r.json()["data"]) == 30


def test_generate_rejects_bad_size():
    assert client.post("/api/generate", json={"size": 5, "fill": "random"}).status_code == 422


def test_generate_rejects_unknown_fill():
    assert client.post("/api/generate", json={"size": 20, "fill": "bogus"}).status_code == 422


def test_record_events_replay_to_sorted_for_each_algorithm():
    data = [5, 3, 4, 1, 2, 9, 0]
    for name in ALGORITHMS:
        r = client.post("/api/record", json={"algorithm": name, "data": data})
        assert r.status_code == 200, name
        body = r.json()
        assert _replay(body["initial"], body["events"]) == sorted(data), name
        assert body["stats"]["comparisons"] >= 0


def test_record_unknown_algorithm_404():
    r = client.post("/api/record", json={"algorithm": "nope", "data": [1, 2, 3]})
    assert r.status_code == 404


def test_race_returns_all_four_recordings():
    data = [5, 3, 4, 1, 2]
    r = client.post("/api/race", json={"data": data})
    assert r.status_code == 200
    recs = r.json()["recordings"]
    assert set(recs) == set(ALGORITHMS)
    for name, rec in recs.items():
        assert _replay(rec["initial"], rec["events"]) == sorted(data), name
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_api_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: sorting_visualizer.web.server`

- [ ] **Step 3: Write minimal implementation**

`sorting_visualizer/web/server.py`:
```python
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from ..core.algorithms import ALGORITHMS
from ..core.fill import FillMode, generate
from ..core.runner import record
from ..io.array_store import ArrayLoadError
from ..io.stats_export import StatsRow
from . import storage
from .serialization import recording_to_dict

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Sorting Visualizer")


class GenerateRequest(BaseModel):
    size: int = Field(ge=10, le=200)
    fill: str
    seed: int | None = None

    @field_validator("fill")
    @classmethod
    def _validate_fill(cls, v: str) -> str:
        try:
            FillMode(v)
        except ValueError as exc:
            raise ValueError(f"unknown fill: {v}") from exc
        return v


class RecordRequest(BaseModel):
    algorithm: str
    data: list[int]


class RaceRequest(BaseModel):
    data: list[int]


@app.post("/api/generate")
def api_generate(req: GenerateRequest) -> dict:
    return {"data": generate(req.size, FillMode(req.fill), seed=req.seed)}


@app.post("/api/record")
def api_record(req: RecordRequest) -> dict:
    if req.algorithm not in ALGORITHMS:
        raise HTTPException(status_code=404, detail=f"unknown algorithm: {req.algorithm}")
    return recording_to_dict(record(ALGORITHMS[req.algorithm], req.data))


@app.post("/api/race")
def api_race(req: RaceRequest) -> dict:
    return {
        "recordings": {
            name: recording_to_dict(record(fn, req.data)) for name, fn in ALGORITHMS.items()
        }
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_api_engine.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/web/server.py tests/web/test_api_engine.py
git commit -m "feat: add engine API (generate/record/race)" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Storage & export API endpoints

**Files:**
- Modify: `sorting_visualizer/web/server.py` (add storage/export routes)
- Test: `tests/web/test_api_storage.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from sorting_visualizer.web.server import app

client = TestClient(app)


def test_save_list_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    data = list(range(1, 21))
    assert client.put("/api/arrays/demo", json={"data": data, "fill": "random"}).status_code == 200
    assert client.get("/api/arrays").json()["names"] == ["demo"]
    body = client.get("/api/arrays/demo").json()
    assert body["data"] == data and body["fill"] == "random"


def test_load_missing_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    assert client.get("/api/arrays/ghost").status_code == 404


def test_invalid_name_returns_400(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    r = client.put("/api/arrays/bad%20name", json={"data": [1] * 12, "fill": "random"})
    assert r.status_code == 400


def test_export_stats_returns_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    rows = [
        {"algorithm": "bubble", "size": 20, "fill": "random",
         "comparisons": 100, "writes": 50, "time_ms": 1.2},
    ]
    r = client.post("/api/export-stats", json={"rows": rows})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.content.decode("utf-8")
    assert text.splitlines()[0] == "algorithm,size,fill,comparisons,writes,time_ms"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_api_storage.py -v`
Expected: FAIL — 404s (routes not defined yet)

- [ ] **Step 3: Add the routes to `server.py`**

Add these model classes after `RaceRequest` and these routes after `api_race` (before `def main()`):
```python
class SaveRequest(BaseModel):
    data: list[int]
    fill: str


class StatsRowModel(BaseModel):
    algorithm: str
    size: int
    fill: str
    comparisons: int
    writes: int
    time_ms: float


class ExportRequest(BaseModel):
    rows: list[StatsRowModel]


@app.get("/api/arrays")
def api_list_arrays() -> dict:
    return {"names": storage.list_arrays()}


@app.put("/api/arrays/{name}")
def api_save_array(name: str, req: SaveRequest) -> dict:
    try:
        storage.save_array(name, req.data, req.fill)
    except storage.InvalidName as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.get("/api/arrays/{name}")
def api_load_array(name: str) -> dict:
    try:
        loaded = storage.load_array(name)
    except storage.InvalidName as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ArrayLoadError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data": loaded.data, "fill": loaded.fill}


@app.post("/api/export-stats")
def api_export_stats(req: ExportRequest) -> FileResponse:
    rows = [StatsRow(**row.model_dump()) for row in req.rows]
    path = storage.export_stats(rows)
    return FileResponse(path, media_type="text/csv", filename=path.name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_api_storage.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/web/server.py tests/web/test_api_storage.py
git commit -m "feat: add storage and CSV export API" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Frontend (static files) + static serving

**Files:**
- Modify: `sorting_visualizer/web/server.py` (mount static + serve index at `/`)
- Create: `sorting_visualizer/web/static/index.html`, `styles.css`, `app.js`
- Delete: `sorting_visualizer/web/static/.gitkeep` (no longer needed)
- Test: `tests/web/test_static.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from sorting_visualizer.web.server import app

client = TestClient(app)


def test_index_served_at_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Sorting Visualizer" in r.text


def test_app_js_served():
    r = client.get("/static/app.js")
    assert r.status_code == 200
    assert "Timeline" in r.text


def test_styles_served():
    assert client.get("/static/styles.css").status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_static.py -v`
Expected: FAIL — 404 (no `/` route, no static mount)

- [ ] **Step 3a: Add static serving to `server.py`**

Add the index route immediately after `app = FastAPI(...)`:
```python
@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")
```
And add this at the END of the file, just before `def main()`:
```python
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

- [ ] **Step 3b: Create `sorting_visualizer/web/static/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sorting Visualizer</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <h1>Sorting Visualizer</h1>

  <div class="tabs">
    <button id="tab-single" class="tab active">Single</button>
    <button id="tab-race" class="tab">Race</button>
  </div>

  <div class="controls">
    <button id="play">Play</button>
    <button id="stepBack">&lt; Step</button>
    <button id="stepFwd">Step &gt;</button>
    <button id="reset">Reset</button>
    <label>Speed <input id="speed" type="range" min="5" max="500" value="60" /></label>
    <label>Size <input id="size" type="number" min="10" max="200" value="50" /></label>
    <label>Fill
      <select id="fill">
        <option value="random">random</option>
        <option value="reversed">reversed</option>
        <option value="nearly_sorted">nearly_sorted</option>
      </select>
    </label>
    <label class="single-only">Algorithm
      <select id="algo">
        <option value="bubble">bubble</option>
        <option value="insertion">insertion</option>
        <option value="merge">merge</option>
        <option value="quick">quick</option>
      </select>
    </label>
    <button id="save">Save</button>
    <button id="load">Load</button>
    <button id="export">Export CSV</button>
  </div>

  <div id="single-view" class="view">
    <canvas id="single-canvas" width="960" height="480"></canvas>
    <div id="single-stats" class="stats"></div>
  </div>

  <div id="race-view" class="view hidden">
    <div class="race-grid">
      <div><h3>bubble</h3><canvas class="race-canvas" data-algo="bubble" width="470" height="240"></canvas><div class="stats" data-algo="bubble"></div></div>
      <div><h3>insertion</h3><canvas class="race-canvas" data-algo="insertion" width="470" height="240"></canvas><div class="stats" data-algo="insertion"></div></div>
      <div><h3>merge</h3><canvas class="race-canvas" data-algo="merge" width="470" height="240"></canvas><div class="stats" data-algo="merge"></div></div>
      <div><h3>quick</h3><canvas class="race-canvas" data-algo="quick" width="470" height="240"></canvas><div class="stats" data-algo="quick"></div></div>
    </div>
  </div>

  <div id="error" class="error hidden"></div>

  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 3c: Create `sorting_visualizer/web/static/styles.css`**

```css
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; margin: 16px; color: #222; }
h1 { font-size: 20px; }
.tabs { margin-bottom: 8px; }
.tab { padding: 6px 14px; border: 1px solid #ccc; background: #f4f4f4; cursor: pointer; }
.tab.active { background: #ddd; font-weight: bold; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 10px 0; }
.controls button, .controls select, .controls input { padding: 4px 8px; }
.view.hidden { display: none; }
canvas { border: 1px solid #ddd; background: #fafafa; width: 100%; height: auto; }
.race-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.race-grid h3 { margin: 4px 0; font-size: 14px; }
.stats { font-size: 13px; color: #555; margin-top: 4px; }
.error { color: #b00; margin-top: 10px; }
.error.hidden { display: none; }
.hidden { display: none; }
```

- [ ] **Step 3d: Create `sorting_visualizer/web/static/app.js`**

```javascript
"use strict";

const COLORS = { normal: "#B0B0B0", compare: "#F2C037", move: "#E5484D", sorted: "#46A758" };

async function api(path, body, method) {
  const opts = { method: method || (body ? "POST" : "GET"), headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = res.status + " " + res.statusText;
    try { const j = await res.json(); if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch (e) {}
    throw new Error(msg);
  }
  return res.json();
}

function showError(err) {
  const el = document.getElementById("error");
  el.textContent = "Error: " + err.message;
  el.classList.remove("hidden");
}
function clearError() { document.getElementById("error").classList.add("hidden"); }

class Timeline {
  constructor(recording) { this.rec = recording; this.reset(); }
  get length() { return this.rec.events.length; }
  get atEnd() { return this.index >= this.length; }
  reset() {
    this.index = 0;
    this.state = { data: this.rec.initial.slice(), sorted: new Set(), highlight: [], kind: "" };
  }
  _apply(e) {
    const s = this.state;
    if (e.type === "compare") { s.highlight = [e.i, e.j]; s.kind = "compare"; }
    else if (e.type === "swap") { const t = s.data[e.i]; s.data[e.i] = s.data[e.j]; s.data[e.j] = t; s.highlight = [e.i, e.j]; s.kind = "move"; }
    else if (e.type === "overwrite") { s.data[e.i] = e.value; s.highlight = [e.i]; s.kind = "move"; }
    else if (e.type === "marksorted") { s.sorted.add(e.i); s.highlight = []; s.kind = ""; }
  }
  _revert(e) {
    const s = this.state;
    if (e.type === "swap") { const t = s.data[e.i]; s.data[e.i] = s.data[e.j]; s.data[e.j] = t; }
    else if (e.type === "overwrite") { s.data[e.i] = e.old; }
    else if (e.type === "marksorted") { s.sorted.delete(e.i); }
    s.highlight = []; s.kind = "";
  }
  stepForward() { if (this.atEnd) return false; this._apply(this.rec.events[this.index]); this.index++; return true; }
  stepBack() { if (this.index <= 0) return false; this.index--; this._revert(this.rec.events[this.index]); return true; }
}

function role(i, state) {
  if (state.sorted.has(i)) return "sorted";
  if (state.highlight.includes(i)) return state.kind || "normal";
  return "normal";
}

function drawBars(canvas, state) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const data = state.data, n = data.length;
  if (!n) return;
  const maxv = Math.max.apply(null, data) || 1;
  const bw = w / n;
  for (let i = 0; i < n; i++) {
    const bh = (data[i] / maxv) * h;
    ctx.fillStyle = COLORS[role(i, state)];
    ctx.fillRect(i * bw, h - bh, Math.max(1, bw - 1), bh);
  }
}

// ---- shared UI state ----
const els = {};
["play", "stepBack", "stepFwd", "reset", "speed", "size", "fill", "algo",
 "save", "load", "export", "tab-single", "tab-race",
 "single-view", "race-view", "single-canvas", "single-stats"].forEach((id) => { els[id] = document.getElementById(id); });

let currentData = [];
let currentFill = "random";
let mode = "single";              // "single" | "race"
let single = null;                // Timeline
let race = {};                    // {name: Timeline}
let timer = null;

function statsText(rec) {
  return `comparisons: ${rec.stats.comparisons}  writes: ${rec.stats.writes}  time: ${rec.elapsed_ms.toFixed(1)} ms`;
}

function renderSingle() {
  if (!single) return;
  drawBars(els["single-canvas"], single.state);
  els["single-stats"].textContent = statsText(single.rec);
}

function renderRace() {
  document.querySelectorAll(".race-canvas").forEach((c) => {
    const tl = race[c.dataset.algo];
    if (tl) drawBars(c, tl.state);
  });
  document.querySelectorAll(".stats[data-algo]").forEach((d) => {
    const tl = race[d.dataset.algo];
    if (tl) d.textContent = `${d.dataset.algo}: ${tl.index} ops / ${tl.length}`;
  });
}

function render() { mode === "single" ? renderSingle() : renderRace(); }

function stopPlay() {
  if (timer) { clearInterval(timer); timer = null; }
  els.play.textContent = "Play";
}

function tick() {
  if (mode === "single") {
    if (!single.stepForward()) { stopPlay(); return; }
  } else {
    const anyMoved = Object.values(race).map((tl) => tl.stepForward()).some(Boolean);
    if (!anyMoved) { stopPlay(); return; }
  }
  render();
}

function togglePlay() {
  if (timer) { stopPlay(); return; }
  els.play.textContent = "Pause";
  timer = setInterval(tick, parseInt(els.speed.value, 10));
}

async function rebuild() {
  clearError();
  try {
    if (mode === "single") {
      single = new Timeline(await api("/api/record", { algorithm: els.algo.value, data: currentData }));
    } else {
      const resp = await api("/api/race", { data: currentData });
      race = {};
      for (const name of Object.keys(resp.recordings)) race[name] = new Timeline(resp.recordings[name]);
    }
    render();
  } catch (err) { showError(err); }
}

async function regenerate() {
  clearError();
  try {
    const resp = await api("/api/generate", { size: parseInt(els.size.value, 10), fill: els.fill.value });
    currentData = resp.data;
    currentFill = els.fill.value;
    await rebuild();
  } catch (err) { showError(err); }
}

function collectStatsRows() {
  const size = currentData.length;
  if (mode === "single") {
    const s = single.rec;
    return [{ algorithm: els.algo.value, size, fill: currentFill,
              comparisons: s.stats.comparisons, writes: s.stats.writes, time_ms: s.elapsed_ms }];
  }
  return Object.keys(race).map((name) => {
    const s = race[name].rec;
    return { algorithm: name, size, fill: currentFill,
             comparisons: s.stats.comparisons, writes: s.stats.writes, time_ms: s.elapsed_ms };
  });
}

// ---- event wiring ----
els.play.onclick = () => togglePlay();
els.stepFwd.onclick = () => { stopPlay(); mode === "single" ? single.stepForward() : Object.values(race).forEach((t) => t.stepForward()); render(); };
els.stepBack.onclick = () => { stopPlay(); mode === "single" ? single.stepBack() : Object.values(race).forEach((t) => t.stepBack()); render(); };
els.reset.onclick = () => { stopPlay(); mode === "single" ? single.reset() : Object.values(race).forEach((t) => t.reset()); render(); };
els.speed.onchange = () => { if (timer) { stopPlay(); togglePlay(); } };
els.size.onchange = () => regenerate();
els.fill.onchange = () => regenerate();
els.algo.onchange = () => { stopPlay(); rebuild(); };

els["tab-single"].onclick = () => switchMode("single");
els["tab-race"].onclick = () => switchMode("race");

function switchMode(m) {
  stopPlay();
  mode = m;
  els["tab-single"].classList.toggle("active", m === "single");
  els["tab-race"].classList.toggle("active", m === "race");
  els["single-view"].classList.toggle("hidden", m !== "single");
  els["race-view"].classList.toggle("hidden", m !== "race");
  document.querySelectorAll(".single-only").forEach((e) => e.classList.toggle("hidden", m !== "single"));
  rebuild();
}

els.save.onclick = async () => {
  const name = prompt("Save array as (letters/digits/_/- only):");
  if (!name) return;
  clearError();
  try { await api("/api/arrays/" + encodeURIComponent(name), { data: currentData, fill: currentFill }, "PUT"); }
  catch (err) { showError(err); }
};

els.load.onclick = async () => {
  clearError();
  try {
    const list = (await api("/api/arrays")).names;
    if (!list.length) { alert("No saved arrays."); return; }
    const name = prompt("Load which array?\n" + list.join(", "), list[0]);
    if (!name) return;
    const body = await api("/api/arrays/" + encodeURIComponent(name));
    currentData = body.data;
    currentFill = body.fill;
    els.size.value = currentData.length;
    if (["random", "reversed", "nearly_sorted"].includes(body.fill)) els.fill.value = body.fill;
    await rebuild();
  } catch (err) { showError(err); }
};

els.export.onclick = async () => {
  clearError();
  try {
    const res = await fetch("/api/export-stats", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows: collectStatsRows() }),
    });
    if (!res.ok) throw new Error(res.status + " " + res.statusText);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "stats.csv"; a.click();
    URL.revokeObjectURL(url);
  } catch (err) { showError(err); }
};

// ---- boot ----
regenerate();
```

- [ ] **Step 3e: Remove the placeholder**

```bash
git rm sorting_visualizer/web/static/.gitkeep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/web/test_static.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add sorting_visualizer/web/server.py sorting_visualizer/web/static tests/web/test_static.py
git commit -m "feat: add web frontend and static serving" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Docker (web image) + README

**Files:**
- Modify: `Dockerfile` (replace desktop-oriented build with web)
- Modify: `.dockerignore` (add `data`)
- Modify: `README.md` (add Web section)

- [ ] **Step 1: Replace `Dockerfile` with the web build**

Overwrite `Dockerfile` with:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY . .

# Run the web-relevant tests headless as part of the build (no Qt needed).
RUN python -m pytest tests/core tests/io tests/web

EXPOSE 8000
CMD ["uvicorn", "sorting_visualizer.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Add `data` to `.dockerignore`**

Append a line `data` to `.dockerignore` (so local saved arrays/exports aren't copied into the image). Resulting file:
```
.git
.venv
venv
__pycache__
*.pyc
.pytest_cache
docs
variants.pdf
data
```

- [ ] **Step 3: Add a Web section to `README.md`**

Append to `README.md`:
````markdown
## Web version

A browser UI over the same core (FastAPI + vanilla JS/Canvas). Full parity with the
desktop app: single-algorithm view, 4-way race, step forward/back, server-side JSON
array storage and CSV export.

### Run locally

```bash
.venv/bin/python -m pip install -r requirements-web.txt   # Windows: .venv/Scripts/python.exe
.venv/bin/python -m uvicorn sorting_visualizer.web.server:app --reload
```
Open http://localhost:8000

### Docker (recommended for the web app — no X server needed)

```bash
docker build -t sorting-visualizer-web .
docker run -p 8000:8000 sorting-visualizer-web
```
Open http://localhost:8000

Saved arrays and exported CSVs live under `data/` (override with `SV_DATA_DIR`).
````

- [ ] **Step 4: Verify the web-relevant suite passes (what the image runs)**

Run: `.venv/Scripts/python.exe -m pytest tests/core tests/io tests/web -q`
Expected: PASS (all core + io + web tests green).

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore README.md
git commit -m "chore: switch Docker to web server; document web version" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Full verification + manual run + push

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite (desktop + web, nothing regressed)**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: PASS — the original 72 tests plus the new web tests, all green.

- [ ] **Step 2: Smoke-run the server and hit it**

Start the server in the background:
```
.venv/Scripts/python.exe -m uvicorn sorting_visualizer.web.server:app --port 8011
```
Then in another shell verify:
```
.venv/Scripts/python.exe -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8011/').status)"
```
Expected: `200`. Then stop the server.

(If Docker is running, optionally: `docker build -t sorting-visualizer-web . && docker run -d -p 8000:8000 sorting-visualizer-web`, open http://localhost:8000, confirm the bars render and a race runs, then stop the container.)

- [ ] **Step 3: Push the branch**

```bash
git push -u origin feat/web-visualizer
```

---

## Self-Review (completed by plan author)

**Spec coverage:**
- Reuse core/io unchanged → all tasks import from `..core`/`..io`; desktop untouched. ✅
- Serialization (Event/Recording ↔ dict) → Task 2. ✅
- Server-side storage (arrays JSON, CSV export, `SV_DATA_DIR`, name sanitization) → Task 3. ✅
- Engine API (generate/record/race) with validation + 404/422 → Task 4. ✅
- Storage/export API with 400/404 error mapping → Task 5. ✅
- Frontend: tabs, controls (play/step±/reset/speed/size/fill/algo), JS Timeline mirror, Canvas role colors, race 4 canvases, save/load/export → Task 6. ✅
- Docker runs web (uvicorn), Qt-free image, runs core+io+web tests in build; README web section → Task 7. ✅
- Contract test (recorded events replay to sorted) → Tasks 2 & 4. ✅
- Full-suite regression + manual run + push → Task 8. ✅

**Placeholder scan:** No TBD/TODO; every code step has complete code. ✅

**Type consistency:** Endpoints and payload keys match between backend (`recording_to_dict` → `initial`/`events`/`stats`/`elapsed_ms`; `/api/arrays`, `/api/record` {algorithm,data}; `/api/export-stats` {rows:[{algorithm,size,fill,comparisons,writes,time_ms}]}) and the frontend `app.js` fetch calls and `collectStatsRows()`. `StatsRowModel` fields match `io.stats_export.StatsRow`. JS `Timeline` apply/revert mirror the Python `runner` semantics (swap/overwrite/marksorted/compare). ✅
