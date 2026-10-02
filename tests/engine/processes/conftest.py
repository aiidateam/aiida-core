###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures for checkpoint persistence tests."""

from collections.abc import Callable
from types import ModuleType

import pytest

from aiida.engine.processes.persistence import CheckpointSerializable


@pytest.fixture
def user_serializable(importable_module: Callable[..., ModuleType]) -> type[CheckpointSerializable]:
    """Return a serializable class from a temporary importable module."""
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
