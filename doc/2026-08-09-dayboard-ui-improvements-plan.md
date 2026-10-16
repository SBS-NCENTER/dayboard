# dayboard UI 개선 (5건) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** dayboard에 5개 UI 개선 — 스와이프 선택방지·라이트모드 토글·날씨 주간7일+이모지·해달 텍스트+달아이콘·천체 전체목록+서버공유 숨김필터.

**Architecture:** 백엔드는 순수 데이터 유지(이모지는 프론트 매핑). weather는 7일 배열로 확장, 천체는 전체 반환 + 서버측 숨김 상태(`hidden_events.py` + `data/hidden_events.json` + 2 엔드포인트)로 필터. 프론트는 vanilla JS/CSS(빌드0) — CSS 변수화로 라이트/다크, 이모지 아이콘 맵, 필터 UI.

**Tech Stack:** Python 3.14/Flask/waitress/requests, vanilla HTML/JS/CSS, pytest, uv.

## Global Constraints

- 테스트 러너 = `uv run pytest`. 전체 회귀 유지 + 신규 테스트 green.
- **secret 0 / 빌드 0 / 네트워크 최소** 유지. 이모지 아이콘은 **프론트(app.js) 매핑** — 백엔드는 weather_code·moon_phase 이름만.
- **날씨 = Open-Meteo best_match**, `forecast_days=7`. daily.time/temperature_2m_max/min/weather_code = 7원소 배열(실측 확정).
- **천체 숨김 = 무인증** POST (secret-0 유지·저위험 토글·신뢰 LAN). 상태파일 `data/hidden_events.json`(gitignore, `data/*.pid`처럼 이미 무시됨) 요청당 읽기 = 재시작 불필요.
- **라이트 팔레트**: dark(기본) `--bg #0b1020 --text #e8ecf5 --accent #3b6ef5 --holiday #ff7a7a`; light `--bg #f5f7fb --text #1a2030 --accent #3b6ef5 --holiday #d64545`.
- **이모지**: WMO(0 ☀️,1 🌤️,2 ⛅,3 ☁️,45/48 🌫️,51/53/55 🌦️,61/63/65 🌧️,71/73/75 🌨️,80/81/82 🌧️,95/96/99 ⛈️); 달(신월 🌑,초승달 🌒,상현 🌓,상현망간 🌔,보름 🌕,하현망간 🌖,하현 🌗,그믐달 🌘).
- 텍스트 `open()`/파일 = `encoding="utf-8"`. cwd 비의존.
- **커밋 케이던스**: implementer는 commit 안 함 → controller working-tree diff 리뷰 → 사용자 task당 commit. **브랜치 = main**(기존 코드 이어서).

---

## File Structure

```text
src/dayboard/
├── weather.py            [T1] forecast_days 7 + week 배열
├── astro.py              [T2] upcoming_events n=None(전부)
├── hidden_events.py      [T3] 신규: 숨김 date 집합 영속
├── server/routes/api.py  [T4] /api/data 서버필터 + GET /api/events + POST /api/events/hidden
├── data/celestial-events-2026.json  [T8] note 관측조건 갱신(10건 유지)
└── static/
    ├── style.css         [T5] user-select + CSS변수화(dark/light) + 신규 컴포넌트 스타일
    ├── index.html        [T6] 테마 버튼 + [T8] 필터 버튼
    └── app.js            [T6]테마토글 [T7]weather/sunmoon render+아이콘 [T8]필터 UI
tests/
├── test_weather.py       [T1] week 배열
├── test_astro.py         [T2] n=None
├── test_hidden_events.py [T3] 신규
└── test_api.py           [T4] 서버필터·엔드포인트
```

---

## Task 1: weather.py — 주간 7일 배열

**Files:** Modify `src/dayboard/weather.py`, `tests/test_weather.py`

**Interfaces:**
- Produces: `get_weather(...)` 반환 dict = `{temp, humidity, wind, code, label, week: [{date, weekday, tmax, tmin, code} × N]}` (weekday 0=월). 기존 top-level `tmax`/`tmin` **제거**(→ `week[0]`).

