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

from datetime import datetime
import dateutil


def get_current_timezone():
    """Return the current timezone.

    :return: current timezone
    """
    from tzlocal import get_localzone
    local = get_localzone()

    if local.zone == 'local':
        raise ValueError(
            "Unable to detect name of local time zone. Please set 'TZ' environment variable, e.g."
            " to 'Europe/Zurich'"
        )
    return local


def now():
    """Return the datetime object of the current time.

    :return: datetime object represeting current time
    """
    import pytz
    from aiida.manage.configuration import settings

    if getattr(settings, 'USE_TZ', None):
        return datetime.utcnow().replace(tzinfo=pytz.utc)

    return datetime.now()


def is_naive(value):
    """Return whether the given datetime object is timezone naive

    :return: boolean, True if naive, False otherwise
    """
    return value.utcoffset() is None


def is_aware(value):
    """Return whether the given datetime object is timezone aware

    :return: boolean, True if aware, False otherwise
    """
    return value.utcoffset() is not None


def make_aware(value, timezone=None, is_dst=None):
    """Make the given datetime object timezone aware.

    :param value: datetime object to make aware
    :param timezone:
    :param is_dst:
    :return:
    """
    if timezone is None:
        timezone = get_current_timezone()
    if hasattr(timezone, 'localize'):
        return timezone.localize(value, is_dst=is_dst)

    if is_aware(value):
        raise ValueError('make_aware expects a naive datetime, got %s' % value)

    # This may be wrong around DST changes!
    # See http://pytz.sourceforge.net/#localized-times-and-date-arithmetic
    return timezone.localize(value)


def localtime(value, timezone=None):
    """Converts an aware datetime.datetime to local time.

    Local time is defined by the current time zone, unless another time zone is specified.
    """
    if timezone is None:
        timezone = get_current_timezone()

    # If `value` is naive, astimezone() will raise a ValueError, so we don't need to perform a redundant check.
    value = value.astimezone(timezone)
    if hasattr(timezone, 'normalize'):
        # This method is available for pytz time zones.
        value = timezone.normalize(value)

    return value


def delta(from_time, to_time=None):
    """Return the datetime object representing the different between two datetime objects.

    :param from_time: starting datetime object
    :param to_time: end datetime object
    :return: the delta datetime object
    """
    if to_time is None:
        to_time = now()

    try:
        from_time_aware = make_aware(from_time)
    except ValueError:
        from_time_aware = from_time
    try:
        to_time_aware = make_aware(to_time)
    except ValueError:
        to_time_aware = to_time

    return to_time_aware - from_time_aware


def datetime_to_isoformat(value):
    """Convert a datetime object to string representations in ISO format.

    :param value: a datetime object
    """
    if value is None:
        return None
    return value.isoformat()


def isoformat_to_datetime(value):
    """Convert string representation of a datetime in ISO format to a datetime object.

    :param value: a ISO format string representation of a datetime object
    """
    if value is None:
        return None
    return dateutil.parser.parse(value)
