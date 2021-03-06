#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from typing import List

from tabulate import tabulate

from probar import FIFTEEN_MINUTES, UNITS_PER_DAY, get_expected_time, probar
from timeblob import TimeBlip, TimeBlob
from util import beget_date, beget_filepath, error_handler

DUMMY_DATE = (1986, 2, 21)
TIME_ENTRY_RE = re.compile(r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?')


def print_delta_line(hr1, min1, hr2, min2, delta):
    """Pretty print the time delta line."""
    delta_value = f'\u0394{str(delta):>8}'
    print(f'{hr1:02}:{min1:02}-{hr2:02}:{min2:02}{delta_value:>23}')


def log_2_blob(filename: str, date: dt.date | None = None) -> TimeBlob:
    """Scan a log file and place the data in a TimeBlip."""
    # Check existence of file
    blob = None
    if not os.path.isfile(filename):
        error_handler(f'File: "{filename}" does not exist.')

    # Determine the date corresponding to filename
    if not date:
        date = beget_date(filename)
        # second date check required until beget_date has back compat check
        if not date:
            date = dt.date(*DUMMY_DATE)

    # Begin transfering text info to TimeBlob data stucture
    with open(filename, 'r') as log:
        blob = TimeBlob()
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
                start_time = dt.datetime.combine(date, dt.time(hour1, min1))
                # Grab end time
                hour2 = int(hour_search.group(3))
                min2 = 0
                if hour_search.group(4) is not None:
                    min2 = int(hour_search.group(4))
                end_time = dt.datetime.combine(date, dt.time(hour2, min2))

                purgatory_blip = TimeBlip(start_time, end_time)

            else:  # Description lines
                if isinstance(purgatory_blip, TimeBlip):
                    purgatory_blip.desc = line.strip()
                    purgatory_blip.set_tag(TimeBlip.strip_tag(line.strip()))

                    # Add the Blip to the Blob
                    blob.add_blip(purgatory_blip)
                    # Reset the purgatory_blip for the next delta,desc pair
                    purgatory_blip = None
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


def get_week_blob(date_contained: dt.date):
    """Place a week's worth of logs into a blob."""
    date_list = get_week_list(date_contained)

    week_blob = TimeBlob()
    # Place all dates in week into a single blob
    for date in date_list:
        file_path = beget_filepath(date)
        # Only process files that exist
        if not os.path.isfile(file_path):
            continue

        daily_blob = log_2_blob(file_path, date)
        week_blob = week_blob + daily_blob

    return week_blob


def weekly_report(date_contained: dt.date,
                  tag_sort: bool = False,
                  verbose: int = 0) -> None:
    """Generate and display the weekly report."""
    def print_workday_total(blob: TimeBlob):
        full_days = int(blob.total_work_days)
        remainder = blob.blob_total - dt.timedelta(hours=(full_days * 8))
        print(f'\nWeekly Total{full_days:>7} days {remainder}')

    week_blob = get_week_blob(date_contained)

    for day in get_week_list(date_contained):
        daily_total = week_blob.sub_blob(day).blob_total
        if daily_total > dt.timedelta(0):
            print(day.strftime('%a %b %d %Y'), end='')
            print(f'{"":10}{daily_total}')

    print_workday_total(week_blob)
    probar(get_expected_time(weekly=True),
           int(week_blob.blob_total.total_seconds() / FIFTEEN_MINUTES),
           40 * 4)


def daptiv_format(blob: TimeBlob,
                  groups: List[List[str]] = None) -> None:
    """Display tdeltas and descriptions in a format for transfer to daptiv.

    Assume that the blob only contains dates from a single week (M-Sun).
    """

    def get_table_header(date_list: List[dt.date]) -> List[str]:
        """Return a list with each table header for tabulate."""
        # Check that all dates are in the same week
        iso_week = None
        for date in date_list:
            _, week_num, _ = date.isocalendar()
            if not iso_week:
                iso_week = week_num
            elif iso_week != week_num:
                raise ValueError('Received dates from different iso-weeks')

        header_list = list()
        days_in_week = get_week_list(date_list[0])
        # Print out the Weekly header
        for date in days_in_week:
            day = date.strftime('%A')
            day += f'\n{str(date)}'
            header_list.append(day)

        # Prepend an empty str to account for Y-axis labels
        header_list = [''] + header_list

        return header_list

    vector_list = list()
    # Segregate blobs by tag and filter the descriptions

    # Apply tag groups
    singelton_tags = list(blob.tag_set.copy())
    # Strip tags in groups from singelton list
    for group in groups:
        for tag in group:
            singelton_tags.remove(tag)
    # Merge singelton and grouped tags for printing structure
    tag_groups = [[tag] for tag in singelton_tags] + groups
    tag_groups = sorted(tag_groups)

    for tag_list in tag_groups:
        # Print the descriptions, w/o repeated tag
        print("\nTag: ", tag_list[0], '----------------')
        filtered_blob = blob.filter_by(tag_list)

        # Collect the descriptions
        desc_set = set()
        for blip in filtered_blob.blip_list:
            # Only print if there is a detailed description
            if len(blip.desc) > len(blip.tag)+1:
                desc_set.add(blip.desc[len(blip.tag)+1:])
        # Print the descriptions
        for desc in desc_set:
            print(desc)
        # Organize the dates in chronological order
        tag_dates = list(filtered_blob.date_set)
        tag_dates.sort()

        # Create the time vector with the tag as the left-most (first) entry
        time_vector = [tag_list[0]]
        days_in_week: List[dt.date] = get_week_list(tag_dates[0])
        for date in days_in_week:
            if date in tag_dates:
                daily_blob = filtered_blob.sub_blob(date)
                time_vector.append(f'{str(daily_blob.blob_total):>12}')
            else:
                time_vector.append('')
        vector_list.append(time_vector)

    # Print the tabulated table
    headers = get_table_header(list(blob.date_set))
    print(tabulate(vector_list, headers))


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
    parser.add_argument('-d', '--daptiv', action='store_true',
                        help='Display data in daptiv format')
    parser.add_argument('-g', '--group', action='append', default=None,
                        type=str,
                        help='enter tags to group together in weekly formats')

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

    # Determine the list of grouped tags
    group_list = list()
    if args.group:
        for g_str in args.group:
            group_list.append(g_str.split(sep=','))

    if args.week:
        weekly_report(d_in_q,
                      tag_sort=args.tag_sort,
                      verbose=args.verbose)
    elif args.daptiv:
        weekly_blob = get_week_blob(d_in_q)
        daptiv_format(weekly_blob, group_list)
    else:
        blob = log_2_blob(beget_filepath(d_in_q))
        ex_time = get_expected_time() if d_in_q == today else UNITS_PER_DAY
        probar(ex_time,
               int(blob.blob_total.total_seconds() / FIFTEEN_MINUTES),
               UNITS_PER_DAY)


if __name__ == '__main__':
    try:
        driver()
    except FileNotFoundError as exc:
        error_handler(exception=exc)
