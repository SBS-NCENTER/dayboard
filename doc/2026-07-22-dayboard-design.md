# dayboard — 설계 (신규 웹서버 + server-manager test fixture)

> 날짜: 2026-07-22 · 상태: **설계 승인 → plan** · repo: SBS-NCENTER/dayboard (**public**, 신규)
> 성격: 신규 단일 플랫폼(Linux) 웹서버 = **표준 main 하나**. server-manager 검증용 재사용 fixture 겸용.

## 1. 목적

두 가지를 겸한다:
1. **실사용 표출 앱** — 달력·날씨·해/달·천체 정보를 한 화면씩 넘겨 보는 전체화면 스와이프 보드.
2. **server-manager 재사용 test fixture** — 기존 웹앱(schedule-dashboard 등)과 **동일한 descriptor 계약**을 따라, server-manager의 update(`u`)·revert(`U`)·restart·health·로그(Activity/Lifecycle)를 **실경로로 반복 검증**할 수 있는 등록 가능한 서비스.

**핵심 설계 원칙:**
- **계약 미러링**: `schedule-dashboard` 구조를 그대로 따른다(server.toml descriptor·setup/·/health·access-log→journald·pytest). 이게 fixture 가치의 핵심이다.
- **secret 0 (키리스)**: 공개 repo이므로 API 키·비밀이 전혀 없어야 한다. clone → `install.sh` → 바로 뜬다.
- **빌드 0 (순수 Python)**: 프론트는 vanilla JS/CSS(빌드 스텝 없음). `[hooks] post_install = uv sync`만 있는 **가벼운 빌드 경로**를 커버 → XR-FreeD(npm 빌드)와 상호보완.
- **네트워크 최소**: 날씨(Open-Meteo)만 네트워크. 해·달·달력·천체는 전부 오프라인 → 네트워크 없이도 4개 중 3개 pane이 동작.

## 2. 데이터 소스 (전부 키리스)

```text
┌──────────────┬─────────────────────────────────────┬──────────┐
│ 날씨          │ Open-Meteo — KMA 모델 엔드포인트     │ 네트워크  │
│ 일출·일몰     │ astral (순수 Python)                │ 오프라인  │
│ 달 위상       │ astral (순수 Python)                │ 오프라인  │
│ 달력·공휴일   │ calendar(stdlib) + holidays 라이브러리│ 오프라인  │
│ 천체 이벤트   │ repo 동봉 JSON (큐레이션 2026)        │ 오프라인  │
└──────────────┴─────────────────────────────────────┴──────────┘
```

- **날씨 = Open-Meteo KMA 모델**: `https://api.open-meteo.com/v1/kma` (기상청 LDPS 1.5km 고해상도 + GDPS 10km). 한국 정확도(기상청 자체 모델) + 키리스 동시 달성. 기상청 직통은 배제(동네예보 RSS 2024-11-28 종료, API허브/data.go.kr는 서비스키 필수 → secret-0 위반).
- **해·달 = astral**: 순수 Python이라 uv sync가 C 확장 빌드 없이 끝난다(빠르고 튼튼). 일출/일몰 + 달 위상/조명률.
- **달력 = stdlib `calendar` + `holidays`**: 이번달 그리드 + 한국 공휴일 마킹(오프라인).
- **천체 이벤트 = repo 동봉 JSON**: 2026 유성우 피크·일식/월식·슈퍼문 등 큐레이션 목록(`src/dayboard/data/celestial-events-2026.json`). "새 이벤트 목록으로 갱신"이 곧 `u`를 눌러볼 자연스러운 이유가 된다.

## 3. 구조 (schedule-dashboard 미러링)