- [ ] **Step 1: 테스트 갱신(실패)** — `tests/test_weather.py`의 `_fake_payload`와 assertion을 week 배열로:
```python
def _fake_payload():
    return {
        "current": {
            "temperature_2m": 30.4,
            "relative_humidity_2m": 71,
            "weather_code": 1,
            "wind_speed_10m": 5.4,
        },
        "daily": {
            "time": ["2026-08-09", "2026-08-10", "2026-08-11"],
            "temperature_2m_max": [30.4, 31.7, 31.5],
            "temperature_2m_min": [24.4, 25.0, 24.8],
            "weather_code": [1, 3, 51],
        },
    }


def test_get_weather_parses(monkeypatch):
    weather.reset_cache()
    monkeypatch.setattr(weather, "_fetch", lambda lat, lon, tz: _fake_payload())
    w = weather.get_weather(37.57, 126.98, "Asia/Seoul", ttl=600, now=0.0)
    assert w["temp"] == 30.4 and w["humidity"] == 71 and w["wind"] == 5.4
    assert w["code"] == 1 and w["label"] == "대체로 맑음"
    assert "tmax" not in w and "tmin" not in w  # top-level 제거
    assert len(w["week"]) == 3
    d0 = w["week"][0]
    assert d0["date"] == "2026-08-09" and d0["tmax"] == 30.4 and d0["tmin"] == 24.4
    assert d0["code"] == 1 and d0["weekday"] == 6  # 2026-08-09 = 일요일(6)
```
(기존 `test_cache_serves_within_ttl`·`test_failure_falls_back_to_cache_then_none`은 `_fake_payload()`를 재사용하므로 자동으로 새 구조 사용 — 그 테스트들은 temp만 보므로 수정 불필요.)

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/test_weather.py::test_get_weather_parses -v` · Expected: FAIL (`week` 키 없음 / tmax 잔존).

- [ ] **Step 3: 구현** — `src/dayboard/weather.py`. 상단 import에 추가:
```python
from datetime import date as _date
```
`_fetch`의 params에서 `"forecast_days": 1` → `"forecast_days": 7`.
`_parse` 교체:
```python
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
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/test_weather.py -v` · Expected: PASS (3).

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: weekly 7-day weather (week array)

weather.py forecast_days 7 + _parse가 week[{date,weekday,tmax,tmin,
code}] 반환. 프론트 주간 스트립용. 아이콘은 프론트 매핑.
```

---

## Task 2: astro.upcoming_events — 상한 제거(n=None)

**Files:** Modify `src/dayboard/astro.py`, `tests/test_astro.py`

**Interfaces:**
- Produces: `upcoming_events(today, n: int | None = None, path=None) -> list[dict]`. `n=None`이면 다가오는 것 **전부**(정렬). `n=<int>`이면 기존처럼 상한.

- [ ] **Step 1: 실패 테스트** — `tests/test_astro.py`에 추가:
```python
def test_upcoming_events_no_limit_returns_all(tmp_path):
    p = tmp_path / "ev.json"
    p.write_text(
        '[{"date":"2026-08-12","name":"a","type":"x","note":""},'
        '{"date":"2026-09-01","name":"b","type":"x","note":""},'
        '{"date":"2026-10-01","name":"c","type":"x","note":""},'
        '{"date":"2026-11-01","name":"d","type":"x","note":""},'
        '{"date":"2026-12-01","name":"e","type":"x","note":""},'
        '{"date":"2026-12-14","name":"f","type":"x","note":""}]',
        encoding="utf-8",
    )
    got = astro.upcoming_events(datetime.date(2026, 8, 1), path=p)  # n 생략 = None
    assert len(got) == 6  # 상한 없음
    assert [e["date"] for e in got][:2] == ["2026-08-12", "2026-09-01"]
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/test_astro.py::test_upcoming_events_no_limit_returns_all -v` · Expected: FAIL (기존 `n=5` 상한으로 6개 중 5개만).

