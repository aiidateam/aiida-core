# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the functionality that reads and modifies the caching configuration file."""

# pylint: disable=redefined-outer-name

import tempfile
import contextlib

import yaml
import pytest

from aiida.common import exceptions
from aiida.manage.configuration import get_profile
from aiida.manage.caching import configure, get_use_cache, enable_caching, disable_caching


@pytest.fixture
def configure_caching():
    """
    Fixture to set the caching configuration in the test profile to
    a specific dictionary. This is done by creating a temporary
    caching configuration file.
    """

    @contextlib.contextmanager
    def inner(config_dict):
        with tempfile.NamedTemporaryFile() as handle:
            yaml.dump({get_profile().name: config_dict}, handle, encoding='utf-8')
            configure(config_file=handle.name)
        yield
        # reset the configuration
        configure()

    return inner


@pytest.fixture
def use_default_configuration(configure_caching):  # pylint: disable=redefined-outer-name
    """
    Fixture to load a default caching configuration.
    """
    with configure_caching(
        config_dict={
            'default': True,
            'enabled': ['aiida.calculations:arithmetic.add'],
            'disabled': ['aiida.calculations:templatereplacer']
        }
    ):
        yield


def test_empty_enabled_disabled(configure_caching):
    """Test that `aiida.manage.caching.configure` does not except when either `enabled` or `disabled` is `None`.

    This will happen when the configuration file specifies either one of the keys but no actual values, e.g.::

        profile_name:
            default: False
            enabled:

    In this case, the dictionary parsed by yaml will contain `None` for the `enabled` key.
    Now this will be unlikely, but the same holds when all values are commented::

        profile_name:
            default: False
            enabled:
                # - aiida.calculations:templatereplacer

    which is not unlikely to occurr in the wild.
    """
    with configure_caching(config_dict={'default': True, 'enabled': None, 'disabled': None}):
        # Check that `get_use_cache` also does not except, and works as expected
        assert get_use_cache(identifier='aiida.calculations:templatereplacer')


def test_no_enabled_disabled(configure_caching):
    """Test that `aiida.manage.caching.configure` does not except when either `enabled` or `disabled` do not exist.

    This will happen when the configuration file does not specify these values::

        profile_name:
            default: False
    """
    with configure_caching(config_dict={'default': False}):
        # Check that `get_use_cache` also does not except, and works as expected
        assert not get_use_cache(identifier='aiida.calculations:templatereplacer')


@pytest.mark.parametrize(
    'config_dict', [{
        'wrong_key': ['foo']
    }, {
        'default': 2
    }, {
        'enabled': 4
    }, {
        'default': 'string'
    }, {
        'enabled': ['aiida.spam:Ni']
    }, {
        'default': True,
        'enabled': ['aiida.calculations:With:second_separator']
    }, {
        'enabled': ['aiida.sp*:Ni']
    }, {
        'disabled': ['aiida.sp*!bar']
    }, {
        'enabled': ['startswith.number.2bad']
    }, {
        'enabled': ['some.thing.in.this.is.a.keyword']
    }]
)
def test_invalid_configuration_dict(configure_caching, config_dict):
    """Test that `configure` raises for invalid configurations."""

    with pytest.raises(exceptions.ConfigurationError):
        with configure_caching(config_dict):
            pass


def test_invalid_identifier(use_default_configuration):  # pylint: disable=unused-argument
    """Test `get_use_cache` raises a `TypeError` if identifier is not a string."""
    with pytest.raises(TypeError):
        get_use_cache(identifier=int)


def test_default(use_default_configuration):  # pylint: disable=unused-argument
    """Verify that when not specifying any specific identifier, the `default` is used, which is set to `True`."""
    assert get_use_cache()


