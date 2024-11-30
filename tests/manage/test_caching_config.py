###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the functionality that reads and modifies the caching configuration file."""

import contextlib
import json
import pathlib

import pytest
import yaml

from aiida.common import exceptions
from aiida.manage.caching import _validate_identifier_pattern, disable_caching, enable_caching, get_use_cache


@pytest.fixture
def configure_caching(config_with_profile_factory):
    """Fixture to set the caching configuration in the test profile to
    a specific dictionary. This is done by creating a temporary
    caching configuration file.
    """
    config = config_with_profile_factory()

    @contextlib.contextmanager
    def inner(config_dict):
        for key, value in config_dict.items():
            config.set_option(f'caching.{key}', value)
        yield
        # reset the configuration
        for key in config_dict.keys():
            config.unset_option(f'caching.{key}')

    return inner


def test_merge_deprecated_yaml(tmp_path):
    """Test that an existing 'cache_config.yml' is correctly merged into the main config.

    An AiidaDeprecationWarning should also be raised.
    """
    from aiida.common.warnings import AiidaDeprecationWarning
    from aiida.manage import configuration, get_manager
    from aiida.manage.configuration import get_config_option, load_profile
    from aiida.manage.configuration.settings import AiiDAConfigDir

    # Store the current configuration instance and config directory path
    current_config = configuration.CONFIG
    current_config_path = pathlib.Path(current_config.dirpath)
    current_profile_name = configuration.get_profile().name

    try:
        get_manager().unload_profile()
        configuration.CONFIG = None

        # Create a temporary folder, set it as the current config directory path
        AiiDAConfigDir.set(pathlib.Path(tmp_path))
        config_dictionary = json.loads(
            pathlib.Path(__file__)
            .parent.joinpath('configuration/migrations/test_samples/reference/6.json')
            .read_text(encoding='utf-8')
        )
        config_dictionary['profiles']['default']['storage']['config']['repository_uri'] = f"file:///{tmp_path/'repo'}"
        cache_dictionary = {
            'default': {
                'default': True,
                'enabled': ['aiida.calculations:core.arithmetic.add'],
                'disabled': ['aiida.calculations:core.templatereplacer'],
            }
        }
        tmp_path.joinpath('config.json').write_text(json.dumps(config_dictionary))
        tmp_path.joinpath('cache_config.yml').write_text(yaml.dump(cache_dictionary))
        with pytest.warns(AiidaDeprecationWarning, match='cache_config.yml'):
            configuration.CONFIG = configuration.load_config()
        load_profile('default')

        assert get_config_option('caching.default_enabled') is True
        assert get_config_option('caching.enabled_for') == ['aiida.calculations:core.arithmetic.add']
        assert get_config_option('caching.disabled_for') == ['aiida.calculations:core.templatereplacer']
        # should have now been moved to cache_config.yml.<DATETIME>
        assert not tmp_path.joinpath('cache_config.yml').exists()
    finally:
        # Reset the config folder path and the config instance. Note this will always be executed after the yield no
        # matter what happened in the test that used this fixture.
        get_manager().unload_profile()
        AiiDAConfigDir.set(current_config_path)
        configuration.CONFIG = current_config
        load_profile(current_profile_name)


def test_no_enabled_disabled(configure_caching):
    """Test that `aiida.manage.caching.configure` does not except when either `enabled` or `disabled` do not exist.

    This will happen when the configuration file does not specify these values::

        profile_name:
            default: False
    """
    with configure_caching(config_dict={'default_enabled': False}):
        # Check that `get_use_cache` also does not except, and works as expected
        assert not get_use_cache(identifier='aiida.calculations:core.templatereplacer')


@pytest.mark.parametrize(
    'config_dict',
    [
        {'wrong_key': ['foo']},
        {'default_enabled': 'x'},
        {'enabled_for': 4},
        {'default_enabled': 'string'},
        {'enabled_for': ['aiida.spam:Ni']},
        {'default_enabled': True, 'enabled_for': ['aiida.calculations:With:second_separator']},
        {'enabled_for': ['aiida.sp*:Ni']},
        {'disabled_for': ['aiida.sp*!bar']},
        {'enabled_for': ['startswith.number.2bad']},
        {'enabled_for': ['some.thing.in.this.is.a.keyword']},
    ],
)
def test_invalid_configuration_dict(configure_caching, config_dict):
    """Test that `configure` raises for invalid configurations."""
    with pytest.raises(exceptions.ConfigurationError):
        with configure_caching(config_dict):
            pass


