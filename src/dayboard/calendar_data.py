"""이번달 그리드 + 한국 공휴일(오프라인)."""
import calendar
import datetime

import holidays


def month_grid(year: int, month: int, today: datetime.date) -> dict:
    kr = holidays.SouthKorea(years=year, language="ko")
    cal = calendar.Calendar(firstweekday=0)  # 0 = 월요일
    weeks = []
    for week in cal.monthdayscalendar(year, month):  # 0 = 빈칸
        row = []
        for wd, day in enumerate(week):
            if day == 0:
                row.append({"day": None, "is_today": False, "holiday": None, "weekday": wd})
            else:
                d = datetime.date(year, month, day)
                row.append({
                    "day": day,
                    "is_today": d == today,
                    "holiday": kr.get(d),
                    "weekday": wd,
                })
        weeks.append(row)
    return {"year": year, "month": month, "weeks": weeks}