@pytest.mark.parametrize(['config_dict', 'enabled', 'disabled'], [
    ({
        'default': True,
        'enabled': ['aiida.calculations:arithmetic.add'],
        'disabled': ['aiida.calculations:templatereplacer']
    }, ['some_identifier', 'aiida.calculations:arithmetic.add', 'aiida.calculations:TEMPLATEREPLACER'
       ], ['aiida.calculations:templatereplacer']),
    ({
        'default': False,
        'enabled': ['aiida.calculations:arithmetic.add'],
        'disabled': ['aiida.calculations:templatereplacer']
    }, ['aiida.calculations:arithmetic.add'], ['aiida.calculations:templatereplacer', 'some_identifier']),
    ({
        'default': False,
        'enabled': ['aiida.calculations:*'],
    }, ['aiida.calculations:templatereplacer', 'aiida.calculations:arithmetic.add'], ['some_identifier']),
    ({
        'default': False,
        'enabled': ['aiida.calcul*'],
    }, ['aiida.calculations:templatereplacer', 'aiida.calculations:arithmetic.add'], ['some_identifier']),
    ({
        'default': False,
        'enabled': ['aiida.calculations:*'],
        'disabled': ['aiida.calculations:arithmetic.add']
    }, ['aiida.calculations:templatereplacer', 'aiida.calculations:ARIthmetic.add'
       ], ['some_identifier', 'aiida.calculations:arithmetic.add']),
    ({
        'default': False,
        'enabled': ['aiida.calculations:ar*thmetic.add'],
        'disabled': ['aiida.calculations:*'],
    }, ['aiida.calculations:arithmetic.add', 'aiida.calculations:arblarghthmetic.add'
       ], ['some_identifier', 'aiida.calculations:templatereplacer']),
])
def test_configuration(configure_caching, config_dict, enabled, disabled):
    """Check that different caching configurations give the expected result.
    """
    with configure_caching(config_dict=config_dict):
        for identifier in enabled:
            assert get_use_cache(identifier=identifier)
        for identifier in disabled:
            assert not get_use_cache(identifier=identifier)


@pytest.mark.parametrize(
    ['config_dict', 'valid_identifiers', 'invalid_identifiers'],
    [({
        'default': False,
        'enabled': ['aiida.calculations:*thmetic.add'],
        'disabled': ['aiida.calculations:arith*ic.add']
    }, ['some_identifier', 'aiida.calculations:templatereplacer'], ['aiida.calculations:arithmetic.add']),
     ({
         'default': False,
         'enabled': ['aiida.calculations:arithmetic.add'],
         'disabled': ['aiida.calculations:arithmetic.add']
     }, ['some_identifier', 'aiida.calculations:templatereplacer'], ['aiida.calculations:arithmetic.add'])]
)
def test_ambiguous_configuration(configure_caching, config_dict, valid_identifiers, invalid_identifiers):
    """
    Check that calling 'get_use_cache' on identifiers for which the
    configuration is ambiguous raises a ConfigurationError.
    """
    with configure_caching(config_dict=config_dict):
        for identifier in valid_identifiers:
            get_use_cache(identifier=identifier)
        for identifier in invalid_identifiers:
            with pytest.raises(exceptions.ConfigurationError):
                get_use_cache(identifier=identifier)


def test_enable_caching_specific(configure_caching):
    """
    Check that using enable_caching for a specific identifier works.
    """
    identifier = 'some_ident'
    with configure_caching({'default': False}):
        with enable_caching(identifier=identifier):
            assert get_use_cache(identifier=identifier)


def test_enable_caching_global(configure_caching):
    """
    Check that using enable_caching for a specific identifier works.
    """
    specific_identifier = 'some_ident'
    with configure_caching(config_dict={'default': False, 'disabled': [specific_identifier]}):
        with enable_caching():
            assert get_use_cache(identifier='some_other_ident')
            assert get_use_cache(identifier=specific_identifier)


def test_disable_caching_specific(configure_caching):
    """
    Check that using disable_caching for a specific identifier works.
    """
    identifier = 'some_ident'
    with configure_caching({'default': True}):
        with disable_caching(identifier=identifier):
            assert not get_use_cache(identifier=identifier)


def test_disable_caching_global(configure_caching):
    """
    Check that using disable_caching for a specific identifier works.
    """
    specific_identifier = 'some_ident'
    with configure_caching(config_dict={'default': True, 'enabled': [specific_identifier]}):
        with disable_caching():
            assert not get_use_cache(identifier='some_other_ident')
            assert not get_use_cache(identifier=specific_identifier)


@pytest.mark.parametrize(
    'identifier', [
        'aiida.spam:Ni', 'aiida.calculations:With:second_separator', 'aiida.sp*:Ni', 'aiida.sp*!bar',
        'startswith.number.2bad', 'some.thing.in.this.is.a.keyword'
    ]
)
def test_enable_disable_invalid(identifier):
    """
    Test that the enable and disable context managers raise when given
    an invalid identifier.
    """
    with pytest.raises(ValueError):
        with enable_caching(identifier=identifier):
            pass
    with pytest.raises(ValueError):
        with disable_caching(identifier=identifier):
            pass
