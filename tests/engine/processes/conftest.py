###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures shared by the tests of checkpoint persistence and of the class identity it records."""

import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from aiida.engine.processes.persistence import CheckpointSerializable


@pytest.fixture
def user_serializable(importable_module: Callable[..., ModuleType]) -> type[CheckpointSerializable]:
    """A class from a directory on this interpreter's path only, as a user's own module would be."""
    module = importable_module(
        'usercheckpoint',
        """
        from aiida.engine.processes.persistence import CheckpointSerializable


        class UserSerializable(CheckpointSerializable):
            def __init__(self, value='from the user module'):
                self.value = value

            def save_instance_state(self, out_state, save_context):
                super().save_instance_state(out_state, save_context)
                out_state['value'] = self.value

            def load_instance_state(self, saved_state, load_context):
                super().load_instance_state(saved_state, load_context)
                self.value = saved_state['value']
        """,
    )

    return module.UserSerializable


@pytest.fixture
def worker_without(tmp_path: Path) -> tuple[str, ...]:
    """The paths of an interpreter that has everything this one has, except the user's own directory."""
    return tuple(entry for entry in sys.path if entry != str(tmp_path))


@pytest.fixture(autouse=True)
def reset_identity_policy_warnings():
    """Clear what the identity policy has warned about, before every test in this directory.

    That memory is interpreter-wide, so without this a test observing one of those warnings passes or fails
    depending on whether an earlier test had already provoked the same one.
    """
    from aiida.engine.processes import _class_identity

    _class_identity.identity_policy.reset_warnings()

    yield
