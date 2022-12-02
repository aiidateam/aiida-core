# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on datetime objects."""
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Optional

import pytz

utc = timezone.utc  # Simply forward this attribute from the :mod:`datetime.timezone` built in library


def now() -> datetime:
    """Return the datetime object of the current time.

    :return: datetime object represeting current time
    """
    return datetime.now().astimezone()


def make_aware(value: datetime, tz: Optional[tzinfo] = None) -> datetime:
    """Make the given datetime object timezone aware.

    :param value: The datetime object to make aware.
    :param tz: The timezone to set. If not defined the system local timezone is assumed for the target timezone.
    :return: A timezone aware datetime object.
    """
    return value.astimezone(tz)


def localtime(value: datetime) -> datetime:
    """Make a :class:`datetime.datetime` object timezone aware with the local timezone.

    :param value: The datetime object to make aware.
    :return: A timezone aware datetime object with the timezone set to that of the operating system.
    """
    return make_aware(value)


def timezone_from_name(name: str) -> tzinfo:
    """Return a :class:`datetime.tzinfo` instance corresponding to the given timezone name.

    :param name: The timezone name. Should correspond to a known name in the Olsen database.
        https://en.wikipedia.org/wiki/Tz_database
    :returns: The corresponding timezone object.
    :raises ValueError: if the timezone name is unknown.
    """
    try:
        return pytz.timezone(name)
    except pytz.exceptions.UnknownTimeZoneError as exception:
        raise ValueError(f'unknown timezone: {name}') from exception


def delta(from_time: datetime, to_time: Optional[datetime] = None) -> timedelta:
    """Return the datetime object representing the different between two datetime objects.

    :param from_time: The starting datetime object.
    :param to_time: The end datetime object. If not specified :func:`aiida.common.timezone.now` is used.
    :return: The delta datetime object.
    """
    return make_aware(to_time or now()) - make_aware(from_time)
