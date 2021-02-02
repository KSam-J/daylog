#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import sys

import progressbar


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


if __name__ == '__main__':
    try:
        probar(sys.argv[1], sys.argv[2], sys.argv[3])
    except KeyboardInterrupt:
        sys.exit()
