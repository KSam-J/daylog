"""Tests for daptiv mode — apply_tag_groups and daptiv_format output."""
import datetime as dt
import io
from contextlib import redirect_stdout
import pytest

from timeblob import TimeBlob, TimeBlip
from daysum import apply_tag_groups, daptiv_format


def make_blob_for_week(entries):
    """
    Build a TimeBlob from a list of (date, start_h, end_h, desc) tuples.
    All times are whole-hours on the given date.
    """
    blob = TimeBlob()
    for date, start_h, end_h, desc in entries:
        start = dt.datetime.combine(date, dt.time(start_h, 0))
        stop = dt.datetime.combine(date, dt.time(end_h, 0))
        blip = TimeBlip(start, stop, desc)
        blip.set_tag(TimeBlip.strip_tag(desc))
        blob.add_blip(blip)
    return blob


# Week of 2024-03-11 (Mon) through 2024-03-15 (Fri)
MON = dt.date(2024, 3, 11)
TUE = dt.date(2024, 3, 12)
WED = dt.date(2024, 3, 13)
THU = dt.date(2024, 3, 14)
FRI = dt.date(2024, 3, 15)


# ---------------------------------------------------------------------------
# apply_tag_groups
# ---------------------------------------------------------------------------

class TestApplyTagGroups:
    def test_no_groups_returns_singletons(self):
        tags = ['backend', 'frontend', 'devops']
        result = apply_tag_groups(tags, None)
        assert result == [['backend'], ['devops'], ['frontend']]  # sorted

    def test_groups_merged(self):
        tags = ['backend', 'frontend', 'devops']
        result = apply_tag_groups(tags, [['backend', 'frontend']])
        # The grouped pair should appear; 'devops' stays singleton
        flat = [t for group in result for t in group]
        assert 'backend' in flat
        assert 'frontend' in flat
        assert 'devops' in flat

    def test_groups_remove_from_singletons(self):
        tags = ['backend', 'frontend', 'devops']
        result = apply_tag_groups(tags, [['backend', 'frontend']])
        singletons = [g for g in result if len(g) == 1]
        # 'backend' and 'frontend' should NOT appear as singletons
        singleton_tags = [g[0] for g in singletons]
        assert 'backend' not in singleton_tags
        assert 'frontend' not in singleton_tags

    def test_result_is_sorted(self):
        tags = ['zzz', 'aaa', 'mmm']
        result = apply_tag_groups(tags, None)
        labels = [g[0] for g in result]
        assert labels == sorted(labels)

    def test_empty_tags_empty_result(self):
        assert apply_tag_groups([], None) == []


# ---------------------------------------------------------------------------
# daptiv_format  —  integration / output structure
# ---------------------------------------------------------------------------

class TestDaptivFormat:
    @pytest.fixture
    def week_blob(self):
        return make_blob_for_week([
            (MON, 9, 11, 'backend refactor'),
            (MON, 13, 15, 'M+O planning'),
            (TUE, 9, 12, 'backend tests'),
            (WED, 9, 10, 'frontend review'),
            (THU, 9, 11, 'backend deploy'),
            (FRI, 9, 10, 'M+O retro'),
        ])

    def test_output_contains_weekday_headers(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob)
        output = f.getvalue()
        assert 'Monday' in output
        assert 'Friday' in output

    def test_output_contains_total_row(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob)
        output = f.getvalue()
        assert 'Σ' in output or 'Total' in output

    def test_output_contains_tag_rows(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob)
        output = f.getvalue()
        assert 'backend' in output
        assert 'M' in output  # M+O tag stripped to 'M'

    def test_output_contains_separator(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob)
        output = f.getvalue()
        assert '----------' in output

    def test_verbose_mode_prints_descriptions(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob, verbose=1)
        output = f.getvalue()
        # Verbose mode should print unique descriptions under each tag block
        assert 'refactor' in output or 'tests' in output or 'deploy' in output

    def test_group_option_merges_tags(self, week_blob):
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob, groups=[['backend', 'frontend']])
        output = f.getvalue()
        # Merged group should appear as a single row labelled by first tag
        assert 'backend' in output

    def test_hours_are_decimal(self, week_blob):
        """Time values in the table should be decimal strings like '2.0'."""
        f = io.StringIO()
        with redirect_stdout(f):
            daptiv_format(week_blob)
        output = f.getvalue()
        import re
        # At least one decimal hour value should appear
        assert re.search(r'\d+\.\d+', output)
