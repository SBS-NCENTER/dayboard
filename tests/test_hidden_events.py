from dayboard import hidden_events


def test_load_missing_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(hidden_events, "_PATH", tmp_path / "nope.json")
    assert hidden_events.load() == set()


def test_save_load_round_trip(tmp_path, monkeypatch):
    p = tmp_path / "hidden.json"
    monkeypatch.setattr(hidden_events, "_PATH", p)
    hidden_events.save(["2026-08-12", "2026-08-28", "2026-08-12"])  # 중복 포함
    assert hidden_events.load() == {"2026-08-12", "2026-08-28"}  # dedup


def test_load_corrupt_is_empty(tmp_path, monkeypatch):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(hidden_events, "_PATH", p)
    assert hidden_events.load() == set()
