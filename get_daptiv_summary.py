#!/usr/bin/python3
"""Read Time log and print summary on stdout."""
import argparse
import datetime as dt
import os
import re

import fire

# FILENAME = f'log'
LOG_PATH = '/home/samkel/journal/oct_time_sheet/'

PRINT_DESCRIPTION = 0


def get_total_hours(month, day, filename=None):
    """Return total hours and print subtotals."""
    if not filename:
        filename = f'{LOG_PATH}log{month:02}_{day:02}.txt'
    # Check existence of file
    if not os.path.isfile(filename):
        print(f'File:\n"{filename}"\ndoes not exist.')
        return
    # Open the log file, read only
    with open(filename, 'r') as log:
        total = dt.timedelta(0, 0, 0)
        for line in log:
            hour_search = re.search(
                r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?', line)

            # On lines stating time deltas
            if hour_search:
                # Grab start time
                hour1 = int(hour_search.group(1))
                min1 = 0
                if hour_search.group(2):
                    min1 = int(hour_search.group(2))
                start_time = dt.datetime(2020, month, day, hour1, min1)

                # Grab end time
                hour2 = int(hour_search.group(3))
                min2 = 0
                if hour_search.group(4) is not None:
                    min2 = int(hour_search.group(4))
                end_time = dt.datetime(2020, month, day, hour2, min2)

                # Calculate and print Time Delta
                tdelta = end_time - start_time
                if tdelta.days < 0:
                    # Make all timedeltas be < 12 hours.
                    tdelta = dt.timedelta(
                        days=0, seconds=(tdelta.seconds - 60*60*12))
                print(f'{hour1:02}:{min1:02}-{hour2:02}:{min2:02}\t\t\u0394{tdelta}')

                # Accumulate the total hours
                total += tdelta

            elif args.verbose >= 1:
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
        "file_or_month", help='numeral of month OR name of logfile')
    parser.add_argument(
        "day", help='numeral of day IF with month', type=int, nargs='?')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')

    # parser.add_argument("--filename", help="explicit logfile name for analysis")

    args = parser.parse_args()

    if os.path.isfile(args.file_or_month):
        # Read an explicitly defined file
        total_str = get_total_hours(5, 5, filename=args.file_or_month)
    else:
        # Default behavior, use month and day to determine filename
        total_str = get_total_hours(int(args.file_or_month), args.day)

    print(total_str)
