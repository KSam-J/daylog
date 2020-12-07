import datetime as dt

# FILENAME = f'log'
LOG_PATH = '/home/samkel/journal'

PRINT_DESCRIPTION = 0

FOLDER_SUFFIX = '_time_sheet'


def error_handler(error_str):
    print(error_str)
    exit(1)

def beget_path_and_file(year, month, day):
    """Return full filepath of log file for select date."""
    date = dt.datetime(year, month, day)
    specific_path = f'{LOG_PATH}/{date.strftime(r"%Y/%b")}{FOLDER_SUFFIX}/'
    filename = f'log{month:02}_{day:02}.txt'

    return (specific_path, filename)

def beget_filepath(year, month, day):
    """Return full filepath of log file for select date."""
    date = dt.datetime(year, month, day)
    specific_path = f'{LOG_PATH}/{date.strftime(r"%Y/%b")}{FOLDER_SUFFIX}/'
    filename = f'log{month:02}_{day:02}.txt'

    return f'{specific_path}{filename}'
