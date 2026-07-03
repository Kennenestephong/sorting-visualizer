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
