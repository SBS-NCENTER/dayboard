# dayboard

달력·날씨·해/달·천체를 한 화면씩 넘겨 보는 전체화면 스와이프 표출 보드.
server-manager가 관리하는 서비스 계약을 따르는 재사용 test fixture.

## 특징
- **키리스**(secret 0): Open-Meteo(날씨, best_match=한국 KMA 자동선택)·astral(해·달)·holidays(공휴일)·동봉 JSON(천체). API 키 불필요.
- **빌드 0**: 프론트는 vanilla JS/CSS.
- **네트워크 최소**: 날씨만 네트워크, 나머지 3개 pane은 오프라인.

## 실행
```bash
bash setup/install.sh        # uv sync (Python 3.14 자동 프로비저닝)
bash setup/run.sh            # http://0.0.0.0:20000
```
config는 `config.toml`(위치·포트·캐시 TTL). systemd 배포는 `setup/dayboard.service`.

## 테스트
```bash
uv run pytest -q
```

## server-manager fixture
`server.toml`에 `[hooks] post_install`·`/health`·access-log·systemd 유닛을 갖춰, server-manager의 update(`u`)·revert(`U`)·restart·health·로그를 실경로로 검증한다. 등록: server-manager `registered.json`에 이 repo 경로 추가.
