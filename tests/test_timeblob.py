"""Tests for TimeBlip and TimeBlob classes."""
import datetime as dt
import pytest

from timeblob import TimeBlip, TimeBlob


def make_blip(start_h, start_m, end_h, end_m, desc='work tag', date=None):
    """Helper to build a TimeBlip on an arbitrary date."""
    d = date or dt.date(2024, 3, 11)
    start = dt.datetime.combine(d, dt.time(start_h, start_m))
    stop = dt.datetime.combine(d, dt.time(end_h, end_m))
    blip = TimeBlip(start, stop, desc)
    blip.set_tag(TimeBlip.strip_tag(desc))
    return blip


# ---------------------------------------------------------------------------
# TimeBlip
# ---------------------------------------------------------------------------

class TestTimeBlip:
    def test_tdelta_whole_hours(self):
        blip = make_blip(9, 0, 10, 0)
        assert blip.tdelta == dt.timedelta(hours=1)

    def test_tdelta_with_minutes(self):
        blip = make_blip(9, 30, 11, 0)
        assert blip.tdelta == dt.timedelta(hours=1, minutes=30)

    def test_tdelta_zero(self):
        blip = make_blip(9, 0, 9, 0)
        assert blip.tdelta == dt.timedelta(0)

    def test_date_property(self):
        blip = make_blip(9, 0, 10, 0, date=dt.date(2024, 3, 11))
        assert blip.date == dt.date(2024, 3, 11)

    def test_strip_tag_single_word(self):
        assert TimeBlip.strip_tag('backend refactor') == 'backend'

    def test_strip_tag_underscore(self):
        assert TimeBlip.strip_tag('code_review nits') == 'code_review'

    def test_tag_set_on_blip(self):
        blip = make_blip(9, 0, 10, 0, desc='backend refactor work')
        assert blip.tag == 'backend'


# ---------------------------------------------------------------------------
# TimeBlob
# ---------------------------------------------------------------------------

class TestTimeBlob:
    def test_empty_blob_total(self):
        blob = TimeBlob()
        assert blob.blob_total == dt.timedelta(0)

    def test_single_blip_total(self):
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0))
        assert blob.blob_total == dt.timedelta(hours=1)

    def test_multiple_blip_total(self):
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0))   # 1h
        blob.add_blip(make_blip(10, 0, 11, 30))  # 1.5h
        assert blob.blob_total == dt.timedelta(hours=2, minutes=30)

    def test_add_blobs(self):
        blob1 = TimeBlob()
        blob1.add_blip(make_blip(9, 0, 10, 0))
        blob2 = TimeBlob()
        blob2.add_blip(make_blip(13, 0, 14, 0))
        combined = blob1 + blob2
        assert combined.blob_total == dt.timedelta(hours=2)

    def test_tag_set_populated(self):
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0, desc='backend work'))
        blob.add_blip(make_blip(10, 0, 11, 0, desc='frontend work'))
        assert 'backend' in blob.tag_set
        assert 'frontend' in blob.tag_set

    def test_sub_blob_single_day(self):
        d1 = dt.date(2024, 3, 11)
        d2 = dt.date(2024, 3, 12)
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0, date=d1))
        blob.add_blip(make_blip(9, 0, 10, 0, date=d2))
        sub = blob.sub_blob(d1)
        assert sub.blob_total == dt.timedelta(hours=1)

    def test_date_set(self):
        d1 = dt.date(2024, 3, 11)
        d2 = dt.date(2024, 3, 12)
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0, date=d1))
        blob.add_blip(make_blip(9, 0, 10, 0, date=d2))
        assert blob.date_set == {d1, d2}

    def test_filter_by_tag(self):
        blob = TimeBlob()
        blob.add_blip(make_blip(9, 0, 10, 0, desc='backend work'))
        blob.add_blip(make_blip(10, 0, 11, 0, desc='frontend work'))
        filtered = blob.filter_by(['backend'])
        assert filtered.blob_total == dt.timedelta(hours=1)
        assert 'frontend' not in filtered.tag_set

    def test_total_work_days(self):
        blob = TimeBlob()
        for hour in range(8):
            blob.add_blip(make_blip(hour, 0, hour + 1, 0))
        assert blob.total_work_days == pytest.approx(1.0)
