from dayboard.server import routes
from dayboard.server.app import create_app


def test_api_data_shape_weather_ok(monkeypatch):
    monkeypatch.setattr(routes.api.weather, "get_weather",
                        lambda *a, **k: {"temp": 30.4, "humidity": 71, "wind": 5.4,
                                         "code": 1, "label": "대체로 맑음", "tmax": 30.4, "tmin": 24.4})
    c = create_app().test_client()
    d = c.get("/api/data").get_json()
    assert set(d) == {"location", "today", "calendar", "weather", "sun_moon", "events"}
    assert d["weather"]["temp"] == 30.4
    assert d["calendar"]["weeks"] and d["sun_moon"]["sunrise"]


def test_api_data_weather_failure_null_but_offline_panes_present(monkeypatch):
    monkeypatch.setattr(routes.api.weather, "get_weather", lambda *a, **k: None)
    c = create_app().test_client()
    d = c.get("/api/data").get_json()
    assert d["weather"] is None                 # 상류 실패
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
    assert d["calendar"]["weeks"] and d["events"] is not None   # other panes survive
