#!/usr/bin/python
"""Print progressbars and other resources for progressbars."""
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import datetime as dt
import shutil
import sys

import progressbar

PHOENIX_TZ = dt.timezone(dt.timedelta(hours=-7), name='Phoenix')
START_OF_DAY = [9, 30, 0, 0, PHOENIX_TZ]

FIFTEEN_MINUTES = 60 * 15  # Unit granularity
UNITS_PER_DAY = 8 * 4

# Formatting constants
ENCLOSING_BAR_CHARS = 2


def probar(expected, done, total):
    """Print a progress bar denoting work done, expected, and total hours."""
    expected = int(expected)
    done = int(done)
    total = int(total)
    markers = [
        '\x1b[30m\x1b[107m\x1b[1m#\x1b[0m',  # On Track
        '\x1b[32m\x1b[107m \x1b[0m',  # Ahead
        '#\x1b[0m',                 # Behind
        ' '                   # Left
    ]
    widgets = [progressbar2.MultiRangeBar("amounts", markers=markers)]

    # Calculate amounts
    diff = abs(done - expected)
    if expected <= done:
        amounts = [expected, diff, 0, (total - done)]
    else:  # expected > done
        amounts = [done, 0, diff, (total - expected)]

    suffix = f'{done/4:5} hours'
    # Set bar_width
    bar_width = 0
    if total < UNITS_PER_DAY:
        bar_width = UNITS_PER_DAY + ENCLOSING_BAR_CHARS + len(suffix)
    else:
        bar_width = total + ENCLOSING_BAR_CHARS + len(suffix)

    # Cap the width at the terminal size
    terminal_width = None
    try:
        terminal_width = shutil.get_terminal_size()[0]
    except OSError:
        terminal_width = 40

    bar_width = terminal_width if bar_width > terminal_width else bar_width

    p_bar = progressbar2.ProgressBar(widgets=widgets, max_value=10,
                                    term_width=bar_width,
                                    suffix=suffix).start()
    p_bar.update(amounts=amounts, force=True)


def get_expected_time(weekly=False):
    """
    Calculate the expected amount of work that should be done.

        This assumes that we are asking about the current day or week.
        TODO: change to (number_of_days, today_included=False)
    """
    now = dt.datetime.now(PHOENIX_TZ)

    start_of_day = dt.datetime(now.year, now.month, now.day, *START_OF_DAY)
    tdelta = abs(start_of_day - now)
    expected_today = round(tdelta.total_seconds() / FIFTEEN_MINUTES)

    # Account for the lunch break
    noon = dt.datetime(now.year, now.month, now.day, 12, tzinfo=PHOENIX_TZ)
    one_pm = dt.datetime(now.year, now.month, now.day, 13, tzinfo=PHOENIX_TZ)
    offset = 0
    if noon < now < one_pm:
        offset = round((noon - now).total_seconds() / FIFTEEN_MINUTES)
    elif one_pm < now:
        offset = 4  # UNITS
    expected_today -= offset

    # Cap the expected_today at eight hours a day
    if expected_today > UNITS_PER_DAY:
        expected_today = UNITS_PER_DAY

    if weekly:
        weekday = dt.date.today().weekday()
        expected_upto_today = UNITS_PER_DAY * weekday
        expected_today = expected_upto_today + expected_today

    return expected_today


if __name__ == '__main__':
    try:
        probar(sys.argv[1], sys.argv[2], sys.argv[3])
    except KeyboardInterrupt:
        sys.exit()
