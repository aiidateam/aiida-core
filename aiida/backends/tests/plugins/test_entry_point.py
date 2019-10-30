# -*- coding: utf-8 -*-
"""Tests for the :py:mod:`~aiida.plugins.entry_point` module."""
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.plugins.entry_point import validate_registered_entry_points


class TestEntryPoint(AiidaTestCase):
    """Tests for the :py:mod:`~aiida.plugins.entry_point` module."""

    @staticmethod
    def test_validate_registered_entry_points():
        """Test the `validate_registered_entry_points` function."""
        validate_registered_entry_points()
