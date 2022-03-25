# -*- coding: utf-8 -*-
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

from aiida.common.timezone import localtime, make_aware, now, timezone_from_name


def is_aware(dt):  # pylint: disable=invalid-name
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
    delta = timedelta(minutes=1)
    ref = now()

    from_tz = make_aware(datetime.fromtimestamp(time()))
    assert from_tz <= ref + delta
    assert from_tz >= ref - delta


def test_make_aware():
    """Test the :func:`aiida.common.timezone.make_aware` function.

    This should make a naive datetime object aware using the timezone of the operating system.
    """
    system_tzinfo = datetime.now(timezone.utc).astimezone()  # This is how to get the timezone of the OS.
    naive = datetime(1970, 1, 1)
    aware = make_aware(naive)
    assert is_aware(aware)
    assert aware.tzinfo.tzname(aware) == system_tzinfo.tzname()
    assert aware.tzinfo.utcoffset(aware) == system_tzinfo.utcoffset()


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
    delta = timedelta(hours=2)
    naive = datetime(1970, 1, 1)
    aware = make_aware(naive, timezone(delta))
    assert is_aware(aware)
    assert aware.tzinfo.utcoffset(aware) == delta


def test_timezone_from_name():
    """Test the :func:`aiida.common.timezone.timezone_from_name` function."""
    assert isinstance(timezone_from_name('Europe/Amsterdam'), tzinfo)


def test_timezone_from_name_unknown():
    """Test the :func:`aiida.common.timezone.timezone_from_name` function for unknown timezone."""
    with pytest.raises(ValueError, match=r'unknown timezone: .*'):
        timezone_from_name('Invalid/Unknown')
