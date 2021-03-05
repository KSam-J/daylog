#!/usr/bin/python3
"""Allow access and creation of text log files."""
import argparse
import datetime as dt
import os
import subprocess

from util import beget_path_and_file


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

<<<<<<< HEAD
    parser.add_argument('-y', '--yester', action='store', default=0,
=======
    parser.add_argument('-y', '--yester', action='store', default=1,
>>>>>>> bcf4a655b9c38bb009b731643aefa18bb7ee12ae
                        type=int, nargs='?', const=1,
                        help="Choose a relative day's date in the past")

    args = parser.parse_args()
    today = dt.date.today()
    if args.yester:
        days_in_past = dt.timedelta(args.yester)
        past_date = today - days_in_past
        logpath, logname = beget_path_and_file(
            past_date.year, past_date.month, past_date.day)
    elif args.month is None:
        logpath, logname = beget_path_and_file(
            today.year, today.month, today.day)
    else:
        # Default behavior, use month and day to determine filename
        args.month = int(args.month)
        logpath, logname = beget_path_and_file(
            today.year, args.month, args.day)

    # Create the path to the log file if it does not already exist
    os.makedirs(logpath, exist_ok=True)

    edit_timesheet(f'{logpath}{logname}')


if __name__ == '__main__':
    driver()
