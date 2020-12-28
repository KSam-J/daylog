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

    args = parser.parse_args()
    today = dt.date.today()

    if args.month is None:
        logpath, logname = beget_path_and_file(
            today.year, today.month, today.day)

        # Create the path to the log file if it does not already exist
        os.makedirs(logpath, exist_ok=True)

        edit_timesheet(f'{logpath}{logname}')

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
