# -*- coding: utf-8 -*-
"""Tests for the AiiDA pytest fixtures."""

from aiida.manage.configuration import get_config
from aiida.manage.configuration.config import Config


def test_profile_config(aiida_profile):  # pylint: disable=unused-argument
    """Check that the config file created with the test profile passes validation."""
    Config.from_file(get_config().filepath)
