#!/usr/bin/python3
"""Log File parsing utilities."""
from __future__ import annotations

import datetime as dt
import re
import os
# import decimal

from timeblob import TimeBlip, TimeBlob
from util import beget_date, error_handler

DUMMY_DATE = (1986, 2, 21)
TIME_ENTRY_RE = re.compile(r'(\d{1,2}):?(\d{1,2})?-(\d{1,2}):?(\d{1,2})?')
TIME_BLOCK_RE = re.compile(r'^(\d{1,2})\.?(\d{1,2})?$')


def log_2_blob(filename: str, date: dt.date | None = None) -> TimeBlob:
    """Scan a log file and place the data in a TimeBlip."""
    # Check existence of file
    blob = None

    # Determine the date corresponding to filename
    if not date:
        date = beget_date(filename)
        # second date check required until beget_date has back compat check
        if not date:
            date = dt.date(*DUMMY_DATE)

    # Begin transfering text info to TimeBlob data stucture
    with open(filename, 'r') as log:
        blob = TimeBlob()
        purgatory_blip = None

        for line in log:
            # Determine what type of info is on line
            hour_search = re.match(TIME_ENTRY_RE, line)
            block_search = re.match(TIME_BLOCK_RE, line)

            # On lines stating time deltas
            if hour_search:
                # Grab start time
                hour1 = int(hour_search.group(1))
                min1 = 0
                if hour_search.group(2):
                    min1 = int(hour_search.group(2))
                start_time = dt.datetime.combine(date, dt.time(hour1, min1))
                # Grab end time
                hour2 = int(hour_search.group(3))
                min2 = 0
                if hour_search.group(4) is not None:
                    min2 = int(hour_search.group(4))
                end_time = dt.datetime.combine(date, dt.time(hour2, min2))

                purgatory_blip = TimeBlip(start_time, end_time)
            elif block_search:
                # Grab hour value
                hour_delta = int(block_search.group(1))
                min_delta = 0
                if block_search.group(2):
                    min_delta = int(block_search.group(2)) * 0.01
                start_time = dt.datetime.combine(date, dt.time(0, 0))
                # Grab end time
                end_time = dt.datetime.combine(
                    date, dt.time(hour_delta, round(min_delta * 60)))

                purgatory_blip = TimeBlip(start_time, end_time)

            else:  # Description lines
                if isinstance(purgatory_blip, TimeBlip):
                    purgatory_blip.desc = line.strip()
                    purgatory_blip.set_tag(TimeBlip.strip_tag(line.strip()))

                    # Add the Blip to the Blob
                    blob.add_blip(purgatory_blip)
                    # Reset the purgatory_blip for the next delta,desc pair
                    purgatory_blip = None
    return blob
