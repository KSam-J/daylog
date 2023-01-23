#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
from __future__ import annotations

import argparse
import datetime as dt
import os
from typing import List

from tabulate import tabulate, SEPARATING_LINE

from probar import FIFTEEN_MINUTES, UNITS_PER_DAY, get_expected_time, probar
from timeblob import TimeBlob, TimeBlip
from util import beget_filepath, error_handler
from logfile import log_2_blob


TODAY = dt.date.today()


def print_delta_line(hr1, min1, hr2, min2, delta):
    """Pretty print the time delta line."""
    delta_value = f'\u0394{str(delta):>8}'
    print(f'{hr1:02}:{min1:02}-{hr2:02}:{min2:02}{delta_value:>23}')


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

    return blobify_dates(date_list)


def blobify_dates(date_list: List[dt.date]) -> TimeBlob:
    """Return a TimeBlob formed from the specified dates."""
    blob = TimeBlob()
    # Place all dates in week into a single blob
    for date in date_list:
        file_path = beget_filepath(date)
        # Only process files that exist
        if not os.path.isfile(file_path):
            continue

        daily_blob = log_2_blob(file_path, date)
        blob += daily_blob

    return blob


def print_probar(blob: TimeBlob):
    """Print the progressbar for a given blob."""
    # Determine time expected to be done
    expected_time = 0
    if TODAY in blob.date_set:
        expected_time = get_expected_time()
        expected_time += 8 * 4 * (len(blob.date_set) - 1)
    else:
        expected_time += 8 * 4 * len(blob.date_set)

    # Determine time actually finished
    done_time = int(blob.blob_total.total_seconds() / FIFTEEN_MINUTES)

    # Determine total amount of time
    total_time = UNITS_PER_DAY * len(blob.date_set)

    # Print the progressbar with total
    probar(expected_time,
           done_time,
           total_time)


def report_view(blob: TimeBlob,
                tag_sort: bool = False,
                verbose: int = 0) -> None:
    """
    Generate and display the weekly report.

        TODO: create a tag sort option and verbose option?
    """
    def print_workday_total(blob: TimeBlob):
        full_days = int(blob.total_work_days)
        remainder = blob.blob_total - dt.timedelta(hours=(full_days * 8))
        print(f'\nWeekly Total{full_days:>7} days {remainder}')

    for day in sorted(blob.date_set):
        daily_total = blob.sub_blob(day).blob_total
        if daily_total > dt.timedelta(0):
            print(day.strftime('%a %b %d %Y'), end='')
            print(f'{"":10}{daily_total}')

    print_workday_total(blob)

    # Print the progressbar with total
    print_probar(blob)


def daptiv_format(blob: TimeBlob,
                  groups: List[List[str]] | None = None) -> None:
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
            day += '\n' + date.strftime('%D')
            header_list.append(day)

        # Prepend an empty str to account for Y-axis labels
        header_list = [''] + header_list

        return header_list

    vector_list = list()
    # Segregate blobs by tag and filter the descriptions

    # Apply tag groups
    tag_groups = apply_tag_groups(list(blob.tag_set.copy()), groups)

    # Build the table Row by Row
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
                # Convert Time-Deltas to Daptiv decimal form
                # Ex: 6:30:00 --> 6.5
                time_vector.append(
                    str(daily_blob.blob_total/dt.timedelta(hours=1)))
            else:
                time_vector.append('')
        vector_list.append(time_vector)

    # Add totals at the bottom of the table
    # Insert blank spacing row
    vector_list.append(SEPARATING_LINE)
    # Organize the dates in chronological order
    blob_dates = list(blob.date_set)
    blob_dates.sort()
    time_vector = [f'Σ: {str(blob.blob_total/dt.timedelta(hours=1))}']
    days_in_week: List[dt.date] = get_week_list(blob_dates[0])
    for date in days_in_week:
        if date in blob_dates:
            daily_blob = blob.sub_blob(date)
            # Convert Time-Deltas to Daptiv decimal form
            # Ex: 6:30:00 --> 6.5
            time_vector.append(
                str(daily_blob.blob_total/dt.timedelta(hours=1)))
        else:
            time_vector.append('0.0')
    vector_list.append(time_vector)

    # Print the tabulated table
    headers = get_table_header(list(blob.date_set))
    print(tabulate(vector_list, headers))


