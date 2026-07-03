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
