###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.exit_code.ExitCode`."""

import pytest

from aiida.engine import ExitCode


def test_exit_code_defaults():
    """Test that the defaults are properly set."""
    exit_code = ExitCode()
    assert exit_code.status == 0
    assert exit_code.message is None
    assert exit_code.invalidates_cache is False


def test_exit_code_construct():
    """Test that the constructor allows to override defaults."""
    status = 418
    message = 'I am a teapot'
    invalidates_cache = True

    exit_code = ExitCode(status, message, invalidates_cache)
    assert exit_code.status == status
    assert exit_code.message == message
    assert exit_code.invalidates_cache == invalidates_cache


def test_exit_code_serializability():
    """Test that an `ExitCode` instance can be serialized and deserialized with `yaml`."""
    import yaml

    exit_code = ExitCode()
    serialized = yaml.dump(exit_code)
    # The default loaders are "safe" and won't load an ``ExitCode``, however, the ``Loader`` loader will.
    deserialized = yaml.load(serialized, Loader=yaml.Loader)

    assert deserialized == exit_code
    assert isinstance(deserialized, ExitCode)


def test_exit_code_equality():
    """Test that the equality operator works properly."""
    exit_code_origin = ExitCode(1, 'message', True)
    exit_code_clone = ExitCode(1, 'message', True)
    exit_code_different = ExitCode(2, 'message', True)

    assert exit_code_origin == exit_code_clone
    assert exit_code_clone != exit_code_different

    # Check default `ExitCode` also matches normal tuples
    exit_code = ExitCode()
    assert exit_code == (0, None, False)

    assert exit_code != {}
    assert exit_code != []
    assert exit_code != ()
    assert exit_code != (0)
    assert exit_code != (None,)
    assert exit_code != (0, None)
    assert exit_code != [0, None, False]
    assert exit_code != [0, None, False, 'test']

    # `ExitCode` instances should match bare tuples as long as the content is the same
    exit_code = ExitCode(1, 'message', True)
    assert exit_code == (1, 'message', True)
    assert exit_code != ()


def test_exit_code_template_message():
    """Test that an exit code with a templated message can be called to replace the parameters."""
    message_template = 'Wrong parameter {parameter}'
    parameter_name = 'some_parameter'

    exit_code_base = ExitCode(418, message_template)
    exit_code_called = exit_code_base.format(parameter=parameter_name)

    # Incorrect placeholder
    with pytest.raises(ValueError):
        exit_code_base.format(non_existing_parameter=parameter_name)

    # Missing placeholders
    with pytest.raises(ValueError):
        exit_code_base.format()

    assert exit_code_base != exit_code_called  # Calling the exit code should return a new instance
    assert exit_code_called.message == message_template.format(parameter=parameter_name)


def test_exit_code_expand_tuple():
    """Test that an exit code instance can be expanded in its attributes like a tuple."""
    status = 418
    message = 'I am a teapot'
    invalidates_cache = True

    status_exp, message_exp, invalidates_cache_exp = ExitCode(418, message, True)

    assert status == status_exp
    assert message == message_exp
    assert invalidates_cache == invalidates_cache_exp
