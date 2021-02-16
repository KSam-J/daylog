"""Contain the classes used to organize time log data."""
import datetime as dt
import re

STRIP_TAG_RE = re.compile(r'[a-zA-Z_+]*')

HOURS_IN_WDAY = 8
SECONDS_IN_HOUR = 60 * 60


class TimeBlip():
    """A single timedelta of work with metadata."""

    def __init__(self,
                 start: dt.datetime,
                 stop: dt.datetime,
                 desc: str = None,
                 tag: list() = None):
        """Populate essential timedelta and metadata."""
        self.start = start
        self.stop = stop
        self.desc = desc
        self.tag = tag
        self.dummy = False

    @property
    def date(self) -> dt.date:
        """Return the date of the blob."""
        return self.start.date()

    @property
    def tdelta(self) -> dt.timedelta:
        """Return the calculated stop - start time."""
        tdelta = self.stop - self.start
        if tdelta.days < 0:
            # Make all timedeltas be < 12 hours.
            tdelta = dt.timedelta(
                days=0, seconds=(tdelta.seconds - 60*60*12))

        return tdelta

    def set_tag(self, tag):
        """Set the tag value."""
        self.tag = tag

    @staticmethod
    def strip_tag(desc):
        """Extract the tag info from a description string."""
        return re.search(STRIP_TAG_RE, desc).group(0)


class TimeBlob():
    """A loosely correlated group of TimeBlips."""

    def __init__(self, blip_list=None, tag_set=None):
        """Create an empty list for holding TimeBlips."""
        self.blip_list = blip_list if blip_list else list()
        self.tag_set = tag_set if tag_set else set()

    @property
    def blob_total(self) -> dt.timedelta:
        """Calculate the total of all blips."""
        blob_sum = dt.timedelta()
        for blip in self.blip_list:
            blob_sum += blip.tdelta

        return blob_sum

    @property
    def total_work_days(self) -> float:
        """Return the blob_total in work days and hours."""
        # Calculate work days
        work_days = (self.blob_total.total_seconds() / SECONDS_IN_HOUR) \
            / HOURS_IN_WDAY
        return work_days

    def __add__(self, other_blob):
        """Allow addition of Blobs."""
        blips = self.blip_list + other_blob.blip_list
        tags = self.tag_set.union(other_blob.tag_set)
        return TimeBlob(blips, tags)

    def add_blip(self, blip: TimeBlip):
        """Add the blip to the list and perform accounting actions."""
        self.tag_set.add(blip.tag)
        self.blip_list.append(blip)

    def print_total(self):
        """Print the grand total to stdout."""
        print(self.blob_total)

    def print_tag_totals(self):
        """Print the totals of each tag."""
        for tag in self.tag_set:
            print(f'{tag:>20}', end='')
            tag_total = dt.timedelta()
            for blip in self.blip_list:
                if blip.tag == tag:
                    tag_total += blip.tdelta
            print(f'    {str(tag_total):>8}')
