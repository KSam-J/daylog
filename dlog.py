import argparse
import datetime as dt
import os
import subprocess

from util import LOG_PATH, beget_filepath, beget_path_and_file


def ensure_path(path):
    os.makedirs(path, exist_ok=True)

def edit_timesheet(filename):
    subprocess.run(['vim', filename])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='dlog',
        usage='%(prog)s FILENAME\n'
              '  or:  %(prog)s MONTH DAY')

    parser.add_argument(
        "file_or_month", help='numeral of month OR name of logfile', nargs='?')
    parser.add_argument(
        "day", help='numeral of day IF with month', type=int, nargs='?')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show additional hourly info')

    args = parser.parse_args()
    today = dt.date.today()

    if args.file_or_month is None:
        logpath, logname = beget_path_and_file(
            today.year, today.month, today.day)
        ensure_path(logpath)
        edit_timesheet(f'{logpath}{logname}')
    # elif os.path.isfile(args.file_or_month):
    #     # Read an explicitly defined file
    #     total_str = generate_summary(args.file_or_month)
    else:
        # Default behavior, use month and day to determine filename
        args.file_or_month = int(args.file_or_month)
        logpath, logname = beget_path_and_file(
            today.year, args.file_or_month, args.day)
        ensure_path(logpath)
        edit_timesheet(f'{logpath}{logname}')