- [ ] **Step 3: 구현** — `src/dayboard/astro.py` `upcoming_events` 시그니처·반환 수정:
```python
def upcoming_events(
    today: datetime.date, n: int | None = None, path: Path | None = None
) -> list[dict]:
    p = path or _EVENTS_PATH
    try:
        items = json.loads(p.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return []
    upcoming = [e for e in items if e.get("date", "") >= today.isoformat()]
    upcoming.sort(key=lambda e: e["date"])
    return upcoming if n is None else upcoming[:n]
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/test_astro.py -v` · Expected: PASS (기존 `test_upcoming_events_filters_and_limits`[n=3] + 신규 무제한 + 나머지).

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: upcoming_events optional limit (n=None = all)

필터 UI가 전체 목록을 다루도록 n 상한을 선택적으로. 기본 None=전부,
정수 지정 시 기존 상한.
```

---

## Task 3: hidden_events.py — 숨김 상태 영속 (신규)

**Files:** Create `src/dayboard/hidden_events.py`, `tests/test_hidden_events.py`

**Interfaces:**
- Produces: `load() -> set[str]` (`data/hidden_events.json`의 숨긴 date 집합; 부재/파싱실패 → 빈 셋). `save(dates) -> None` (dedup+정렬 후 atomic JSON write). 모듈 상수 `_PATH`(테스트가 monkeypatch).

- [ ] **Step 1: 실패 테스트** — `tests/test_hidden_events.py`:
```python
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
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/test_hidden_events.py -v` · Expected: FAIL (모듈 없음).

- [ ] **Step 3: 구현** — `src/dayboard/hidden_events.py`:
```python
"""숨긴 천체 이벤트 date 집합 영속(data/hidden_events.json). 서버 공유 필터 상태."""

import json

from . import config

_PATH = config.DATA_DIR / "hidden_events.json"


def load() -> set[str]:
    try:
        return set(json.loads(_PATH.read_text(encoding="utf-8")))
    except OSError, ValueError:
        return set()


def save(dates) -> None:
    config.ensure_runtime_dirs()
    _PATH.write_text(json.dumps(sorted(set(map(str, dates)))), encoding="utf-8")
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/test_hidden_events.py -v` · Expected: PASS (3).

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: hidden_events state module

data/hidden_events.json에 숨긴 천체 이벤트 date 집합 영속(load 빈셋
폴백·save dedup+정렬). 서버 공유 필터의 상태 저장소.
```

---

## Task 4: api.py — 서버 필터 + 이벤트 엔드포인트

**Files:** Modify `src/dayboard/server/routes/api.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `astro.upcoming_events(today)` (T2, 전부), `hidden_events.load/save` (T3).
- Produces: `GET /api/data`의 `events` = upcoming − hidden(서버필터). `GET /api/events` = 전체 upcoming 각 `{...e, hidden: bool}`. `POST /api/events/hidden` body `{"hidden":[date…]}` → save; 잘못된 body → 400.

- [ ] **Step 1: 실패 테스트** — `tests/test_api.py`에 추가(파일 상단 import에 `from dayboard import hidden_events` 추가):
```python
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
```

- [ ] **Step 2: 실패 확인** — Run: `uv run pytest tests/test_api.py -k "hidden or events" -v` · Expected: FAIL (엔드포인트/필터 없음).

- [ ] **Step 3: 구현** — `src/dayboard/server/routes/api.py` 전체 교체:
```python
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
    return jsonify(
        {
            "location": c.label,
            "today": today.isoformat(),
            "calendar": _safe(
                lambda: calendar_data.month_grid(today.year, today.month, today), None
            ),
            "weather": weather.get_weather(c.lat, c.lon, c.tz, ttl=c.cache_ttl),
            "sun_moon": _safe(lambda: astro.sun_moon(c.lat, c.lon, c.tz, today), None),
            "events": events,
        }
    )


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
```

- [ ] **Step 4: 통과 확인** — Run: `uv run pytest tests/test_api.py -v` · Expected: PASS (기존 + 신규 4). 전체 `uv run pytest -q` green.

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: server-side event hide filter + endpoints

/api/data가 숨김 제외(전 기기 동일) + GET /api/events(전체+hidden) +
POST /api/events/hidden(무인증·400 검증). hidden_events 상태 소비.
```

