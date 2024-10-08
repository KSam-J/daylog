"""Contain general use functions for daysum programs."""
import datetime as dt
import re
import sys

# FILENAME = f'log'
LOG_PATH = '/home/samkel/journal'

PRINT_DESCRIPTION = 0

FOLDER_SUFFIX = '_time_sheet'

ISO_FMT_RE = re.compile(r'(19|20)\d{2}-[01]\d-[0-3]\d')  # YYYY-MM-DD
BACK_COMPAT_RE = re.compile(r'log([01]\d)_([0-3]\d).txt')  # MM_DD
ISO_FMT_FILE = 'log{year:4}-{month:02}-{day:02}.txt'
BACK_COMPAT_FILE = 'log{month:02}_{day:02}.txt'


def error_handler(error_str: str | None = None, exception: Exception | None = None):
    """Print error info to screen and exit the program."""
    # Determine what to print
    if error_str:
        print(error_str)
    elif exception:
        print(exception)
    else:
        print('System Error!')

    # Determine exit code
    exit_code = 1
    if exception:
        # Use the provided errno, if possible
        try:
            exit_code = exception.errno
        except AttributeError:
            pass

    sys.exit(exit_code)


def beget_filepath(date: dt.date):
    """Generate full filepath of log file for select date."""
    specific_path = f'{LOG_PATH}/{date.strftime(r"%Y/%b")}{FOLDER_SUFFIX}/'
    filename = BACK_COMPAT_FILE.format(month=date.month, day=date.day)

    return f'{specific_path}{filename}'


def beget_date(filename) -> dt.date:
    """Beget a date object based on parsed filename."""
    # Search for ISO format
    iso_match = re.match(ISO_FMT_RE, filename)
    mm_dd_match = re.match(BACK_COMPAT_RE, filename)
    if iso_match:
        begotten_date = dt.date.fromisoformat(iso_match.group(0))
    # elif search for ISO w/o year format
    elif mm_dd_match:
        begotten_date = dt.date(2021, int(mm_dd_match.group(1)),
                                int(mm_dd_match.group(2)))
    else:
        begotten_date = None

    return begotten_date
