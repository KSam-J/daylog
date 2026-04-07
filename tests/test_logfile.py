"""Tests for logfile parsing (log_2_blob) and util date helpers."""
import datetime as dt
import os
import pytest

from logfile import log_2_blob
from util import beget_date, beget_filepath


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


# ---------------------------------------------------------------------------
# beget_date
# ---------------------------------------------------------------------------

class TestBegetDate:
    def test_iso_format(self):
        assert beget_date('2024-03-11') == dt.date(2024, 3, 11)

    def test_iso_format_with_extension(self):
        assert beget_date('2024-01-01.txt') == dt.date(2024, 1, 1)

    def test_back_compat_format(self):
        result = beget_date('log03_11.txt')
        assert result == dt.date(2021, 3, 11)

    def test_unrecognised_returns_none(self):
        assert beget_date('notes.txt') is None

    def test_unrecognised_plain_text(self):
        assert beget_date('somelogfile') is None


# ---------------------------------------------------------------------------
# beget_filepath
# ---------------------------------------------------------------------------

class TestBegetFilepath:
    def test_path_contains_year_and_month(self):
        path = beget_filepath(dt.date(2024, 3, 11))
        assert '2024' in path
        assert 'Mar' in path

    def test_path_contains_log_filename(self):
        path = beget_filepath(dt.date(2024, 3, 11))
        assert 'log03_11.txt' in path


# ---------------------------------------------------------------------------
# log_2_blob  —  round-trip parse of the sample fixture
# ---------------------------------------------------------------------------

class TestLog2Blob:
    def test_parses_all_entries(self, sample_log_path, sample_date):
        blob = log_2_blob(sample_log_path, sample_date)
        assert len(blob.blip_list) == 7

    def test_total_is_seven_hours(self, sample_log_path, sample_date):
        """9-10, 10-11:30, 11:30-12, 13-14:30, 14:30-16, 16-17 = 7h."""
        blob = log_2_blob(sample_log_path, sample_date)
        assert blob.blob_total == dt.timedelta(hours=7,minutes=30)

    def test_tags_extracted(self, sample_log_path, sample_date):
        blob = log_2_blob(sample_log_path, sample_date)
        assert 'M+O' in blob.tag_set  # STRIP_TAG_RE includes '+', so M+O is a single tag
        assert 'backend' in blob.tag_set

    def test_descriptions_set(self, sample_log_path, sample_date):
        blob = log_2_blob(sample_log_path, sample_date)
        descs = [b.desc for b in blob.blip_list]
        assert 'M+O meeting with team' in descs

    def test_date_set_is_sample_date(self, sample_log_path, sample_date):
        blob = log_2_blob(sample_log_path, sample_date)
        assert blob.date_set == {sample_date}


# ---------------------------------------------------------------------------
# Open-ended entry  (the  "HH-"  syntax)
# ---------------------------------------------------------------------------

class TestOpenEndedEntry:
    def _write_logfile(self, tmp_path, content):
        f = tmp_path / 'open_log.txt'
        f.write_text(content)
        return str(f)

    def test_open_entry_uses_current_time(self, tmp_path):
        """End time should be close to now (within 5 seconds)."""
        content = '9-\nbackend work\n'
        path = self._write_logfile(tmp_path, content)
        date = dt.date.today()
        before = dt.datetime.now()
        blob = log_2_blob(path, date)
        after = dt.datetime.now()

        assert len(blob.blip_list) == 1
        end = blob.blip_list[0].stop
        assert before <= end <= after

    def test_open_entry_capped_at_eight_hours(self, tmp_path):
        """If 7h are already logged, the open entry can add at most 1h."""
        lines = []
        for h in range(7):
            lines.append(f'{h}-{h+1}')
            lines.append('task work')
        lines.append('15-')   # start at 15:00, no end
        lines.append('task work')
        content = '\n'.join(lines) + '\n'
        path = self._write_logfile(tmp_path, content)
        date = dt.date.today()
        blob = log_2_blob(path, date)

        total_seconds = blob.blob_total.total_seconds()
        assert total_seconds <= 8 * 3600 + 1  # allow 1s float tolerance

    def test_open_entry_already_at_eight_hours(self, tmp_path):
        """If 8h are already logged, the open entry should add zero time."""
        lines = []
        for h in range(8):
            lines.append(f'{h}-{h+1}')
            lines.append('task work')
        lines.append('8-')
        lines.append('task extra')
        content = '\n'.join(lines) + '\n'
        path = self._write_logfile(tmp_path, content)
        date = dt.date.today()
        blob = log_2_blob(path, date)

        total_seconds = blob.blob_total.total_seconds()
        assert total_seconds <= 8 * 3600 + 1