---

## Task 5: style.css — 스와이프 선택방지 + CSS 변수화(dark/light) + 신규 컴포넌트

**Files:** Modify `src/dayboard/static/style.css`

**Interfaces:**
- Produces: `:root` CSS 변수(dark 기본) + `:root[data-theme="light"]` override. `.track/.page` user-select:none. 신규 스타일: `.theme-btn`, `.wk`(주간 스트립), `.filter-*`(필터 UI). 후속 T6/T7/T8 프론트가 이 클래스를 씀.

- [ ] **Step 1: style.css 전체 교체** — `src/dayboard/static/style.css`:
```css
:root {
  --bg: #0b1020; --text: #e8ecf5; --accent: #3b6ef5; --holiday: #ff7a7a;
  --muted: rgba(255,255,255,.55); --dot: rgba(255,255,255,.25); --dot-on: #e8ecf5;
  --card: rgba(255,255,255,.06); --border: rgba(255,255,255,.12);
}
:root[data-theme="light"] {
  --bg: #f5f7fb; --text: #1a2030; --accent: #3b6ef5; --holiday: #d64545;
  --muted: rgba(20,30,50,.55); --dot: rgba(20,30,50,.2); --dot-on: #1a2030;
  --card: rgba(20,30,50,.05); --border: rgba(20,30,50,.12);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; background: var(--bg); color: var(--text);
  font-family: system-ui, "Noto Sans KR", sans-serif; transition: background .3s, color .3s; }
.track { display: flex; height: 100%; width: 400%; transition: transform .35s ease;
  touch-action: pan-y; user-select: none; -webkit-user-select: none; }
.page { width: 25%; height: 100%; flex: 0 0 25%; padding: 5vh 6vw;
  display: flex; flex-direction: column; user-select: none; -webkit-user-select: none; }
.ttl { font-size: 2.2rem; font-weight: 700; opacity: .85; margin-bottom: 3vh; }
.body { flex: 1; display: flex; flex-direction: column; justify-content: center; }
/* calendar */
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: .4rem; }
.cal-h { text-align: center; opacity: .5; font-size: 1rem; padding: .4rem 0; }
.cal-c { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; border-radius: .6rem; font-size: 1.4rem; }
.cal-c.today { background: var(--accent); color: #fff; font-weight: 700; }
.cal-c.holiday { color: var(--holiday); }
.cal-c.empty { opacity: .15; }
.cal-hol-name { font-size: .7rem; opacity: .8; }
/* weather */
.big { font-size: 5rem; font-weight: 700; }
.sub { font-size: 1.6rem; opacity: .8; margin-top: 1vh; }
.row { display: flex; gap: 2rem; font-size: 1.4rem; opacity: .8; margin-top: 2vh; }
.wx-now { display: flex; align-items: center; gap: 1.5rem; }
.wx-ico { font-size: 4rem; }
.wk { display: flex; gap: .6rem; margin-top: 4vh; }
.wk-d { flex: 1; background: var(--card); border: 1px solid var(--border); border-radius: .6rem;
  padding: 1rem .4rem; text-align: center; }
.wk-day { font-size: 1rem; opacity: .7; }
.wk-ico { font-size: 1.8rem; margin: .4rem 0; }
.wk-t { font-size: 1.1rem; }
.wk-t .mx { font-weight: 700; } .wk-t .mn { opacity: .6; }
/* sun-moon */
.sm-row { font-size: 1.8rem; }
.moon { display: flex; align-items: center; gap: 1rem; margin-top: 3vh; }
.moon-ico { font-size: 3.5rem; }
/* sky events */
.ev { display: flex; justify-content: space-between; font-size: 1.5rem;
  padding: 1.2rem 0; border-bottom: 1px solid var(--border); }
.ev .d { opacity: .6; }
.err { opacity: .5; font-size: 1.4rem; }
/* dots */
.dots { position: fixed; bottom: 3vh; left: 0; right: 0; display: flex;
  justify-content: center; gap: .8rem; }
.dot { width: .8rem; height: .8rem; border-radius: 50%; background: var(--dot);
  cursor: pointer; transition: background .2s; }
.dot.on { background: var(--dot-on); }
/* theme button */
.theme-btn { position: fixed; top: 2vh; right: 2vw; z-index: 10;
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  border-radius: 50%; width: 2.6rem; height: 2.6rem; font-size: 1.2rem;
  cursor: pointer; }
/* event filter */
.filter-btn { align-self: flex-end; background: var(--card); color: var(--text);
  border: 1px solid var(--border); border-radius: .5rem; padding: .4rem .9rem;
  font-size: 1rem; cursor: pointer; margin-bottom: 1vh; }
.filter-panel { background: var(--card); border: 1px solid var(--border);
  border-radius: .6rem; padding: 1rem 1.4rem; margin-bottom: 2vh; }
.filter-row { display: flex; align-items: center; gap: .8rem; font-size: 1.2rem;
  padding: .5rem 0; cursor: pointer; }
.filter-row input { width: 1.2rem; height: 1.2rem; }
.filter-row .fn { flex: 1; } .filter-row .fd { opacity: .6; font-size: 1rem; }
.hidden { display: none; }
```

