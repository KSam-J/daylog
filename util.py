"""Contain general use functions for daysum programs."""
import datetime as dt
import sys

# FILENAME = f'log'
LOG_PATH = '/home/samkel/journal'

PRINT_DESCRIPTION = 0

FOLDER_SUFFIX = '_time_sheet'


def error_handler(error_str):
    """Print error info to screen and exit the program."""
    print(error_str)


def beget_path_and_file(date: dt.date):
    """Generate full filepath of log file for select date."""
    specific_path = f'{LOG_PATH}/{date.strftime(r"%Y/%b")}{FOLDER_SUFFIX}/'
    filename = BACK_COMPAT_FILE.format(month=date.month, day=date.day)

    return (specific_path, filename)


def beget_filepath(date: dt.date):
    """Generate full filepath of log file for select date."""
    specific_path = f'{LOG_PATH}/{date.strftime(r"%Y/%b")}{FOLDER_SUFFIX}/'
    filename = BACK_COMPAT_FILE.format(month=date.month, day=date.day)

    return f'{specific_path}{filename}'
