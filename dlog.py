#!/usr/bin/python3
"""Allow access and creation of text log files."""
import argparse
import datetime as dt
import os
import subprocess
from pathlib import Path

from util import beget_filepath


def edit_timesheet(filename: os.PathLike = None):
    """Call vim and edit a log file."""
    subprocess.run(['vim', filename], check=True)


def driver():
    """Manage the argparse and drive the program."""
    parser = argparse.ArgumentParser(
        prog='dlog',
        usage='%(prog)s FILENAME\n'
              '  or:  %(prog)s MONTH DAY')

    parser.add_argument(
        "month", help='numeral of month OR name of logfile', nargs='?')
    parser.add_argument(
        "day", help='numeral of day IF with month', type=int, nargs='?')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')

    parser.add_argument('-y', '--yester', action='store', default=0,
                        type=int, nargs='?', const=1,
                        help="Choose a relative day's date in the past")

    args = parser.parse_args()
    today = dt.date.today()
    if args.yester:
        days_in_past = dt.timedelta(args.yester)
        past_date = today - days_in_past
        filepath = beget_filepath(past_date)
    elif args.month is None:
        filepath = beget_filepath(today)
    else:
        # Default behavior, use month and day to determine filename
        args.month = int(args.month)
        filepath = beget_filepath(dt.date(
            today.year, args.month, args.day))

    # Create the path to the log file if it does not already exist
    os.makedirs(Path(filepath).parent, exist_ok=True)

    edit_timesheet(f'{filepath}')


if __name__ == '__main__':
    driver()