- [ ] **Step 2: 렌더 스모크(수동)** — 서버가 떠 있으면 브라우저 새로고침해 dark 렌더 깨짐 없나 확인(변수화 후 색 동일해야). 자동 테스트 없음(CSS).

- [ ] **Step 3: Commit (사용자)** — 제안:
```
feat: css variables (dark/light) + no-select + component styles

색을 :root 변수로 추출(dark 기본 · [data-theme=light] override) +
.track/.page user-select:none(스와이프 선택 방지) + 주간/테마버튼/
필터 UI 컴포넌트 스타일. 기존 dark 렌더 동일.
```

---

## Task 6: app.js — 테마 토글 (② JS) + index.html 버튼

**Files:** Modify `src/dayboard/static/index.html`, `src/dayboard/static/app.js`

**Interfaces:**
- Consumes: T5의 `[data-theme]` 변수·`.theme-btn` 스타일.
- Produces: 로드 시 `localStorage('theme')` 적용(없으면 dark), 버튼 클릭 토글. 후속 T7/T8이 같은 app.js에 render/필터 추가.

- [ ] **Step 1: index.html에 버튼 추가** — `src/dayboard/static/index.html`의 `<body>` 맨 위(track 앞)에:
```html
  <button id="theme-btn" class="theme-btn" aria-label="테마 전환"></button>
```

- [ ] **Step 2: app.js 테마 로직 추가** — `src/dayboard/static/app.js` 상단(기존 `const PAGES...` 앞, `esc` 헬퍼 뒤)에:
```javascript
// 테마 (dark 기본 / light 토글, localStorage 지속)
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('theme-btn').textContent = t === 'light' ? '☀' : '☾';
}
let theme = localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
applyTheme(theme);
document.getElementById('theme-btn').onclick = () => {
  theme = theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', theme);
  applyTheme(theme);
};
```

- [ ] **Step 3: 수동 확인** — 브라우저에서 버튼 클릭 → dark↔light 전환·새로고침 후 유지 확인.

- [ ] **Step 4: Commit (사용자)** — 제안:
```
feat: manual light/dark theme toggle

우측 상단 ☾/☀ 버튼 → data-theme 전환 + localStorage 지속(기본 dark).
```

---

## Task 7: app.js — 날씨(③) · 해달(④) render + 이모지

**Files:** Modify `src/dayboard/static/app.js`

**Interfaces:**
- Consumes: `/api/data`의 `weather.week`(T1), `sun_moon.moon_phase`(기존).
- Produces: `renderWeather`(현재 크게+이모지+주간 스트립), `renderSunMoon`(일출/일몰 텍스트+달 이모지). `WMO_ICON`/`MOON_ICON` 맵.

