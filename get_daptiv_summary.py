"""Read Time log and print summary on stdout."""
import datetime as dt
import os
import re

import fire

# FILENAME = f'log'
LOG_PATH = '/home/samkel/journal/oct_time_sheet/'

PRINT_DESCRIPTION = 0

# def printSummary(day, month=dt.date.today().month, filename=''):
#     with file(f'{LOG_PATH}log{month}_{day}.txt') as log:
#         for line in log:
#             hour_search = re.search(
#                 r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?', line)
#             if hour_search:
#                 hour1 = hour_search.group(0)
#                 min1 = 0
#                 if hour_search.group(1):
#                     min1 = hour_search.group(1)
#                 hour2 = hour_search.group(3)
#                 min2 = 0
#                 if hour_search.group(4):
#                     min2 = hour_search.group(4)

#                 start_time = dt.time(hour1, min1)
#                 end_time

#     return


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
                    tdelta = dt.timedelta(
                        days=0, seconds=(tdelta.seconds - 60*60*12))
                print(f'{hour1:02}:{min1:02}-{hour2:02}:{min2:02}\t\t\u0394{tdelta}')

                # Accumulate the total hours
                total += tdelta
            elif PRINT_DESCRIPTION:  # TODO Turn this into a parser flag
                # Print None Time delta lines
                print(line.rstrip())
        # Convert seconds to hours
        total_hrs = total.total_seconds()/3600

    return f'{total_hrs:>32} hours'
    # TODO add flag to convert to work day scale
    # \nOR {(total_hrs)//8} work_days and {total_hrs % 8} hours'

# parser = argparse.ArgumentParser()
# parser.add_argument("echo")
# args = parser.parse_args()
# print(args.echo)


if __name__ == '__main__':
    fire.Fire(get_total_hours)
