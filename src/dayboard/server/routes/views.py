from pathlib import Path

from flask import Blueprint, jsonify, send_from_directory

_STATIC = Path(__file__).resolve().parents[1] / ".." / "static"

bp = Blueprint("views", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/")
def index():
    return send_from_directory(_STATIC.resolve(), "index.html")
