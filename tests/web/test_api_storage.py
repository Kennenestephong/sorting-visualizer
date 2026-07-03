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


def test_save_rejects_size_out_of_range(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_DIR", str(tmp_path))
    r = client.put("/api/arrays/tiny", json={"data": [1, 2, 3], "fill": "random"})
    assert r.status_code == 422