```text
dayboard/
├── pyproject.toml           # uv·Python 3.14·hatchling / deps: flask, waitress, requests, astral, holidays / dev: pytest
├── .python-version          # 3.14
├── server.toml              # descriptor (§5)
├── config.toml              # location(lat/lon/label=서울)·port(20000)·cache TTL — tracked(secret 아님)
├── setup/
│   ├── run.sh               # exec .venv/bin/python -u -m dayboard.serve  (PATH 비의존, systemd robust)
│   ├── install.sh           # uv sync  (= [hooks] post_install)
│   ├── firewall.sh          # optional ufw (20000/tcp)
│   └── dayboard.service     # systemd 유닛 템플릿 (WorkingDirectory·ExecStart 주석은 윗줄 분리 — 인라인 # 금지)
├── src/dayboard/
│   ├── __init__.py
│   ├── serve.py             # waitress 진입 + WSGI access-log 미들웨어(→stdout→journald)
│   ├── app.py               # Flask 라우트: / · /health · /api/data
│   ├── config.py            # config.toml 로드 (lat/lon/label/port/ttl)
│   ├── weather.py           # Open-Meteo KMA 클라이언트 + 인메모리 TTL 캐시
│   ├── astro.py             # astral 일출/일몰·달위상 + 큐레이션 이벤트 로더·필터
│   ├── calendar_data.py     # 이번달 그리드 + holidays
│   └── data/celestial-events-2026.json
├── static/
│   ├── index.html           # 4개 페이지 컨테이너
│   ├── app.js               # 스와이프·fetch·렌더
│   └── style.css
├── tests/                   # pytest
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_api.py          # /api/data 형태
│   ├── test_astro.py        # 달위상 결정적(고정 날짜)
│   ├── test_calendar.py     # 그리드 + 공휴일
│   ├── test_weather.py      # Open-Meteo HTTP mock
│   └── test_config.py
├── .gitignore               # .venv, __pycache__, data/*.pid, log/ 등
└── README.md
```

**컴포넌트 경계(단일 책임):** `weather`/`astro`/`calendar_data`는 각각 순수 데이터 함수(입력=위치/날짜, 출력=dict)로, `app.py`가 조립만 한다. 네트워크는 `weather`에만. 각 모듈은 독립 테스트 가능.

## 4. 데이터 흐름

```text
브라우저 ─ GET / ─────────▶ index.html + app.js + style.css (Flask static)
app.js  ─ GET /api/data ─▶ { location, calendar, weather, sun, moon, events } (JSON)
                           백엔드 조립:
                             weather.get()      Open-Meteo(KMA) + TTL 캐시(~10분)
                             astro.sun_moon()   astral (오프라인)
                             astro.events()     큐레이션 JSON에서 다가오는 것 필터
                             calendar_data.month() stdlib + holidays (오프라인)
app.js  ─ 화면 렌더 ─────▶ 4 전체화면 페이지 (달력/날씨/해·달/천체)
app.js  ─ N분마다 ───────▶ GET /api/data 재요청 (항상-켜둔 표출 자동 갱신)
        ─ GET /health ──▶ {status:"ok"}                    (계약)
        모든 요청 ──────▶ stdout access-log ─▶ journald      (계약)
```

**프론트 상호작용:** 4개 전체화면 페이지를 **클릭-드래그 좌/우 스와이프**(터치=스와이프) + **화살표키**(←/→) + 하단 **페이지 dot**(현재 위치·클릭 이동). 빌드 스텝 없음.

**페이지 구성 (토픽별 1페이지):** ① 달력(이번달·오늘 강조·공휴일) ② 날씨(현재+오늘 최고/최저·아이콘) ③ 해·달(일출/일몰+달 위상) ④ 천체(다가오는 유성우/일식 등).

## 5. descriptor (server.toml) — 계약

```toml
[hooks]
post_install = "bash setup/install.sh"     # uv sync — u(update)가 부르는 빌드 스텝

[[service]]
name = "dayboard"
type = "web"
description = "달력·날씨·해/달·천체 스와이프 표출 보드 (server-manager fixture)"
command = "bash setup/run.sh"
host = "0.0.0.0"
port = 20000
health_path = "/health"
pidfile = "data/dayboard.pid"
autostart_service = "dayboard"
```

