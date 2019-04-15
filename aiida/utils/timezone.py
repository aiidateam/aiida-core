# -*- coding: utf-8 -*-

import pytz

from datetime import datetime

from aiida import settings

# All the timezone part here is taken from Django.
# TODO SP: check license terms ?
# TODO SP: docstring

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

utc = pytz.utc


def get_default_timezone():
    return pytz.timezone(settings.TIME_ZONE)

get_current_timezone = get_default_timezone


def now():
    if getattr(settings, "USE_TZ", None):
        return datetime.utcnow().replace(tzinfo=utc)
    else:
        return datetime.now()


def is_naive(value):
    return value.utcoffset() is None


def is_aware(value):
    return value.utcoffset() is not None


def make_aware(value, timezone=None, is_dst=None):
    if timezone is None:
        timezone = get_current_timezone()
    if hasattr(timezone, 'localize'):
        return timezone.localize(value, is_dst=is_dst)
    else:
        if is_aware(value):
            raise ValueError(
                "make_aware expects a naive datetime, got %s" % value)
        # This may be wrong around DST changes!
        return value.replace(tzinfo=timezone)


def localtime(value, timezone=None):
    """
    Converts an aware datetime.datetime to local time.
    Local time is defined by the current time zone, unless another time zone
    is specified.
    """
    if timezone is None:
        timezone = get_current_timezone()
    # If `value` is naive, astimezone() will raise a ValueError,
    # so we don't need to perform a redundant check.
    value = value.astimezone(timezone)
    if hasattr(timezone, 'normalize'):
        # This method is available for pytz time zones.
        value = timezone.normalize(value)
    return value