- [ ] **Step 1: 아이콘 맵 추가** — app.js 상단(테마 로직 근처)에:
```javascript
const WMO_ICON = {0:'☀️',1:'🌤️',2:'⛅',3:'☁️',45:'🌫️',48:'🌫️',
  51:'🌦️',53:'🌦️',55:'🌦️',61:'🌧️',63:'🌧️',65:'🌧️',
  71:'🌨️',73:'🌨️',75:'🌨️',80:'🌧️',81:'🌧️',82:'🌧️',95:'⛈️',96:'⛈️',99:'⛈️'};
const MOON_ICON = {'신월':'🌑','초승달':'🌒','상현':'🌓','상현망간':'🌔',
  '보름':'🌕','하현망간':'🌖','하현':'🌗','그믐달':'🌘'};
const wmoIco = (c) => WMO_ICON[c] || '';
```
(참고: `WD = ['월','화','수','목','금','토','일']`는 renderCalendar에서 이미 정의됨 — 주간 스트립도 재사용.)

- [ ] **Step 2: renderWeather 교체** — 기존 함수를:
```javascript
function renderWeather(w) {
  const el = document.getElementById('wx');
  if (!w) { el.innerHTML = '<div class="err">날씨 불러오기 실패</div>'; return; }
  const strip = (w.week || []).map(d =>
    `<div class="wk-d"><div class="wk-day">${WD[d.weekday]}</div>` +
    `<div class="wk-ico">${wmoIco(d.code)}</div>` +
    `<div class="wk-t"><span class="mx">${Math.round(d.tmax)}°</span> ` +
    `<span class="mn">${Math.round(d.tmin)}°</span></div></div>`).join('');
  el.innerHTML =
    `<div class="wx-now"><span class="wx-ico">${wmoIco(w.code)}</span>` +
    `<span class="big">${Math.round(w.temp)}°</span></div>` +
    `<div class="sub">${esc(w.label)}</div>` +
    `<div class="row"><span>습도 ${Math.round(w.humidity)}%</span>` +
    `<span>바람 ${Math.round(w.wind)} m/s</span></div>` +
    `<div class="wk">${strip}</div>`;
}
```

- [ ] **Step 3: renderSunMoon 교체** — 기존 함수를:
```javascript
function renderSunMoon(s) {
  const el = document.getElementById('sm');
  if (!s) { el.innerHTML = '<div class="err">해/달 정보 로드 실패</div>'; return; }
  const ico = MOON_ICON[s.moon_phase] || '';
  el.innerHTML =
    `<div class="sm-row">일출 ${esc(s.sunrise)} · 일몰 ${esc(s.sunset)}</div>` +
    `<div class="moon"><span class="moon-ico">${ico}</span>` +
    `<span><div class="big" style="font-size:2.6rem">${esc(s.moon_phase)}</div>` +
    `<div class="sub">달 나이 ${s.moon_age}일</div></span></div>`;
}
```

- [ ] **Step 4: 수동 확인** — 브라우저: 날씨탭 = 현재(이모지+온도)+7일 스트립, 해달탭 = 일출/일몰 텍스트+달 이모지.

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: weather weekly strip + sun/moon icons

renderWeather = 현재(이모지+온도)+주간 7일 스트립(요일·이모지·최고/
최저). renderSunMoon = 일출/일몰 텍스트 + 달 위상 이모지. WMO/MOON
이모지 맵(프론트 매핑).
```

---

## Task 8: app.js 이벤트 필터 UI (⑤ 프론트) + JSON note

**Files:** Modify `src/dayboard/static/index.html`, `src/dayboard/static/app.js`, `src/dayboard/data/celestial-events-2026.json`

**Interfaces:**
- Consumes: `GET /api/events`(T4, 전체+hidden), `POST /api/events/hidden`(T4).
- Produces: 천체 pane의 필터 토글 → 목록 체크 → POST → `/api/data` 재요청.

- [ ] **Step 1: JSON note 갱신** — `src/dayboard/data/celestial-events-2026.json`에서 3건 note 수정(10건 유지, 제거 없음):
  - `2026-03-03` note → `"서울 관측(월출 후 진행, 최대 20:33 KST)"`
  - `2026-08-12` note → `"유럽·북극 경로(한국 미관측)"` (이미 유사 — 정확히 이 문구로)
  - `2026-08-28` note → `"동아시아 대부분 미관측"`

- [ ] **Step 2: index.html에 천체 pane 필터 요소 추가** — 천체 page 섹션(`id="page-sky"`)의 `<div class="body" id="sky">` **앞**에:
```html
      <button id="filter-btn" class="filter-btn">필터</button>
      <div id="filter-panel" class="filter-panel hidden"></div>
