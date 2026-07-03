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
