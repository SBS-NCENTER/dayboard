import datetime

from dayboard.calendar_data import month_grid


def test_grid_marks_today_and_holiday():
    today = datetime.date(2026, 3, 1)  # 삼일절
    g = month_grid(2026, 3, today)
    assert g["year"] == 2026 and g["month"] == 3
    # 실제 날짜 셀만 모아서 검사
    cells = [c for wk in g["weeks"] for c in wk if c["day"] is not None]
    assert len(cells) == 31  # 3월 = 31일
    mar1 = next(c for c in cells if c["day"] == 1)
    assert mar1["is_today"] is True
    assert mar1["holiday"] == "삼일절"
    mar3 = next(c for c in cells if c["day"] == 3)
    assert mar3["is_today"] is False and mar3["holiday"] is None


def test_grid_weeks_are_seven_wide():
    g = month_grid(2026, 3, datetime.date(2026, 3, 1))
    assert all(len(wk) == 7 for wk in g["weeks"])
