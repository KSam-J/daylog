#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
import argparse
import datetime as dt
import os
import re

from util import beget_filepath, error_handler

DUMMY_DATE = (1986, 2, 21)
TIME_ENTRY_RE = re.compile(r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?')
STRIP_TAG_RE = re.compile(r'[a-zA-Z_+]*')


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
    def blob_total(self):
        """Calculate the total of all blips."""
        blob_sum = dt.timedelta()
        for blip in self.blip_list:
            blob_sum += blip.tdelta

        return blob_sum

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


def print_delta_line(hr1, min1, hr2, min2, delta):
    """Pretty print the time delta line."""
    print(f'{hr1:02}:{min1:02}-{hr2:02}:{min2:02}\t\t\u0394{delta}')


def gen_sum_with_blob(filename,
                      blob: TimeBlob = None,
                      quiet: int = 0,
                      verbose: int = 0,
                      tag_summary: bool = False):
    """Read a logfile and generate a summary of the time log."""
    # Check existence of file
    if not os.path.isfile(filename):
        error_handler(f'File: "{filename}" does not exist.')
        return None

    if blob is None:
        blob = TimeBlob()

    # Begin transfering text info to TimeBlob data stucture
    with open(filename, 'r') as log:
        purgatory_blip = None

        for line in log:
            hour_search = re.match(TIME_ENTRY_RE, line)

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

                purgatory_blip = TimeBlip(start_time, end_time)

                # Calculate and print Time Delta
                if quiet == 0:
                    print_delta_line(hour1, min1, hour2, min2,
                                     purgatory_blip.tdelta)

            else:  # Description lines
                if isinstance(purgatory_blip, TimeBlip):
                    purgatory_blip.desc = line.strip()
                    purgatory_blip.set_tag(TimeBlip.strip_tag(line.strip()))

                    # Add the Blip to the Blob
                    blob.add_blip(purgatory_blip)
                    purgatory_blip = None
                    if verbose >= 1:
                        # Print Non-timedelta lines
                        if not re.search(r'Total:|^\n', line):
                            print(line.rstrip())

    if tag_summary:
        blob.print_tag_totals()

    return blob


def weekly_report(date_contained: dt.date,
                  tag_sort: bool = False,
                  verbose: int = 0):
    """Generate and display the weekly report."""
    # Get the week and year in question
    year_iq, week_iq, _ = date_contained.isocalendar()

    # Determine the dates contained by the week in question
    date_list = list()
    for weekday in range(1, 8):
        date_in_week = dt.date.fromisocalendar(year_iq, week_iq, weekday)
        date_list.append(
            (date_in_week.year, date_in_week.month, date_in_week.day))

    week_blob = TimeBlob()
    # Place all dates in week into a single blob
    for date in date_list:
        # Only process files that exist
        if not os.path.isfile(beget_filepath(*date)):
            continue
        # Deliniate each group of daily tags
        print(dt.date(*date).strftime('%a %b %d %Y'))

        gen_sum_with_blob(beget_filepath(*date),
                          week_blob,
                          quiet=1,
                          tag_summary=tag_sort,
                          verbose=verbose)

    return f'\nWeekly Total{str(week_blob.blob_total):>20}'


def driver():
    """Contain the arg parser and perform main functions."""
    today = dt.date.today()

    parser = argparse.ArgumentParser(
        prog='daysum',
        usage='%(prog)s FILENAME\n'
              '  or:  %(prog)s MONTH DAY')

    parser.add_argument(
        "file_or_month", help='numeral of month OR name of logfile', nargs='?')
    parser.add_argument(
        "day", help='numeral of day IF with month', type=int, nargs='?')
    parser.add_argument("year",
                        help='numeral of year',
                        type=int,
                        nargs='?',
                        default=today.year)

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')
    parser.add_argument('-q', '--quiet', action='count', default=0,
                        help='only show total hours')
    parser.add_argument('-x', '--experimental', action='store_true',
                        help='count using the blob data format')
    parser.add_argument('-t', '--tag_sort', action='store_true',
                        help='display timedeltas organized by tag')
    parser.add_argument('-w', '--week', action='store_true',
                        help='display the weekly report')

    args = parser.parse_args()

    # Determine the argument types for the gen_sum function
    gen_args = list()
    if args.file_or_month is None:
        gen_args = [today.year, today.month, today.day]
    elif os.path.isfile(args.file_or_month):
        # Read an explicitly defined file
        gen_args.append(args.file_or_month)
    else:
        # Default behavior, use month and day to determine filename
        args.file_or_month = int(args.file_or_month)
        gen_args = [args.year, args.file_or_month, args.day]

    if not args.week:
        q_val = 1 if args.quiet or args.tag_sort else 0
        blob = gen_sum_with_blob(beget_filepath(*gen_args),
                                 quiet=q_val,
                                 verbose=args.verbose)
        total_hrs = blob.blob_total.total_seconds()/3600
        total_str = f'{total_hrs:>32} hours'
    else:
        total_str = weekly_report(dt.date(*gen_args),
                                  tag_sort=args.tag_sort,
                                  verbose=args.verbose)

    print(total_str)


if __name__ == '__main__':
    driver()
