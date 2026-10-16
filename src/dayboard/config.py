"""설정 SSOT: config.toml 로드 + 경로 상수. cwd 비의존."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/dayboard/config.py -> repo root
CONFIG_TOML = PROJECT_ROOT / "config.toml"
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class Config:
    lat: float
    lon: float
    label: str
    tz: str
    port: int
    cache_ttl: int


def load() -> Config:
    loc, srv, wx = {}, {}, {}
    if CONFIG_TOML.exists():
        data = tomllib.loads(CONFIG_TOML.read_text(encoding="utf-8"))
        loc, srv, wx = (
            data.get("location", {}),
            data.get("server", {}),
            data.get("weather", {}),
        )
    return Config(
        lat=float(loc.get("lat", 37.57)),
        lon=float(loc.get("lon", 126.98)),
        label=str(loc.get("label", "서울")),
        tz=str(loc.get("tz", "Asia/Seoul")),
        port=int(srv.get("port", 20000)),
        cache_ttl=int(wx.get("cache_ttl", 600)),
    )


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
