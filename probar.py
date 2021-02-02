#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import datetime as dt
import sys

import progressbar

PHOENIX_TZ = dt.timezone(dt.timedelta(hours=-7), name='Phoenix')
START_OF_DAY = [9, 30, 0, 0, PHOENIX_TZ]

FIFTEEN_MINUTES = 60 * 15  # Unit granularity
UNITS_PER_DAY = 8 * 4


def probar(expected, done, total):
    expected = int(expected)
    done = int(done)
    total = int(total)
    markers = [
        '\x1b[7m\x1b[1m#\x1b[0m',  # On Track
        '\x1b[32m\x1b[107m \x1b[0m',  # Ahead
        '#\x1b[0m',                 # Behind
        ' '                   # Left
    ]
    widgets = [progressbar.MultiRangeBar("amounts", markers=markers)]

    # Calculate amounts
    diff = abs(done - expected)
    if expected <= done:
        amounts = [expected, diff, 0, (total - done)]
    else:  # expected > done
        amounts = [done, 0, diff, (total - expected)]

    p_bar = progressbar.ProgressBar(widgets=widgets, max_value=10).start()
    p_bar.update(amounts=amounts, force=True)


def get_expected_time(weekly=False):
    now = dt.datetime.now(dt.timezone.utc)

    start_of_day = dt.datetime(now.year, now.month, now.day, *START_OF_DAY)
    tdelta = now - start_of_day
    expected_today = int(tdelta.total_seconds() / FIFTEEN_MINUTES)

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
