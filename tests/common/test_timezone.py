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
import datetime
import time

from aiida.common import timezone


def test_now():
    """Test the ``now`` function.

    Check that the time returned by AiiDA's ``now`` function is compatible with attaching a timezone to a "naive" time
    stamp using ``make_aware``.
    """
    delta = datetime.timedelta(minutes=1)
    ref = timezone.now()

    from_tz = timezone.make_aware(datetime.datetime.fromtimestamp(time.time()))
    assert from_tz <= ref + delta
    assert from_tz >= ref - delta


def test_datetime_to_isoformat():
    """Test the ``datetime_to_isoformat`` function."""
    assert timezone.datetime_to_isoformat(None) is None
    assert isinstance(timezone.datetime_to_isoformat(timezone.now()), str)


def test_isoformat_to_datetime():
    """Test the ``isoformat_to_datetime`` function."""
    timestamp = '2021-09-15T08:54:29.263230+00:00'
    assert timezone.isoformat_to_datetime(None) is None
    assert isinstance(timezone.isoformat_to_datetime(timestamp), datetime.datetime)
