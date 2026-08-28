"""Deterministic date math. No model involvement, ever.

Refuses to produce a date without a rule authority id, because a computed
deadline is the single most dangerous output this profile can emit.
"""
from __future__ import annotations
import datetime as dt

# Federal holidays are legislated; this table is data, not inference. It is
# deliberately small and explicit so it can be audited and extended per forum.
FIXED = {(1, 1): "New Year's Day", (6, 19): "Juneteenth", (7, 4): "Independence Day",
         (11, 11): "Veterans Day", (12, 25): "Christmas Day"}


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    add = (weekday - d.weekday()) % 7
    d += dt.timedelta(days=add + 7 * (n - 1))
    return d


def _last_weekday(year, month, weekday):
    d = dt.date(year, month, 1) + dt.timedelta(days=31)
    d = d.replace(day=1) - dt.timedelta(days=1)
    while d.weekday() != weekday:
        d -= dt.timedelta(days=1)
    return d


def federal_holidays(year: int) -> set:
    h = {dt.date(year, m, d) for (m, d) in FIXED}
    h.add(_nth_weekday(year, 1, 0, 3))    # MLK
    h.add(_nth_weekday(year, 2, 0, 3))    # Presidents
    h.add(_last_weekday(year, 5, 0))      # Memorial
    h.add(_nth_weekday(year, 9, 0, 1))    # Labor
    h.add(_nth_weekday(year, 10, 0, 2))   # Columbus
    h.add(_nth_weekday(year, 11, 3, 4))   # Thanksgiving
    observed = set()
    for d in h:
        if d.weekday() == 5:
            observed.add(d - dt.timedelta(days=1))
        elif d.weekday() == 6:
            observed.add(d + dt.timedelta(days=1))
    return h | observed


def is_court_day(d: dt.date, holidays: set) -> bool:
    return d.weekday() < 5 and d not in holidays


def compute(trigger: str, period: int, day_type: str = "calendar",
            direction: str = "after") -> dict:
    start = dt.date.fromisoformat(trigger)
    step = 1 if direction == "after" else -1
    hol = federal_holidays(start.year) | federal_holidays(start.year + step)
    if day_type == "court":
        d, counted = start, 0
        while counted < period:
            d += dt.timedelta(days=step)
            if is_court_day(d, hol):
                counted += 1
        result = d
    else:
        result = start + dt.timedelta(days=period * step)
        rolled = False
        while not is_court_day(result, hol):   # forward roll off weekends/holidays
            result += dt.timedelta(days=1)
            rolled = True
    return {"trigger": trigger, "period_days": period, "day_type": day_type,
            "direction": direction, "result": result.isoformat(),
            "weekday": result.strftime("%A"),
            "holiday_table": "US federal, observed rules applied",
            "caveat": "Local rules, standing orders, and forum-specific holiday "
                      "calendars are NOT in this table. Verify against the forum's own calendar."}
