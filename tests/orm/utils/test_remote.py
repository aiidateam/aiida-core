###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for remote utilities."""

from unittest.mock import Mock

import pytest

from aiida import orm
from aiida.orm.nodes.data.remote.base import RemoteData
from aiida.orm.utils import remote


@pytest.mark.usefixtures('aiida_profile_clean')
def test_clean_mapping_remote_paths_skips_unconfigured_computer(tmp_path, monkeypatch):
    """Unconfigured computers are skipped with a warning; configured ones in the same call are still cleaned."""
    user = orm.User.collection.get_default()

    unconfigured = orm.Computer(
        label='unconfigured-computer',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(tmp_path / 'unconfigured'),
    ).store()

    configured = orm.Computer(
        label='configured-computer',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(tmp_path / 'configured'),
    ).store()
    configured.configure(user=user)

    folder_unconfigured = Mock(spec=RemoteData)
    folder_configured = Mock(spec=RemoteData)

    warnings: list[str] = []
    monkeypatch.setattr(remote.echo, 'echo_warning', lambda message, **kwargs: warnings.append(message))
    monkeypatch.setattr(remote.echo, 'echo_success', lambda *args, **kwargs: None)

    remote.clean_mapping_remote_paths(
        {
            unconfigured.uuid: [folder_unconfigured],
            configured.uuid: [folder_configured],
        },
        silent=True,
    )

    folder_unconfigured._clean.assert_not_called()
    folder_configured._clean.assert_called_once()

    assert warnings == [
        f'Skipping 1 remote folders on `{unconfigured.label}`: '
        f'computer is not configured for user `{user.email}`'
    ]