```

- [ ] **Step 3: app.js 필터 로직 추가** — app.js 하단(`refresh()` 정의 근처)에:
```javascript
// 천체 이벤트 필터 (서버 공유 상태)
document.getElementById('filter-btn').onclick = async () => {
  const panel = document.getElementById('filter-panel');
  if (!panel.classList.contains('hidden')) { panel.classList.add('hidden'); return; }
  try {
    const evs = await (await fetch('/api/events')).json();
    panel.innerHTML = evs.map(e =>
      `<label class="filter-row"><input type="checkbox" data-date="${esc(e.date)}"` +
      `${e.hidden ? '' : ' checked'}>` +
      `<span class="fn">${esc(e.name)}</span><span class="fd">${esc(e.date)}</span></label>`
    ).join('') || '<div class="err">이벤트 없음</div>';
    panel.classList.remove('hidden');
    panel.querySelectorAll('input[type=checkbox]').forEach(cb => {
      cb.onchange = async () => {
        const hidden = [...panel.querySelectorAll('input:not(:checked)')].map(x => x.dataset.date);
        await fetch('/api/events/hidden', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({hidden}),
        });
        refresh();   // /api/data 재요청 → 표출 즉시 반영
      };
    });
  } catch (e) { /* 무시 — 다음 시도 */ }
};
```
(체크됨 = 표시, 언체크 = 숨김. `refresh()`는 기존 `/api/data` 폴링 함수 재사용.)

- [ ] **Step 4: 수동 확인** — 천체탭 "필터" → 목록 표시, 항목 언체크 → 즉시 사라짐, **다른 브라우저 새로고침 시 동일 반영**(서버 공유), 재시작 불필요.

- [ ] **Step 5: Commit (사용자)** — 제안:
```
feat: server-shared celestial event filter UI + notes

천체 pane 필터 토글 → GET /api/events 체크 → POST /api/events/hidden →
/api/data 재요청. 전 기기 동일 필터. JSON note 관측조건 명확화(10건 유지).
```

---

## Self-Review 결과 (작성자 체크)

- **Spec 커버리지**: ①=T5(user-select) ②=T5(CSS)+T6(JS) ③=T1(backend)+T7(render) ④=T7(render) ⑤=T2(all)+T3(state)+T4(endpoints)+T8(UI+note). §6 테스트=T1~4 TDD. §8 미해결(Open-Meteo 7일)=실측 확정 반영. **누락 없음.**
- **Placeholder 스캔**: TBD/TODO 없음. 코드 전부 제공.
- **타입 일관성**: `week[{date,weekday,tmax,tmin,code}]`(T1) ↔ T7 renderWeather 소비 일치. `upcoming_events(today, n=None)`(T2) ↔ T4 호출 일치. `hidden_events.load/save`(T3) ↔ T4 소비 일치. `/api/events`의 `{...e, hidden}`(T4) ↔ T8 필터 UI 소비 일치. CSS 클래스(T5: wk/theme-btn/filter-*) ↔ T6/7/8 사용 일치. `WD`(기존 renderCalendar) ↔ T7 재사용.
- **주의(실행자)**: 프론트 T5~8은 유닛테스트 없음(무빌드 JS) → 각 task 수동/시각 확인, 최종 e2e. T1의 `_fake_payload` 변경이 기존 cache/failure 테스트에 영향 없는지 확인(temp만 참조). T4 test는 `hidden_events._PATH` monkeypatch로 실 `data/` 미오염.
