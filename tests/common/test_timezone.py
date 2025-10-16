###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`~aiida.common.timezone` module."""

from datetime import datetime, timedelta, timezone, tzinfo
from time import time

import pytest

from aiida.common.timezone import delta, localtime, make_aware, now, timezone_from_name


def is_aware(dt):
    """Return whether the datetime is aware.

    See https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive

    :param dt: The datetime object to check.
    :returns: True if ``datetime`` is aware, False otherwise.
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def test_now():
    """Test the :func:`aiida.common.timezone.now` function.

    Check that the time returned by AiiDA's ``now`` function is compatible with attaching a timezone to a "naive" time
    stamp using ``make_aware``.
    """
    dt = timedelta(minutes=1)
    ref = now()

    from_tz = make_aware(datetime.fromtimestamp(time()))
    assert from_tz <= ref + dt
    assert from_tz >= ref - dt


def test_make_aware_already_aware():
    """Test the :func:`aiida.common.timezone.make_aware` function for an already aware datetime.

    This should simply return the datetime if ``timezone`` is not specified, otherwise the ``timezone`` will be set on
    the datetime object.
    """
    aware = datetime.now(timezone.utc).astimezone()  # This creates an aware object.
    assert is_aware(aware)
    assert make_aware(aware) == aware

    different_tz = make_aware(aware, timezone(timedelta(hours=12)))
    assert different_tz == aware
    assert different_tz.tzinfo.tzname(different_tz) != aware.tzinfo.tzname(aware)
    assert different_tz.tzinfo.utcoffset(different_tz) != aware.tzinfo.tzname(aware)


def test_localtime_aware():
    """Test the :func:`aiida.common.timezone.test_localtime` function for an already aware datetime.

    This should simply return the datetime if ``timezone`` is not specified, otherwise the ``timezone`` will be set on
    the datetime object.
    """
    aware = datetime.now(timezone.utc).astimezone()  # This creates an aware object.
    assert is_aware(aware)
    assert localtime(aware) == aware


def test_localtime_naive():
    """Test the :func:`aiida.common.timezone.test_localtime` function for a naive datetime.

    This should not raise but simply return the same datetime made aware.
    """
    naive = datetime.now()  # This creates a naive object.
    assert not is_aware(naive)

    local = localtime(naive)
    assert local != naive
    assert is_aware(local)


def test_make_aware_timezone():
    """Test the :func:`aiida.common.timezone.make_aware` function passing an explicit timezone."""
    dt = timedelta(hours=2)
    naive = datetime(1970, 1, 1)
    aware = make_aware(naive, timezone(dt))
    assert is_aware(aware)
    assert aware.tzinfo.utcoffset(aware) == dt


def test_timezone_from_name():
    """Test the :func:`aiida.common.timezone.timezone_from_name` function."""
    assert isinstance(timezone_from_name('Europe/Amsterdam'), tzinfo)


def test_timezone_from_name_unknown():
    """Test the :func:`aiida.common.timezone.timezone_from_name` function for unknown timezone."""
    with pytest.raises(ValueError, match=r'unknown timezone: .*'):
        timezone_from_name('Invalid/Unknown')


def test_delta():
    """Test the :func:`aiida.common.timezone.delta` function."""
    datetime_01 = datetime(1980, 1, 1, 0, 0, 0)
    datetime_02 = datetime(1980, 1, 1, 0, 0, 2)

    # Should return an instance of ``timedelta``
    assert isinstance(delta(datetime_02), timedelta)

    # If no comparison datetime is provided, it should be compared to ``now`` as a default
    assert delta(datetime_01).total_seconds() > 0

    assert delta(datetime_01, datetime_02).total_seconds() == 2
    assert delta(datetime_02, datetime_01).total_seconds() == -2
