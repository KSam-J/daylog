"""Tests for every regex pattern defined in the daylog codebase."""
import re
import pytest

from logfile import TIME_ENTRY_RE, TIME_BLOCK_RE
from util import ISO_FMT_RE, BACK_COMPAT_RE
from timeblob import STRIP_TAG_RE


# ---------------------------------------------------------------------------
# TIME_ENTRY_RE  —  matches time-range lines like  9-17  or  9:30-17:00
# ---------------------------------------------------------------------------

class TestTimeEntryRe:
    def test_simple_hour_range(self):
        m = re.match(TIME_ENTRY_RE, '8-17')
        assert m and m.group(1) == '8' and m.group(3) == '17'

    def test_hour_and_minute_range(self):
        m = re.match(TIME_ENTRY_RE, '9:30-17:00')
        assert m
        assert m.group(1) == '9'
        assert m.group(2) == '30'
        assert m.group(3) == '17'
        assert m.group(4) == '00'

    def test_start_only_minutes(self):
        """Start time has minutes; end does not."""
        m = re.match(TIME_ENTRY_RE, '9:30-17')
        assert m and m.group(2) == '30' and m.group(3) == '17' and m.group(4) is None

    def test_open_ended_no_end_time(self):
        """The trailing dash with no end — open-ended entry syntax."""
        m = re.match(TIME_ENTRY_RE, '8-')
        assert m is not None
        assert m.group(1) == '8'
        assert m.group(3) is None

    def test_open_ended_with_minutes(self):
        m = re.match(TIME_ENTRY_RE, '9:00-')
        assert m is not None
        assert m.group(1) == '9'
        assert m.group(2) == '00'
        assert m.group(3) is None

    def test_two_digit_hours(self):
        m = re.match(TIME_ENTRY_RE, '10-18')
        assert m and m.group(1) == '10' and m.group(3) == '18'

    def test_no_match_plain_text(self):
        assert re.match(TIME_ENTRY_RE, 'some description') is None

    def test_no_match_no_dash(self):
        """A plain number without a dash should not match."""
        assert re.match(TIME_ENTRY_RE, '930') is None

    def test_no_match_empty_string(self):
        assert re.match(TIME_ENTRY_RE, '') is None


# ---------------------------------------------------------------------------
# TIME_BLOCK_RE  —  matches block-total lines like  8  or  7.5
# ---------------------------------------------------------------------------

class TestTimeBlockRe:
    def test_whole_hour(self):
        m = re.match(TIME_BLOCK_RE, '8')
        assert m and m.group(1) == '8'

    def test_decimal_hour(self):
        m = re.match(TIME_BLOCK_RE, '7.5')
        assert m and m.group(1) == '7' and m.group(2) == '5'

    def test_two_digit_hour(self):
        m = re.match(TIME_BLOCK_RE, '10')
        assert m and m.group(1) == '10'

    def test_no_match_time_range(self):
        """A time range like 8-17 should NOT match the block regex."""
        assert re.match(TIME_BLOCK_RE, '8-17') is None

    def test_no_match_text(self):
        assert re.match(TIME_BLOCK_RE, 'backend work') is None

    def test_no_match_empty(self):
        assert re.match(TIME_BLOCK_RE, '') is None


# ---------------------------------------------------------------------------
# ISO_FMT_RE  —  matches YYYY-MM-DD dates in filenames
# ---------------------------------------------------------------------------

class TestIsoFmtRe:
    def test_valid_iso_date(self):
        m = re.match(ISO_FMT_RE, '2024-03-11')
        assert m and m.group(0) == '2024-03-11'

    def test_valid_in_filename(self):
        m = re.match(ISO_FMT_RE, '2024-01-01.txt')
        assert m and m.group(0) == '2024-01-01'

    def test_year_1900s(self):
        m = re.match(ISO_FMT_RE, '1999-12-31')
        assert m and m.group(0) == '1999-12-31'

    def test_no_match_wrong_year_prefix(self):
        """Years outside 19xx/20xx should not match."""
        assert re.match(ISO_FMT_RE, '2100-01-01') is None

    def test_no_match_plain_text(self):
        assert re.match(ISO_FMT_RE, 'logfile.txt') is None

    def test_no_match_partial_date(self):
        assert re.match(ISO_FMT_RE, '2024-03') is None


# ---------------------------------------------------------------------------
# BACK_COMPAT_RE  —  matches legacy filenames like log03_11.txt
# ---------------------------------------------------------------------------

class TestBackCompatRe:
    def test_valid_back_compat(self):
        m = re.match(BACK_COMPAT_RE, 'log03_11.txt')
        assert m and m.group(1) == '03' and m.group(2) == '11'

    def test_valid_december(self):
        m = re.match(BACK_COMPAT_RE, 'log12_31.txt')
        assert m and m.group(1) == '12' and m.group(2) == '31'

    def test_no_match_iso_filename(self):
        assert re.match(BACK_COMPAT_RE, '2024-03-11.txt') is None

    def test_no_match_missing_extension(self):
        assert re.match(BACK_COMPAT_RE, 'log03_11') is None

    def test_no_match_wrong_prefix(self):
        assert re.match(BACK_COMPAT_RE, 'file03_11.txt') is None


# ---------------------------------------------------------------------------
# STRIP_TAG_RE  —  extracts the leading word (tag) from a description
# ---------------------------------------------------------------------------

class TestStripTagRe:
    def test_single_word_tag(self):
        m = re.search(STRIP_TAG_RE, 'backend refactor')
        assert m and m.group(0) == 'backend'

    def test_plus_separated_tag(self):
        """STRIP_TAG_RE includes '+', so M+O is captured as a single token."""
        m = re.search(STRIP_TAG_RE, 'M+O meeting with team')
        assert m and m.group(0) == 'M+O'

    def test_underscore_in_tag(self):
        m = re.search(STRIP_TAG_RE, 'code_review changes')
        assert m and m.group(0) == 'code_review'

    def test_empty_string(self):
        m = re.search(STRIP_TAG_RE, '')
        # Should match an empty string at position 0 (zero-length match)
        assert m is not None