def test_invalid_identifier(configure_caching):
    """Test `get_use_cache` raises a `TypeError` if identifier is not a string."""
    with configure_caching({}):
        with pytest.raises(TypeError):
            get_use_cache(identifier=int)


def test_default(configure_caching):
    """Verify that when not specifying any specific identifier, the `default` is used, which is set to `True`."""
    with configure_caching({'default_enabled': True}):
        assert get_use_cache()


@pytest.mark.parametrize(
    ['config_dict', 'enabled_for', 'disabled_for'],
    [
        (
            {
                'default_enabled': True,
                'enabled_for': ['aiida.calculations:core.arithmetic.add'],
                'disabled_for': ['aiida.calculations:core.templatereplacer'],
            },
            ['some_identifier', 'aiida.calculations:core.arithmetic.add', 'aiida.calculations:TEMPLATEREPLACER'],
            ['aiida.calculations:core.templatereplacer'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:core.arithmetic.add'],
                'disabled_for': ['aiida.calculations:core.templatereplacer'],
            },
            ['aiida.calculations:core.arithmetic.add'],
            ['aiida.calculations:core.templatereplacer', 'some_identifier'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:*'],
            },
            ['aiida.calculations:core.templatereplacer', 'aiida.calculations:core.arithmetic.add'],
            ['some_identifier'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calcul*'],
            },
            ['aiida.calculations:core.templatereplacer', 'aiida.calculations:core.arithmetic.add'],
            ['some_identifier'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:*'],
                'disabled_for': ['aiida.calculations:core.arithmetic.add'],
            },
            ['aiida.calculations:core.templatereplacer', 'aiida.calculations:core.ARIthmetic.add'],
            ['some_identifier', 'aiida.calculations:core.arithmetic.add'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:core.ar*thmetic.add'],
                'disabled_for': ['aiida.calculations:*'],
            },
            ['aiida.calculations:core.arithmetic.add', 'aiida.calculations:core.arblarghthmetic.add'],
            ['some_identifier', 'aiida.calculations:core.templatereplacer'],
        ),
    ],
)
def test_configuration(configure_caching, config_dict, enabled_for, disabled_for):
    """Check that different caching configurations give the expected result."""
    with configure_caching(config_dict=config_dict):
        for identifier in enabled_for:
            assert get_use_cache(identifier=identifier)
        for identifier in disabled_for:
            assert not get_use_cache(identifier=identifier)


@pytest.mark.parametrize(
    ['config_dict', 'valid_identifiers', 'invalid_identifiers'],
    [
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:*thmetic.add'],
                'disabled_for': ['aiida.calculations:arith*ic.add'],
            },
            ['some_identifier', 'aiida.calculations:core.templatereplacer'],
            ['aiida.calculations:arithmetic.add'],
        ),
        (
            {
                'default_enabled': False,
                'enabled_for': ['aiida.calculations:core.arithmetic.add'],
                'disabled_for': ['aiida.calculations:core.arithmetic.add'],
            },
            ['some_identifier', 'aiida.calculations:core.templatereplacer'],
            ['aiida.calculations:core.arithmetic.add'],
        ),
    ],
)
def test_ambiguous_configuration(configure_caching, config_dict, valid_identifiers, invalid_identifiers):
    """Check that calling 'get_use_cache' on identifiers for which the
    configuration is ambiguous raises a ConfigurationError.
    """
    with configure_caching(config_dict=config_dict):
        for identifier in valid_identifiers:
            get_use_cache(identifier=identifier)
        for identifier in invalid_identifiers:
            with pytest.raises(exceptions.ConfigurationError):
                get_use_cache(identifier=identifier)


def test_enable_caching_specific(configure_caching):
    """Check that using enable_caching for a specific identifier works."""
    identifier = 'some_ident'
    with configure_caching({'default_enabled': False}):
        with enable_caching(identifier=identifier):
            assert get_use_cache(identifier=identifier)


