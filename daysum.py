#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
import argparse
import datetime as dt
import os
import re
from typing import List

from probar import FIFTEEN_MINUTES, get_expected_time, probar
from timeblob import TimeBlip, TimeBlob
from util import beget_filepath, error_handler

DUMMY_DATE = (1986, 2, 21)
TIME_ENTRY_RE = re.compile(r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?')


def print_delta_line(hr1, min1, hr2, min2, delta):
    """Pretty print the time delta line."""
    delta_value = f'\u0394{str(delta):>8}'
    print(f'{hr1:02}:{min1:02}-{hr2:02}:{min2:02}{delta_value:>23}')


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


def get_week_list(date_contained: dt.date) -> List[dt.date]:
    """Return a list of dates from the week containing a provided date."""
    # Get the week and year in question
    year_iq, week_iq, _ = date_contained.isocalendar()

    # Determine the dates contained by the week in question
    date_list = list()
    for weekday in range(1, 8):
        date_in_week = dt.date.fromisocalendar(year_iq, week_iq, weekday)
        date_list.append(
            dt.date(date_in_week.year, date_in_week.month, date_in_week.day))

    return date_list


def weekly_report(date_contained: dt.date,
                  tag_sort: bool = False,
                  verbose: int = 0):
    """Generate and display the weekly report."""
    def print_workday_total(blob: TimeBlob):
        full_days = int(blob.total_work_days)
        remainder = blob.blob_total - dt.timedelta(hours=(full_days * 8))
        print(f'\nWeekly Total{full_days:>7} days {remainder}')

    date_list = get_week_list(date_contained)

    week_blob = TimeBlob()
    # Place all dates in week into a single blob
    for date in date_list:
        file_path = beget_filepath(date)
        # Only process files that exist
        if not os.path.isfile(file_path):
            continue
        # Deliniate each group of daily tags
        print(date.strftime('%a %b %d %Y'))

        daily_blob = gen_sum_with_blob(file_path,
                                       quiet=1,
                                       tag_summary=tag_sort,
                                       verbose=verbose)
        week_blob = week_blob + daily_blob

    print_workday_total(week_blob)
    probar(get_expected_time(weekly=True),
           int(week_blob.blob_total.total_seconds() / FIFTEEN_MINUTES),
           40 * 4)
    return week_blob


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

    d_in_q = dt.date(*gen_args)  # date in question

    if args.week:
        weekly_blob = weekly_report(d_in_q,
                                    tag_sort=args.tag_sort,
                                    verbose=args.verbose)
    elif args.daptiv:
        weekly_blob = weekly_report(d_in_q,
                                    tag_sort=args.tag_sort,
                                    verbose=args.verbose)
        daptiv_format(weekly_blob)
    else:
        q_val = 1 if args.quiet or args.tag_sort else 0
        blob = gen_sum_with_blob(beget_filepath(d_in_q),
                                 quiet=q_val,
                                 verbose=args.verbose)
        total_hrs = blob.blob_total.total_seconds()/3600
        print(f'{total_hrs:>28} hours')
        ex_time = get_expected_time() if d_in_q == today else 8 * 4
        probar(ex_time,
               int(blob.blob_total.total_seconds() / FIFTEEN_MINUTES),
               8 * 4)


if __name__ == '__main__':
    driver()
