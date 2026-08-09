# dayboard UI 개선 (5건) — 설계

> 날짜: 2026-08-09 · 상태: **설계 승인 → plan** · 대상: 기존 dayboard(구현 완료·main)에 대한 UI 개선 라운드

## 1. 배경

브라우저 실사용 확인 후 사용자 피드백 5건. 기존 아키텍처(키리스·빌드0·네트워크 최소, 백엔드=순수 데이터 / 프론트=vanilla)를 유지하며 개선한다.

**핵심 원칙:** 이모지 아이콘(WMO 코드·달 위상)은 **프론트(app.js)에서 매핑**한다 — 백엔드 모듈은 순수 데이터(weather_code·moon_phase 이름)를 유지하고, 이모지 표현은 뷰 계층에. 백엔드 변경은 weather.py의 주간 확장 하나로 최소화.

## 2. 변경 5건 + 결정

| # | 변경 | 결정 |
|---|---|---|
| ① | 스와이프 시 텍스트 선택 방지 | CSS `user-select:none` (자명) |
| ② | 라이트 모드 추가(현재 dark만) | **수동 토글 버튼** + localStorage (D1) |
| ③ | 날씨탭: 현재 크게 + 주간 + 아이콘 | **주간 7일** 스트립, 이모지 아이콘 (D2) |
| ④ | 해·달탭: 일출/일몰 텍스트化, 달 위상 아이콘 | 일출/일몰 이모지 제거·텍스트 / 달 위상 이모지 |
| ⑤ | 천체 이벤트: 전체 목록 + 서버 공유 숨김 | **브라우저 필터 UI + 서버 상태(무인증 POST)** — 코드 수정 없이 조작, 전 기기 동일 필터 (D3·D4) |

## 3. 변경 상세

### ① 스와이프 텍스트 선택 방지 (style.css)
`.track`과 `.page`에 `user-select: none; -webkit-user-select: none;` 추가. 클릭-드래그 스와이프 시 텍스트가 선택되지 않는다.

### ② 라이트 모드 — 수동 토글 (style.css + app.js)
- **CSS 변수화**: 현재 하드코딩된 색(`#0b1020` bg, `#e8ecf5` text, `#3b6ef5` today, `#ff7a7a` holiday, dot/err 등)을 `:root` CSS custom property로 추출(dark = 기본값). `:root[data-theme="light"]`에 light override.
- **light 팔레트**: bg `#f5f7fb`(밝은 회백), text `#1a2030`, today accent 파랑 유지(`#3b6ef5`), holiday `#d64545`, muted/border는 어두운 계열의 낮은 알파.
- **토글 버튼**: 우측 상단 고정 위치의 작은 버튼(dark일 때 ☾, light일 때 ☀ 표시). 클릭 → `document.documentElement`의 `data-theme` 속성 토글 + `localStorage.setItem('theme', ...)`. 페이지 로드 시 `localStorage.getItem('theme')` 읽어 적용(없으면 dark).

### ③ 날씨탭: 현재 크게 + 주간 7일 (weather.py + app.js)
- **weather.py**: `_fetch` params `forecast_days: 1 → 7`. `_parse`가 현재값(temp/humidity/wind/code/label) + **`week` 배열**(7일, 각 `{date, weekday, tmax, tmin, code}`; weekday = Python `date.fromisoformat(d).weekday()` 0=월) 반환. 반환 dict: `{temp, humidity, wind, code, label, week: [...]}`. (기존 top-level `tmax`/`tmin`는 `week[0]`으로 대체 — 제거.)
- **app.js `WMO_ICON`**: WMO weather_code → 이모지 맵(0 ☀️, 1 🌤️, 2 ⛅, 3 ☁️, 45/48 🌫️, 51/53/55 🌦️, 61/63/65 🌧️, 71/73/75 🌨️, 80/81/82 🌧️, 95/96/99 ⛈️; 미매핑은 빈 문자열).
- **renderWeather**: 상단 = 현재(큰 온도 + `WMO_ICON[code]` + 라벨 + 습도/바람 행). 하단 = 7일 스트립(각 칸 = 요일[weekday→요일 문자]·이모지·최고°/최저°). null이면 기존 placeholder.

### ④ 해·달탭: 텍스트 + 달 아이콘 (app.js)
- **renderSunMoon**: 일출/일몰을 이모지(🌅🌇) 제거하고 텍스트("일출 05:27 · 일몰 19:48"). 달 = **위상 이모지** + 위상명 + 나이. `MOON_ICON` 맵(신월 🌑, 초승달 🌒, 상현 🌓, 상현망간 🌔, 보름 🌕, 하현망간 🌖, 하현 🌗, 그믐달 🌘) — `moon_phase`(한국어 위상명) → 이모지. 백엔드 astro.py는 무변경(이미 moon_phase 이름 반환).

### ⑤ 천체 이벤트: 전체 목록 + 서버 공유 숨김 필터 (astro.py + hidden_events.py + api.py + app.js + JSON note)

큐레이션으로 목록을 줄이는 대신, **전체 목록을 반환 + 서버에 숨김 상태 저장**해 어느 브라우저에서 조작하든 **전 기기 동일 필터**로 표출한다 (코드/파일 수정 없이).