def apply_tag_groups(singelton_tags: List[str],
                     groups: List[List[str]] | None) -> List[List[str]]:
    """Change a list of tags to a list of grouped tags."""
    # Strip tags in groups from singelton list
    for group in groups:  # groups can be None
        for tag in group:
            singelton_tags.remove(tag)
    # Merge singelton and grouped tags for printing structure
    tag_groups = [[tag] for tag in singelton_tags] + groups

    return sorted(tag_groups)


def tag_view(blob: TimeBlob, groups: List[List[str]] | None = None):
    """Display the blob totals by tag."""
    # Apply tag groups
    tag_groups = apply_tag_groups(list(blob.tag_set.copy()), groups)

    vector_list = list()
    for tag_list in tag_groups:
        filtered_blob = blob.filter_by(tag_list)

        # Organize the dates in chronological order
        tag_dates = list(filtered_blob.date_set)
        tag_dates.sort()

        # Create the time vector with the tag as the left-most (first) entry
        row_vector = [tag_list[0]]
        # Convert Time-Deltas to Daptiv decimal form
        # Ex: 6:30:00 --> 6.5
        row_vector.append(str(filtered_blob.blob_total/dt.timedelta(hours=1)))

        vector_list.append(row_vector)

    # Print the tabulated table
    dates = list(blob.date_set)
    dates.sort()
    headers = {'', f'{dates[0]} --> {dates[-1]}'}
    print(tabulate(vector_list, headers))


def driver():
    """Contain the arg parser and perform main functions."""
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
                        default=TODAY.year)

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')
    parser.add_argument('-q', '--quiet', action='count', default=0,
                        help='only show total hours')
    parser.add_argument('-x', '--experimental', action='store_true',
                        help='count using the blob data format')
    parser.add_argument('-t', '--tag_sort', action='store_true',
                        help='display timedeltas organized by tag')
    parser.add_argument('-r', '--report', action='store_true',
                        help='display in report format')
    parser.add_argument('-d', '--daptiv', action='store_true',
                        help='Display data in daptiv format')
    parser.add_argument('-g', '--group', action='append', default=None,
                        type=str,
                        help='enter tags to group together in weekly formats')
    # Quantifiers
    parser.add_argument('-w', '--week', action='count', default=0,
                        help='quantifier in weeks')
    parser.add_argument('-s', '--since', action='store_true',
                        help='since <date provided> quantifier')

    args = parser.parse_args()

    # Determine the argument types for the gen_sum function
    gen_args = list()
    if args.file_or_month is None:
        gen_args = [TODAY.year, TODAY.month, TODAY.day]
    elif os.path.isfile(args.file_or_month):
        # Read an explicitly defined file
        gen_args.append(args.file_or_month)
    else:
        # Default behavior, use month and day to determine filename
        args.file_or_month = int(args.file_or_month)
        gen_args = [args.year, args.file_or_month, args.day]

    d_in_q = dt.date(*gen_args)  # date in question

    # Handle quantifier options
    # Create the Quantifier Blob
    q_blob: TimeBlob = TimeBlob()

    if args.daptiv and not args.week:
        args.week = 1

    if args.week:
        for week in range(0, args.week):
            day_in_week = d_in_q - dt.timedelta(days=(week * 7))
            q_blob += get_week_blob(day_in_week)
    else:  # No quantifiers -> use day in question
        try:
            q_blob = log_2_blob(beget_filepath(d_in_q))
        except FileNotFoundError:
            today = dt.datetime(TODAY.year, TODAY.month, TODAY.day, 0, 0)
            q_blob = TimeBlob(blip_list=[TimeBlip(today, today)])

    # Handle specifier options
    # Determine the list of grouped tags
    group_list = list()
    if args.group:
        for g_str in args.group:
            group_list.append(g_str.split(sep=','))

    # Handle view options
    if args.report:
        report_view(q_blob,
                    tag_sort=args.tag_sort,
                    verbose=args.verbose)
    elif args.daptiv:
        daptiv_format(q_blob, group_list)
    elif args.tag_sort:
        tag_view(q_blob, group_list)
    else:
        print_probar(q_blob)


if __name__ == '__main__':
    try:
        driver()
    except FileNotFoundError as exc:
        error_handler(exception=exc)
