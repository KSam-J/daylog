"""Tests for probar.py — progress bar logic and expected-time calculation."""
import datetime as dt
from unittest.mock import patch, MagicMock
import io
import pytest

from probar import get_expected_time, UNITS_PER_DAY, FIFTEEN_MINUTES, PHOENIX_TZ
from daysum import compact_probar
from timeblob import TimeBlob, TimeBlip


import re


# Strip ANSI escape codes and tmux style tags for assertion-friendly comparisons
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_TMUX_RE = re.compile(r'#\[[^\]]*\]')

def strip_ansi(s: str) -> str:
    return _TMUX_RE.sub('', _ANSI_RE.sub('', s))


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
    def test_zero_hours_label(self):
        result = strip_ansi(compact_probar(make_blob_with_hours(0)))
        assert result == '0.00 hrs'

    def test_four_hours_label(self):
        result = strip_ansi(compact_probar(make_blob_with_hours(4)))
        assert result == '4.00 hrs'

    def test_fractional_hours_label(self):
        result = strip_ansi(compact_probar(make_blob_with_hours(4.5)))
        assert result == '4.50 hrs'

    def test_eight_hours_label(self):
        result = strip_ansi(compact_probar(make_blob_with_hours(8)))
        assert result == '8.00 hrs'

    def test_over_eight_hours_capped(self):
        result = strip_ansi(compact_probar(make_blob_with_hours(9)))
        assert result == '8.00 hrs'

    def test_always_eight_visible_chars(self):
        for h in [0, 1, 3, 4.5, 7.25, 8, 10]:
            result = strip_ansi(compact_probar(make_blob_with_hours(h)))
            assert len(result) == 8, f'Expected 8 visible chars at {h}h, got {len(result)}: {result!r}'

    def test_ansi_mode_contains_escape_codes(self, monkeypatch):
        monkeypatch.delenv('TMUX', raising=False)
        result = compact_probar(make_blob_with_hours(4))
        assert '\x1b[' in result

    def test_ansi_mode_filled_chars_match_whole_hours(self, monkeypatch):
        monkeypatch.delenv('TMUX', raising=False)
        FILLED_SEQ = '\x1b[42m\x1b[97m'
        for whole_h in range(0, 9):
            result = compact_probar(make_blob_with_hours(whole_h))
            filled_count = result.count(FILLED_SEQ)
            assert filled_count == whole_h, f'At {whole_h}h: expected {whole_h} filled seqs, got {filled_count}'

    def test_tmux_mode_uses_hash_bracket_syntax(self, monkeypatch):
        monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
        result = compact_probar(make_blob_with_hours(4))
        assert '#[' in result
        assert '\x1b[' not in result

    def test_tmux_mode_label_correct(self, monkeypatch):
        monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
        import re
        visible = re.sub(r'#\[[^\]]*\]', '', compact_probar(make_blob_with_hours(5.5)))
        assert visible == '5.50 hrs'

    def test_tmux_mode_custom_filled_colour(self, monkeypatch):
        monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
        result = compact_probar(make_blob_with_hours(4), filled='blue')
        assert 'bg=blue' in result

    def test_tmux_mode_custom_empty_colour(self, monkeypatch):
        monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
        result = compact_probar(make_blob_with_hours(4), empty='colour52')
        assert 'bg=colour52' in result


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
