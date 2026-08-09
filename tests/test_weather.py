from dayboard import weather


def _fake_payload():
    return {
        "current": {"temperature_2m": 30.4, "relative_humidity_2m": 71,
                    "weather_code": 1, "wind_speed_10m": 5.4},
        "daily": {"time": ["2026-08-09", "2026-08-10", "2026-08-11"],
                  "temperature_2m_max": [30.4, 31.7, 31.5],
                  "temperature_2m_min": [24.4, 25.0, 24.8],
                  "weather_code": [1, 3, 51]},
    }


def test_get_weather_parses(monkeypatch):
    weather.reset_cache()
    monkeypatch.setattr(weather, "_fetch", lambda lat, lon, tz: _fake_payload())
    w = weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=600, now=0.0)
    assert w["temp"] == 30.4 and w["humidity"] == 71 and w["wind"] == 5.4
    assert w["code"] == 1 and w["label"] == "대체로 맑음"
    assert "tmax" not in w and "tmin" not in w         # top-level 제거
    assert len(w["week"]) == 3
    d0 = w["week"][0]
    assert d0["date"] == "2026-08-09" and d0["tmax"] == 30.4 and d0["tmin"] == 24.4
    assert d0["code"] == 1 and d0["weekday"] == 6      # 2026-08-09 = 일요일(6)


def test_cache_serves_within_ttl(monkeypatch):
    weather.reset_cache()
    calls = {"n": 0}
    def fetch(lat, lon, tz):
        calls["n"] += 1
        return _fake_payload()
    monkeypatch.setattr(weather, "_fetch", fetch)
    weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=600, now=100.0)
    weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=600, now=200.0)  # TTL 내
    assert calls["n"] == 1  # 두번째는 캐시


def test_failure_falls_back_to_cache_then_none(monkeypatch):
    weather.reset_cache()
    monkeypatch.setattr(weather, "_fetch", lambda *a: _fake_payload())
    weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=1, now=0.0)     # 캐시 채움
    def boom(*a):
        raise RuntimeError("network down")
    monkeypatch.setattr(weather, "_fetch", boom)
    stale = weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=1, now=999.0)  # TTL 만료 + 실패
    assert stale["temp"] == 30.4          # 마지막 캐시 폴백
    weather.reset_cache()
    assert weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=1, now=999.0) is None
