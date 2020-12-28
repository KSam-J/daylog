#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
import argparse
import datetime as dt
import os
import re

from util import beget_filepath, error_handler

DUMMY_DATE = (1986, 2, 21)
TIME_ENTRY_RE = re.compile(r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?')
STRIP_TAG_RE = re.compile(r'(\w*)')


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
    def tdelta(self) -> dt.timedelta:
        """Return the calculated stop - start time."""
        tdelta = self.stop - self.start
        if tdelta.days < 0:
            # Make all timedeltas be < 12 hours.
            tdelta = dt.timedelta(
                days=0, seconds=(tdelta.seconds - 60*60*12))

        return tdelta

    @staticmethod
    def strip_tag(desc):
        """Extract the tag info from a description string."""
        return re.search(STRIP_TAG_RE, desc)


class TimeBlob():
    """A loosely correlated group of TimeBlips."""

    def __init__(self):
        """Create an empty list for holding TimeBlips."""
        self.blip_list = list()
        self.tag_set = set()

    @property
    def blob_total(self):
        """Calculate the total of all blips."""
        blob_sum = dt.timedelta()
        for blip in self.blip_list:
            blob_sum += blip.tdelta

        return blob_sum

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
            print(tag)
            tag_total = 0
            for blip in self.blip_list:
                if blip.tag == tag:
                    tag_total += blip.tdelta


def print_delta_line(hr1, min1, hr2, min2, delta):
    """Pretty print the time delta line."""
    print(f'{hr1:02}:{min1:02}-{hr2:02}:{min2:02}\t\t\u0394{delta}')


def generate_summary(filename):
    """Read a logfile and generate a summary of the time log."""
    # Check existence of file
    if not os.path.isfile(filename):
        error_handler(f'File: "{filename}" does not exist.')
        return None
    # Open the log file, read only
    with open(filename, 'r') as log:
        total = dt.timedelta(0, 0, 0)
        for line in log:
            hour_search = re.search(TIME_ENTRY_RE, line)

            # On lines stating time deltas
            if hour_search:
                # Grab start time
                hour1 = int(hour_search.group(1))
                min1 = 0
                if hour_search.group(2):
                    min1 = int(hour_search.group(2))
                start_time = dt.datetime(*DUMMY_DATE, hour1, min1)
                # Grab end time
                hour2 = int(hour_search.group(3))
                min2 = 0
                if hour_search.group(4) is not None:
                    min2 = int(hour_search.group(4))
                end_time = dt.datetime(*DUMMY_DATE, hour2, min2)

                # Calculate and print Time Delta
                tdelta = end_time - start_time
                if tdelta.days < 0:
                    # Make all timedeltas be < 12 hours.
                    tdelta = dt.timedelta(
                        days=0, seconds=(tdelta.seconds - 60*60*12))
                if args.quiet == 0:
                    print_delta_line(hour1, min1, hour2, min2, tdelta)

                # Accumulate the total hours
                total += tdelta

            else:  # Description lines
                if args.verbose >= 1:
                    # Print Non-timedelta lines
                    if not re.search(r'Total:|^\n', line):
                        print(line.rstrip())

        # Convert seconds to hours
        total_hrs = total.total_seconds()/3600

    return f'{total_hrs:>32} hours'
    # TODO add flag to convert to work day scale
    # \nOR {(total_hrs)//8} work_days and {total_hrs % 8} hours'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='daysum',
        usage='%(prog)s FILENAME\n'
              '  or:  %(prog)s MONTH DAY')

    parser.add_argument(
        "file_or_month", help='numeral of month OR name of logfile', nargs='?')
    parser.add_argument(
        "day", help='numeral of day IF with month', type=int, nargs='?')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')
    parser.add_argument('-q', '--quiet', action='count', default=0,
                        help='only show total hours')

    args = parser.parse_args()
    today = dt.date.today()

    if args.file_or_month is None:
        total_str = generate_summary(beget_filepath(
            today.year, today.month, today.day))
    elif os.path.isfile(args.file_or_month):
        # Read an explicitly defined file
        total_str = generate_summary(args.file_or_month)
    else:
        # Default behavior, use month and day to determine filename
        args.file_or_month = int(args.file_or_month)
        total_str = generate_summary(beget_filepath(
            today.year, args.file_or_month, args.day))

    print(total_str)
