"""Open-Meteo(best_match) 날씨 + 인메모리 TTL 캐시. 네트워크는 여기에만."""
import time
from datetime import date as _date

import requests

WMO_LABELS = {
    0: "맑음", 1: "대체로 맑음", 2: "부분적 흐림", 3: "흐림",
    45: "안개", 48: "짙은 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    95: "뇌우", 96: "우박 동반 뇌우", 99: "강한 우박 뇌우",
}

_URL = "https://api.open-meteo.com/v1/forecast"
_cache: dict | None = None
_cache_at: float = 0.0


def reset_cache() -> None:
    global _cache, _cache_at
    _cache, _cache_at = None, 0.0


def _fetch(lat: float, lon: float, tz: str) -> dict:
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": tz, "forecast_days": 7,
        "wind_speed_unit": "ms",
    }
    resp = requests.get(_URL, params=params, timeout=8)
    resp.raise_for_status()
    return resp.json()


def _parse(payload: dict) -> dict:
    cur, daily = payload["current"], payload["daily"]
    code = int(cur["weather_code"])
    times = daily["time"]
    week = [
        {
            "date": times[i],
            "weekday": _date.fromisoformat(times[i]).weekday(),  # 0=월
            "tmax": daily["temperature_2m_max"][i],
            "tmin": daily["temperature_2m_min"][i],
            "code": int(daily["weather_code"][i]),
        }
        for i in range(len(times))
    ]
    return {
        "temp": cur["temperature_2m"],
        "humidity": cur["relative_humidity_2m"],
        "wind": cur["wind_speed_10m"],
        "code": code,
        "label": WMO_LABELS.get(code, "정보 없음"),
        "week": week,
    }


def get_weather(lat: float, lon: float, tz: str, ttl: int = 600, now: float | None = None) -> dict | None:
    global _cache, _cache_at
    t = time.time() if now is None else now
    if _cache is not None and (t - _cache_at) < ttl:
        return _cache
    try:
        parsed = _parse(_fetch(lat, lon, tz))
        _cache, _cache_at = parsed, t
        return parsed
    except Exception:
        return _cache  # 실패 → 마지막 캐시(없으면 None)
