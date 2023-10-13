# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`aiida.cmdline.params.options.callable` module."""
from click.shell_completion import ShellComplete
import pytest

from aiida.cmdline.commands.cmd_verdi import verdi


def _get_completions(cli, args, incomplete):
    comp = ShellComplete(cli, {}, cli.name, '_CLICK_COMPLETE')
    return comp.get_completions(args, incomplete)


@pytest.fixture
def unload_config():
    """Temporarily unload the config by setting ``aiida.manage.configuration.CONFIG`` to ``None``."""
    from aiida.manage import configuration

    config = configuration.CONFIG
    configuration.CONFIG = None
    yield
    configuration.CONFIG = config


@pytest.mark.usefixtures('unload_config')
def test_callable_default_resilient_parsing():
    """Test that tab-completion of ``verdi`` does not evaluate defaults that load the config, which is expensive."""
    from aiida.manage import configuration

    assert configuration.CONFIG is None
    completions = [c.value for c in _get_completions(verdi, [], '')]
    assert 'help' in completions
    assert configuration.CONFIG is None
