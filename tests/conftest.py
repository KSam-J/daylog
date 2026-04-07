"""Shared fixtures and configuration for the daylog test suite."""
import datetime as dt
import sys
import os

import pytest

# Make the repo root importable so tests can import daylog modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
SAMPLE_LOG = os.path.join(FIXTURES_DIR, 'sample.txt')

# A fixed reference date that matches the sample logfile entries (arbitrary workday)
SAMPLE_DATE = dt.date(2024, 3, 11)  # Monday


@pytest.fixture
def sample_log_path():
    return SAMPLE_LOG


@pytest.fixture
def sample_date():
    return SAMPLE_DATE
