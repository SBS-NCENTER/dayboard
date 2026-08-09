import datetime

from flask import Blueprint, jsonify

from ... import astro, calendar_data, config, weather

bp = Blueprint("api", __name__)


@bp.get("/api/data")
def data():
    c = config.load()
    today = datetime.date.today()
    return jsonify({
        "location": c.label,
        "today": today.isoformat(),
        "calendar": calendar_data.month_grid(today.year, today.month, today),
        "weather": weather.get_weather(c.lat, c.lon, c.tz, ttl=c.cache_ttl),
        "sun_moon": astro.sun_moon(c.lat, c.lon, c.tz, today),
        "events": astro.upcoming_events(today, n=5),
    })
