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

import contextlib
import json

import yaml
import pytest

from aiida.common import exceptions
from aiida.manage.caching import get_use_cache, enable_caching, disable_caching


@pytest.fixture
def configure_caching(temporary_config_instance):
    """
    Fixture to set the caching configuration in the test profile to
    a specific dictionary. This is done by creating a temporary
    caching configuration file.
    """

    @contextlib.contextmanager
    def inner(config_dict):
        for key, value in config_dict.items():
            temporary_config_instance.set_option(f'caching.{key}', value)
        yield
        # reset the configuration
        for key in config_dict.keys():
            temporary_config_instance.unset_option(f'caching.{key}')

    return inner


def test_merge_deprecated_yaml(tmp_path):
    """Test that an existing 'cache_config.yml' is correctly merged into the main config.

    An AiidaDeprecationWarning should also be raised.
    """
    from aiida.common.warnings import AiidaDeprecationWarning
    from aiida.manage import configuration
    from aiida.manage.configuration import settings, load_profile, reset_profile, get_config_option

    # Store the current configuration instance and config directory path
    current_config = configuration.CONFIG
    current_config_path = current_config.dirpath
    current_profile_name = configuration.PROFILE.name

    try:
        reset_profile()
        configuration.CONFIG = None

        # Create a temporary folder, set it as the current config directory path
        settings.AIIDA_CONFIG_FOLDER = str(tmp_path)
        config_dictionary = {
            'CONFIG_VERSION': {
                'CURRENT': 5,
                'OLDEST_COMPATIBLE': 5
            },
            'default_profile': 'default',
            'profiles': {
                'default': {
                    'PROFILE_UUID': '00000000000000000000000000000000',
                    'default_user_email': 'dummy@localhost',
                    'AIIDADB_ENGINE': 'postgresql_psycopg2',
                    'AIIDADB_BACKEND': 'django',
                    'AIIDADB_HOST': 'localhost',
                    'AIIDADB_PORT': 5432,
                    'AIIDADB_NAME': 'name',
                    'AIIDADB_USER': 'user',
                    'AIIDADB_PASS': 'pass',
                    'AIIDADB_REPOSITORY_URI': f"file:///{tmp_path/'repo'}",
                }
            }
        }
        cache_dictionary = {
            'default': {
                'default': True,
                'enabled': ['aiida.calculations:quantumespresso.pw'],
                'disabled': ['aiida.calculations:templatereplacer']
            }
        }
        tmp_path.joinpath('config.json').write_text(json.dumps(config_dictionary))
        tmp_path.joinpath('cache_config.yml').write_text(yaml.dump(cache_dictionary))
        with pytest.warns(AiidaDeprecationWarning, match='cache_config.yml'):
            configuration.CONFIG = configuration.load_config()
        load_profile('default')

        assert get_config_option('caching.default') is True
        assert get_config_option('caching.enabled') == ['aiida.calculations:quantumespresso.pw']
        assert get_config_option('caching.disabled') == ['aiida.calculations:templatereplacer']
        # should have now been moved to cache_config.yml.<DATETIME>
        assert not tmp_path.joinpath('cache_config.yml').exists()
    finally:
        # Reset the config folder path and the config instance. Note this will always be executed after the yield no
        # matter what happened in the test that used this fixture.
        reset_profile()
        settings.AIIDA_CONFIG_FOLDER = current_config_path
        configuration.CONFIG = current_config
        load_profile(current_profile_name)


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
        'default': 'x'
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


def test_invalid_identifier(configure_caching):  # pylint: disable=unused-argument
    """Test `get_use_cache` raises a `TypeError` if identifier is not a string."""
    with configure_caching({}):
        with pytest.raises(TypeError):
            get_use_cache(identifier=int)


def test_default(configure_caching):  # pylint: disable=unused-argument
    """Verify that when not specifying any specific identifier, the `default` is used, which is set to `True`."""
    with configure_caching({'default': True}):
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
