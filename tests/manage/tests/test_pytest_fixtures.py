# -*- coding: utf-8 -*-
"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""
import pytest

from aiida.manage.configuration import get_config
from aiida.manage.configuration.config import Config


@pytest.mark.usefixtures('aiida_profile')
def test_profile_config():
    """Check that the config file created with the test profile passes validation."""
    Config.from_file(get_config().filepath)


def test_aiida_localhost(aiida_localhost):
    """Test the ``aiida_localhost`` fixture."""
    assert aiida_localhost.label == 'localhost-test'


def test_aiida_local_code(aiida_local_code_factory):
    """Test the ``aiida_local_code_factory`` fixture."""
    code = aiida_local_code_factory(entry_point='core.templatereplacer', executable='diff')
    assert code.computer.label == 'localhost-test'
