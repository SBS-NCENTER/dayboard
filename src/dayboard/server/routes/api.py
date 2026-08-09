import datetime

from flask import Blueprint, jsonify, request

from ... import astro, calendar_data, config, hidden_events, weather

bp = Blueprint("api", __name__)


def _safe(fn, fallback):
    try:
        return fn()
    except Exception:
        return fallback


@bp.get("/api/data")
def data():
    c = config.load()
    today = datetime.date.today()
    hidden = hidden_events.load()
    events = _safe(lambda: [e for e in astro.upcoming_events(today) if e["date"] not in hidden], [])
    return jsonify({
        "location": c.label,
        "today": today.isoformat(),
        "calendar": _safe(lambda: calendar_data.month_grid(today.year, today.month, today), None),
        "weather": weather.get_weather(c.lat, c.lon, c.tz, ttl=c.cache_ttl),
        "sun_moon": _safe(lambda: astro.sun_moon(c.lat, c.lon, c.tz, today), None),
        "events": events,
    })


@bp.get("/api/events")
def events_all():
    today = datetime.date.today()
    hidden = hidden_events.load()
    items = _safe(lambda: astro.upcoming_events(today), [])
    return jsonify([{**e, "hidden": e["date"] in hidden} for e in items])


@bp.post("/api/events/hidden")
def set_hidden():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("hidden"), list):
        return jsonify({"error": "hidden must be a list"}), 400
    hidden_events.save(body["hidden"])
    return jsonify({"status": "ok"})