- `[hooks] post_install`을 **처음부터 포함** → 배포 즉시 `u`가 update 경로(pull → uv sync → restart)를 실경로로 검증.
- 포트 20000(기존 충돌 회피: 5000 schedule·10000 xr-freed·5005 tally).
- systemd 유닛명 = `dayboard.service`, autostart_service = `dayboard` (server-manager sudoers unit×verb와 정확 일치 필요 — 배포 시 sudoers 5동사 추가).

## 6. 에러 처리

- **Open-Meteo 실패**: 마지막 성공 캐시 반환, 캐시 없으면 `weather: null` + 프론트가 "날씨 불러오기 실패" placeholder. **서비스는 계속 뜬다.**
- **`/health`는 항상 ok**: 헬스 = "서비스 프로세스가 살아있나"이지 상류 API 상태가 아니다(NCCP health L1 계약 정합 — 401/상류실패를 죽음으로 표시 금지). 오프라인 pane 3개는 항상 동작.
- **큐레이션 JSON 파싱 실패/부재**: events 빈 배열, 크래시 없음.
- **config 부재/필드 누락**: 기본값(서울·20000·TTL 10분)으로 폴백, die 하지 않음.

## 7. 테스트 (pytest, schedule-dashboard 스타일)

- `test_health` — `/health` = 200 + `{status:ok}`.
- `test_api` — `/api/data` 형태(키 존재·타입), weather 실패 시에도 200 + 오프라인 pane 채워짐.
- `test_astro` — 달 위상·일출/일몰을 **고정 날짜·위치 주입**해 결정적 검증(astral 순수함수).
- `test_calendar` — 이번달 그리드 셀 수·오늘 강조·공휴일 매칭(고정 날짜 주입).
- `test_weather` — Open-Meteo 클라이언트: HTTP mock(monkeypatch/responses)으로 성공 파싱 + 실패 시 캐시 폴백.
- `test_config` — config.toml 로드 + 부재 시 기본값.

## 8. fixture 값어치 (검증 커버리지)

| server-manager 기능 | dayboard가 검증하는 실경로 |
|---|---|
| `u` update | pull → `[hooks] post_install`(uv sync) → restart (가벼운 빌드 경로) |
| `U` revert | 직전 hash reset → uv sync → restart |
| restart | `sudo -n systemctl restart dayboard.service` |
| health | `/health` 200 → detail Health ✓ |
| 로그 Activity | access-log(요청당 stdout→journald) |
| 로그 Lifecycle | systemd Started/Stopped + update 요약(`dayboard-update`) |
| dirty 경고 | config.toml/server.toml을 제어판서 편집 → dirty 파일명 표시 |

## 9. 스코프 경계 (YAGNI)

**포함:** 4 pane 표출·스와이프·키리스 데이터·계약(server.toml/health/access-log/systemd)·pytest.

**제외:** SSE 실시간 push(자동 갱신은 프론트 폴링으로 충분)·프론트 빌드(vanilla)·다중 위치·사용자 설정 UI·인증·DB·과거 데이터 저장. 큐레이션 이벤트는 2026 한 해분(연 1회 수동 갱신).

## 10. 배포 (후속 — operator-run)

dev 박스에서 먼저 `install.sh`→`run.sh`로 실동작 확인(fixture 로컬 검증) → server-manager `registered.json`에 등록해 update/revert walkthrough. 실서버(ts5) 배포는 별도(선택). git 인증: public repo라 clone/fetch 무인증 가능(private 3개와 달리 이 fixture는 **인증 없는 update 경로**도 검증).

## 11. 미해결 — plan/구현 단계에서 확정

1. **Open-Meteo KMA 응답 필드** — 실제 `/v1/kma` 응답의 weather/daily 필드명(temperature_2m, weathercode 등)을 plan 단계에서 실호출로 확인해 파서 고정.
2. **astral API 표면** — `astral.sun.sun()`·`astral.moon.phase()` 정확한 시그니처/반환을 구현 시 확인.
3. **holidays 라이브러리 KR 키** — `holidays.SouthKorea`(또는 `KR`) 사용법 확인.
