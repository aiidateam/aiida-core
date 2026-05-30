###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for remote utilities."""

from aiida import orm
from aiida.orm.utils import remote


class UncleanableRemoteFolder:
    """Remote folder that should not be cleaned."""

    def _clean(self, **kwargs):
        raise AssertionError('Unconfigured computers should be skipped.')


def test_clean_mapping_remote_paths_skips_unconfigured_computer(aiida_profile_clean, tmp_path, monkeypatch):
    """Test that remote cleanup skips computers without AuthInfo."""
    user = orm.User.collection.get_default()
    computer = orm.Computer(
        label='unconfigured-computer',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(tmp_path),
    ).store()

    warnings = []
    monkeypatch.setattr(remote.echo, 'echo_warning', warnings.append)

    remote.clean_mapping_remote_paths(
        {
            computer.uuid: [
                UncleanableRemoteFolder(),
                UncleanableRemoteFolder(),
            ]
        }
    )

    assert warnings == [
        f'Skipping 2 remote folders on {computer.label}: computer is not configured for user {user.email}'
    ]