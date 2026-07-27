"""해·달(astral, 오프라인) + 큐레이션 천체 이벤트."""
import datetime
import json
from pathlib import Path

from astral import LocationInfo
from astral.moon import phase as _moon_phase
from astral.sun import sun as _sun

_EVENTS_PATH = Path(__file__).resolve().parent / "data" / "celestial-events-2026.json"

# 달 나이(0..27.99, 삭망월 ~29.53의 astral 스케일) → 한국어 위상명
_PHASE_BANDS = [
    (1.84, "신월"), (5.53, "초승달"), (9.22, "상현"), (12.91, "상현망간"),
    (16.61, "보름"), (20.30, "하현망간"), (23.99, "하현"), (27.68, "그믐달"),
]


def moon_phase_name(age: float) -> str:
    for upper, name in _PHASE_BANDS:
        if age < upper:
            return name
    return "신월"  # 27.68.. → 다시 신월


def sun_moon(lat: float, lon: float, tz: str, date: datetime.date) -> dict:
    loc = LocationInfo(latitude=lat, longitude=lon, timezone=tz)
    s = _sun(loc.observer, date=date, tzinfo=tz)
    age = round(float(_moon_phase(date)), 2)
    return {
        "sunrise": s["sunrise"].strftime("%H:%M"),
        "sunset": s["sunset"].strftime("%H:%M"),
        "moon_age": age,
        "moon_phase": moon_phase_name(age),
    }


def upcoming_events(today: datetime.date, n: int = 5, path: Path | None = None) -> list[dict]:
    p = path or _EVENTS_PATH
    try:
        items = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    upcoming = [e for e in items if e.get("date", "") >= today.isoformat()]
    upcoming.sort(key=lambda e: e["date"])
    return upcoming[:n]