def test_enable_caching_global(configure_caching):
    """
    Check that using enable_caching for a specific identifier works.
    """
    specific_identifier = 'aiida.calculations.arithmetic.add.ArithmeticAddCalculation'
    with configure_caching(config_dict={'default_enabled': False, 'disabled_for': [specific_identifier]}):
        with enable_caching():
            assert get_use_cache(identifier='aiida.calculations.transfer.TransferCalculation')
            assert get_use_cache(identifier=specific_identifier)


def test_disable_caching_specific(configure_caching):
    """
    Check that using disable_caching for a specific identifier works.
    """
    identifier = 'aiida.calculations.arithmetic.add.ArithmeticAddCalculation'
    with configure_caching({'default_enabled': True}):
        with disable_caching(identifier=identifier):
            assert not get_use_cache(identifier=identifier)


def test_disable_caching_global(configure_caching):
    """
    Check that using disable_caching for a specific identifier works.
    """
    specific_identifier = 'aiida.calculations.arithmetic.add.ArithmeticAddCalculation'
    with configure_caching(config_dict={'default_enabled': True, 'enabled_for': [specific_identifier]}):
        with disable_caching():
            assert not get_use_cache(identifier='aiida.calculations.transfer.TransferCalculation')
            assert not get_use_cache(identifier=specific_identifier)


@pytest.mark.parametrize(
    'identifier',
    [
        'aiida.spam:Ni',
        'aiida.calculations:With:second_separator',
        'aiida.sp*:Ni',
        'aiida.sp*!bar',
        'startswith.number.2bad',
        'some.thing.in.this.is.a.keyword',
    ],
)
def test_enable_disable_invalid(identifier):
    """Test that the enable and disable context managers raise when given
    an invalid identifier.
    """
    with pytest.raises(ValueError):
        with enable_caching(identifier=identifier):
            pass
    with pytest.raises(ValueError):
        with disable_caching(identifier=identifier):
            pass


@pytest.mark.parametrize(
    'strict, identifier, matches',
    (
        (False, 'aiida.calculations:core.arithmetic.add', None),
        (False, 'aiida.calculations.arithmetic.add.ArithmeticAddCalculation', None),
        (False, 'aiida.calculations:core.non_existent', None),
        (False, 'aiida.calculations.arithmetic.non_existent.ArithmeticAddCalculation', None),
        (False, 'aiida.spam:Ni', r'does not match any of the AiiDA entry point group names\.'),
        (False, 'aiida.calculations:With:second_separator', r'Can contain at most one entry point string separator.*'),
        (False, 'aiida.sp*:Ni', r'does not match any of the AiiDA entry point group names\.'),
        (False, 'aiida.sp*!bar', r'Identifier part `sp\*!bar` can not match a fully qualified Python name.'),
        (False, 'startswith.number.2bad', r'is not a valid Python identifier\.'),
        (False, 'some.thing.in.this.is.a.keyword', r'is a reserved Python keyword\.'),
        (True, 'aiida.calculations:core.arithmetic.add', None),
        (True, 'aiida.calculations.arithmetic.add.ArithmeticAddCalculation', None),
        (True, 'aiida.calculations:core.non_existent', r'cannot be loaded\.'),
        (True, 'aiida.calculations.arithmetic.non_existent.ArithmeticAddCalculation', r'cannot be imported\.'),
        (True, 'aiida.spam:Ni', r'does not match any of the AiiDA entry point group names\.'),
        (True, 'aiida.calculations:With:second_separator', r'Can contain at most one entry point string separator.*'),
        (True, 'aiida.sp*:Ni', r'does not match any of the AiiDA entry point group names\.'),
        (True, 'aiida.sp*!bar', r'Identifier part `sp\*!bar` can not match a fully qualified Python name.'),
        (True, 'startswith.number.2bad', r'is not a valid Python identifier\.'),
        (True, 'some.thing.in.this.is.a.keyword', r'is a reserved Python keyword\.'),
    ),
)
def test_validate_identifier_pattern(strict, identifier, matches):
    """Test :func:`aiida.manage.caching._validate_identifier_pattern`."""
    if matches:
        with pytest.raises(ValueError, match=matches):
            _validate_identifier_pattern(identifier=identifier, strict=strict)
    else:
        _validate_identifier_pattern(identifier=identifier, strict=strict)
