import datetime

from dayboard import astro


def test_sun_moon_deterministic():
    r = astro.sun_moon(37.57, 126.98, "Asia/Seoul", datetime.date(2026, 7, 22))
    assert r["sunrise"] == "05:27"  # astral 3.2 실측
    assert r["sunset"] == "19:48"
    assert isinstance(r["moon_age"], float)
    assert r["moon_phase"] == astro.moon_phase_name(r["moon_age"])


def test_moon_phase_names():
    assert astro.moon_phase_name(0.0) == "신월"
    assert astro.moon_phase_name(14.0) == "보름"
    assert astro.moon_phase_name(7.0) == "상현"
    assert astro.moon_phase_name(27.9) == "신월"  # wrap band: >= 27.68 → 신월


def test_upcoming_events_filters_and_limits(tmp_path):
    p = tmp_path / "ev.json"
    # 5 future events written OUT OF ORDER + 1 past event; n=3 forces both
    # .sort() (out-of-order input) and [:n] truncation to be exercised.
    p.write_text(
        '[{"date":"2026-12-14","name":"쌍둥이자리 유성우","type":"meteor","note":""},'
        '{"date":"2026-01-04","name":"사분의자리 유성우","type":"meteor","note":""},'
        '{"date":"2026-09-01","name":"이벤트C","type":"meteor","note":""},'
        '{"date":"2026-08-12","name":"페르세우스 유성우","type":"meteor","note":"극대"},'
        '{"date":"2026-11-01","name":"이벤트E","type":"meteor","note":""},'
        '{"date":"2026-10-01","name":"이벤트D","type":"meteor","note":""}]',
        encoding="utf-8",
    )
    got = astro.upcoming_events(datetime.date(2026, 8, 1), n=3, path=p)
    # 6 events filtered to 5 future (drops 2026-01-04), sorted ascending, then
    # truncated to the 3 earliest — proves both .sort() and [:n].
    assert [e["date"] for e in got] == ["2026-08-12", "2026-09-01", "2026-10-01"]


def test_upcoming_events_missing_file_is_empty(tmp_path):
    assert astro.upcoming_events(datetime.date(2026, 8, 1), path=tmp_path / "nope.json") == []


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
