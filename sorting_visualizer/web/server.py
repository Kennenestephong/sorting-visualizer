from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from ..core.algorithms import ALGORITHMS
from ..core.fill import FillMode, generate
from ..core.runner import record
from ..io.array_store import MIN_SIZE, MAX_SIZE, ArrayLoadError
from ..io.stats_export import StatsRow
from . import storage
from .serialization import recording_to_dict

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Sorting Visualizer")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


class GenerateRequest(BaseModel):
    size: int = Field(ge=MIN_SIZE, le=MAX_SIZE)
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


class SaveRequest(BaseModel):
    data: list[int] = Field(min_length=MIN_SIZE, max_length=MAX_SIZE)
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


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
