###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.orm.nodes.data.code.shell`."""

import pytest

from aiida.orm import ShellCode


def test_constructor(aiida_localhost):
    """Test initializing an instance."""
    code = ShellCode(
        label='bash',
        computer=aiida_localhost,
        filepath_executable='/bin/bash',
        default_calc_job_plugin='core.shell',
    )
    assert isinstance(code, ShellCode)


def test_constructor_invalid(aiida_localhost):
    """Test the constructor raises if ``default_calc_job_plugin`` is not ``core.shell``."""
    with pytest.raises(ValueError, match=r'`default_calc_job_plugin` has to be `core.shell`, but got: .*'):
        ShellCode(
            label='bash',
            computer=aiida_localhost,
            filepath_executable='/bin/bash',
            default_calc_job_plugin='core.arithmetic.add',
        )


@pytest.mark.parametrize(
    ('value', 'exception'),
    (
        ('core.shell', None),
        ('core.arithmetic.add', r'`default_calc_job_plugin` has to be `core.shell`, but got: .*'),
    ),
)
def test_validate_default_calc_job_plugin(value, exception):
    """Test the constructor raises if ``default_calc_job_plugin`` is not ``core.shell``."""
    if exception:
        with pytest.raises(ValueError, match=exception):
            ShellCode.validate_default_calc_job_plugin(value)
    else:
        assert ShellCode.validate_default_calc_job_plugin(value) is None
