###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for remote utilities."""

from unittest.mock import patch

import pytest

from aiida import orm
from aiida.orm.nodes.data.remote.base import RemoteData
from aiida.orm.utils import _remote as remote


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

    folder_unconfigured = RemoteData(remote_path=str(tmp_path / 'unconfigured-folder'), computer=unconfigured)
    folder_configured = RemoteData(remote_path=str(tmp_path / 'configured-folder'), computer=configured)

    warnings: list[str] = []
    monkeypatch.setattr(remote.echo, 'echo_warning', lambda message, **kwargs: warnings.append(message))
    monkeypatch.setattr(remote.echo, 'echo_success', lambda *args, **kwargs: None)

    with patch.object(RemoteData, '_clean', autospec=True) as mock_clean:
        remote.clean_mapping_remote_paths(
            {
                unconfigured.uuid: [folder_unconfigured],
                configured.uuid: [folder_configured],
            },
            silent=True,
        )

    mock_clean.assert_called_once()
    assert mock_clean.call_args.args[0] is folder_configured

    assert warnings == [
        f'Skipping 1 remote folders on `{unconfigured.label}`: ' f'computer is not configured for user `{user.email}`'
    ]
