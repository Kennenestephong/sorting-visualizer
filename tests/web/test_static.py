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
