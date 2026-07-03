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

## Docker (desktop)

The desktop GUI has its own image, `Dockerfile.desktop` (the default `Dockerfile` builds
the web version — see below). Build (runs the full test suite as part of the build):

```bash
docker build -f Dockerfile.desktop -t sorting-visualizer-desktop .
```

Run the GUI — a desktop app needs the host display forwarded into the container:

- **Linux:**
  ```bash
  xhost +local:docker
  docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix sorting-visualizer-desktop
  ```
- **Windows / macOS:** run an X server (VcXsrv / XQuartz), then:
  ```bash
  docker run --rm -e DISPLAY=host.docker.internal:0 sorting-visualizer-desktop
  ```

Headless smoke run (no window, verifies it boots):

```bash
docker run --rm -e QT_QPA_PLATFORM=offscreen sorting-visualizer-desktop
```

## File formats

- **Array (JSON):** `{"version": 1, "size": 50, "fill": "random", "data": [...]}`
- **Stats (CSV):** `algorithm,size,fill,comparisons,writes,time_ms`

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

The default `Dockerfile` builds the web app:

```bash
docker build -t sorting-visualizer-web .
docker run -p 8000:8000 sorting-visualizer-web
```
Open http://localhost:8000

Saved arrays and exported CSVs live under `data/` (override with `SV_DATA_DIR`).
