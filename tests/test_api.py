from dayboard import hidden_events
from dayboard.server import routes
from dayboard.server.app import create_app


def test_api_data_shape_weather_ok(monkeypatch):
    monkeypatch.setattr(
        routes.api.weather,
        "get_weather",
        lambda *a, **k: {
            "temp": 30.4,
            "humidity": 71,
            "wind": 5.4,
            "code": 1,
            "label": "대체로 맑음",
            "tmax": 30.4,
            "tmin": 24.4,
        },
    )
    c = create_app().test_client()
    d = c.get("/api/data").get_json()
    assert set(d) == {"location", "today", "calendar", "weather", "sun_moon", "events"}
    assert d["weather"]["temp"] == 30.4
    assert d["calendar"]["weeks"] and d["sun_moon"]["sunrise"]


def test_api_data_weather_failure_null_but_offline_panes_present(monkeypatch):
    monkeypatch.setattr(routes.api.weather, "get_weather", lambda *a, **k: None)
    c = create_app().test_client()
    d = c.get("/api/data").get_json()
    assert d["weather"] is None  # 상류 실패
    assert d["calendar"]["weeks"] and d["sun_moon"]["sunset"]  # 오프라인 pane 정상


def test_api_data_one_module_failure_degrades_only_its_pane(monkeypatch):
    def boom(*a, **k):
        raise ValueError("polar latitude")

    monkeypatch.setattr(routes.api.astro, "sun_moon", boom)
    monkeypatch.setattr(routes.api.weather, "get_weather", lambda *a, **k: None)
    c = create_app().test_client()
    r = c.get("/api/data")
    assert r.status_code == 200
    d = r.get_json()
    assert d["sun_moon"] is None
    assert d["calendar"]["weeks"] and d["events"] is not None  # other panes survive


def test_api_data_excludes_hidden(monkeypatch, tmp_path):
    monkeypatch.setattr(hidden_events, "_PATH", tmp_path / "h.json")
    hidden_events.save(["2026-08-12"])
    monkeypatch.setattr(
        routes.api.astro,
        "upcoming_events",
        lambda *a, **k: [
            {"date": "2026-08-12", "name": "숨김", "type": "x", "note": ""},
            {"date": "2026-09-01", "name": "표시", "type": "x", "note": ""},
        ],
    )
    monkeypatch.setattr(routes.api.weather, "get_weather", lambda *a, **k: None)
    d = create_app().test_client().get("/api/data").get_json()
    dates = [e["date"] for e in d["events"]]
    assert "2026-08-12" not in dates and "2026-09-01" in dates


def test_api_events_lists_all_with_hidden_flag(monkeypatch, tmp_path):
    monkeypatch.setattr(hidden_events, "_PATH", tmp_path / "h.json")
    hidden_events.save(["2026-08-12"])
    monkeypatch.setattr(
        routes.api.astro,
        "upcoming_events",
        lambda *a, **k: [
            {"date": "2026-08-12", "name": "a", "type": "x", "note": ""},
            {"date": "2026-09-01", "name": "b", "type": "x", "note": ""},
        ],
    )
    r = create_app().test_client().get("/api/events").get_json()
    by_date = {e["date"]: e["hidden"] for e in r}
    assert by_date == {"2026-08-12": True, "2026-09-01": False}


def test_api_post_hidden_persists_and_reflects(monkeypatch, tmp_path):
    monkeypatch.setattr(hidden_events, "_PATH", tmp_path / "h.json")
    monkeypatch.setattr(
        routes.api.astro,
        "upcoming_events",
        lambda *a, **k: [{"date": "2026-09-01", "name": "b", "type": "x", "note": ""}],
    )
    monkeypatch.setattr(routes.api.weather, "get_weather", lambda *a, **k: None)
    c = create_app().test_client()
    assert c.post("/api/events/hidden", json={"hidden": ["2026-09-01"]}).status_code == 200
    assert hidden_events.load() == {"2026-09-01"}
    assert c.get("/api/data").get_json()["events"] == []  # 숨김 반영


def test_api_post_hidden_bad_body_400(monkeypatch, tmp_path):
    monkeypatch.setattr(hidden_events, "_PATH", tmp_path / "h.json")
    c = create_app().test_client()
    assert c.post("/api/events/hidden", json={"nope": 1}).status_code == 400
    assert hidden_events.load() == set()
