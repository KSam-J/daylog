"""Tests for probar.py — progress bar logic and expected-time calculation."""
import datetime as dt
from unittest.mock import patch, MagicMock
import io
import pytest

from probar import get_expected_time, UNITS_PER_DAY, FIFTEEN_MINUTES, PHOENIX_TZ
from daysum import compact_probar
from timeblob import TimeBlob, TimeBlip


# ---------------------------------------------------------------------------
# compact_probar
# ---------------------------------------------------------------------------

def make_blob_with_hours(hours: float) -> TimeBlob:
    blob = TimeBlob()
    seconds = int(hours * 3600)
    start = dt.datetime(2024, 3, 11, 9, 0)
    stop = start + dt.timedelta(seconds=seconds)
    blip = TimeBlip(start, stop, 'work tag')
    blip.set_tag('work')
    blob.add_blip(blip)
    return blob


class TestCompactProbar:
    def test_zero_hours(self):
        result = compact_probar(make_blob_with_hours(0))
        assert result == '⣀' * 8

    def test_four_hours(self):
        result = compact_probar(make_blob_with_hours(4))
        assert result == '⣿' * 4 + '⣀' * 4

    def test_eight_hours(self):
        result = compact_probar(make_blob_with_hours(8))
        assert result == '⣿' * 8

    def test_over_eight_hours_capped(self):
        """More than 8h should still show full bar."""
        result = compact_probar(make_blob_with_hours(9))
        assert result == '⣿' * 8

    def test_always_eight_chars(self):
        for h in [0, 1, 3, 5, 7, 8, 10]:
            result = compact_probar(make_blob_with_hours(h))
            assert len(result) == 8


# ---------------------------------------------------------------------------
# get_expected_time
# ---------------------------------------------------------------------------

def _fake_now(hour, minute=0, second=0):
    """Return a datetime in Phoenix TZ at the given time today."""
    today = dt.date.today()
    return dt.datetime(today.year, today.month, today.day,
                       hour, minute, second, tzinfo=PHOENIX_TZ)


class TestGetExpectedTime:
    def test_before_start_of_day(self):
        """Before 9:30 the function counts abs distance to start — at 8:00 that's 6 units."""
        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(8, 0)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            result = get_expected_time()
        assert result == 6  # abs(9:30 - 8:00) = 90 min = 6 × 15-min units

    def test_at_start_of_day(self):
        """Exactly at 9:30 the expected elapsed time is zero."""
        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(9, 30)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            result = get_expected_time()
        assert result == 0

    def test_at_end_of_day_cap(self):
        """After 18:30 the result should be capped at UNITS_PER_DAY (32)."""
        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(19, 30)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            result = get_expected_time()
        assert result == UNITS_PER_DAY

    def test_lunch_break_offset(self):
        """During lunch the offset boosts expected; after 1pm it subtracts 4 units."""
        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(12, 30)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            result_during_lunch = get_expected_time()

        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(13, 30)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            result_after_lunch = get_expected_time()

        # After 1pm the full 4-unit lunch offset is applied; during lunch it is partial
        assert result_during_lunch > result_after_lunch

    def test_weekly_mode_multiplies_days(self):
        """Weekly mode should produce a result >= daily result."""
        with patch('probar.dt') as mock_dt:
            mock_dt.datetime.now.return_value = _fake_now(14, 0)
            mock_dt.datetime.side_effect = lambda *a, **kw: dt.datetime(*a, **kw)
            mock_dt.date.today.return_value = dt.date.today()
            mock_dt.timedelta = dt.timedelta
            daily = get_expected_time(weekly=False)
            weekly = get_expected_time(weekly=True)
        assert weekly >= daily