- **백엔드 — 전체 목록**: `celestial-events-2026.json`은 **10건 전부 유지**(미관측 일식 2건도 안 지움). `astro.upcoming_events`의 상한 제거: `n: int | None = None`(None이면 다가오는 것 전부). 연 ≤10건.
- **JSON note**(운영자 판단 근거): 각 이벤트 `note`에 관측 조건 명확화 — `2026-08-12 개기일식` = "유럽·북극 경로(한국 미관측)", `2026-08-28 부분월식` = "동아시아 대부분 미관측", `2026-03-03 개기월식` = "서울 관측(월출 후 진행, 최대 20:33 KST)". 유성우는 그대로.
- **숨김 상태 모듈** `src/dayboard/hidden_events.py` (registry.py 패턴): `load() -> set[str]`(숨긴 date 집합; `data/hidden_events.json` 부재/파싱실패 → 빈 셋), `save(dates: list[str])`(atomic JSON write). 파일 = `data/hidden_events.json`(런타임 상태·gitignore, `data/*.pid`처럼).
- **엔드포인트** (`routes/api.py`):
  - `GET /api/data` — `events`를 **서버에서 필터**(`upcoming_events` − 숨김 집합) → 모든 클라 동일 표출.
  - `GET /api/events` — 다가오는 **전체** 이벤트 각각에 `hidden: bool` 부착(필터 UI용).
  - `POST /api/events/hidden` — body `{"hidden": ["2026-08-12", …]}` → `hidden_events.save(...)`. **무인증**(secret-0 유지·저위험 토글·신뢰 LAN, spec §5 참조). 요청당 상태파일 읽음 = 재시작 불필요. 동시성 = last-write-wins(저빈도 수용).
- **프론트 — 필터 UI**: 천체 pane 상단 작은 **필터 토글**(예: "필터"/⚙) → `GET /api/events`로 전체 목록 + 각 숨김 체크. 변경 시 `POST /api/events/hidden` → 성공하면 `/api/data` 재요청(즉시 반영). 기본 = 전부 표시(운영자가 숨김). `renderSky`는 `/api/data`의 (이미 서버필터된) events를 렌더.

## 4. 데이터 흐름 (변경 후)

```text
weather.get_weather   → {temp,humidity,wind,code,label, week:[{date,weekday,tmax,tmin,code}×7]}
astro.sun_moon        → {sunrise,sunset,moon_age,moon_phase}          (무변경)
astro.upcoming_events → [{date,name,type,note}…]  (n 상한 제거 = 다가오는 것 전부)
hidden_events.load    → set[date]  (data/hidden_events.json, 부재→빈셋)
GET  /api/data        → events = upcoming − hidden(서버 필터)          [전 기기 동일]
GET  /api/events      → 전체 upcoming + 각 hidden:bool                 [필터 UI]
POST /api/events/hidden → hidden_events.save(...)                      [무인증 토글]
app.js:
  WMO_ICON[code]      현재/주간 각 날 이모지
  MOON_ICON[phase]    달 위상 이모지
  data-theme 토글     localStorage('theme')  (테마만 클라 저장)
  필터 UI             GET /api/events → 체크변경 POST → /api/data 재요청
```

## 5. 에러 처리 (기존 계약 유지)
- weather null → 기존 "날씨 불러오기 실패" placeholder(주간 포함 pane 통째). 미매핑 WMO 코드 → 이모지 빈 문자열(텍스트 라벨은 유지).
- 미매핑 moon phase → 이모지 없이 위상명만.
- 테마 localStorage 부재 → dark 기본. 숨김 상태파일 부재·파싱실패 → 빈 셋(전부 표시). `POST /api/events/hidden` 잘못된 body → 400·상태 무변경(크래시 없음).

## 6. 테스트
- **weather.py**: `_parse`가 `week` 7일 배열 반환(각 date/weekday/tmax/tmin/code) 검증 + 기존 현재값 파싱 유지. test_weather fixture를 7일 daily 배열로 갱신.
- **astro.py**: `upcoming_events`의 `n=None`(상한 없음)이 다가오는 것 전부 반환 검증 + 기존 `n=<int>` 상한 동작 유지(test_astro 확장).
- **hidden_events.py**: `load`(부재→빈셋·라운드트립) + `save` atomic(registry 패턴 테스트).
- **api**: `GET /api/data` events가 숨김 제외 반영 · `GET /api/events`가 전체 + hidden:bool · `POST /api/events/hidden`이 상태파일 기록 후 `/api/data`에 반영 · 잘못된 body → 400.
- **events**: celestial-events-2026.json이 **10건 전부 유지**(미관측 일식 2건 포함) + 각 note에 관측 조건 존재 검증.
- 기존 회귀(config·calendar·astro·server·serve·views·api) 전부 유지. 프론트 JS는 유닛테스트 없음(무빌드 fixture — 기존 방침) → e2e 시각 확인(테마 토글·필터 UI·전 기기 공유).

## 7. 스코프 경계 (YAGNI)
**포함:** 위 5건(⑤ = 전체 목록 + **서버 공유** 숨김 필터).
**제외:** 자동 테마(시간/OS)·주간 시간별 예보·달 위상 그래픽(이모지로 충분)·숨김 POST 인증(무인증=secret-0 유지, §5)·이벤트 편집/추가 UI(숨김만)·프론트 빌드 도입.

## 8. 미해결 (구현 시 확정)
1. **Open-Meteo 7일 daily 응답** — `forecast_days=7`의 실제 `daily.time`/`temperature_2m_max` 배열 길이·형식을 구현 시 실호출로 확인(현재 1일과 동일 구조 확장 예상).
2. **light 팔레트 실색상** — §3-② 제안값 기준, 시각 확인 후 미세조정.
