###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.AuthInfo tests for the export and import routines"""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive
from aiida.tools.archive.abstract import get_format


@pytest.mark.usefixtures('aiida_localhost')
@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_all_no_authinfo(tmp_path):
    """Test archive creation that does not include authinfo."""
    filename1 = tmp_path / 'export1.aiida'
    create_archive(None, filename=filename1, include_authinfos=False)
    with get_format().open(filename1, 'r') as archive:
        assert archive.querybuilder().append(orm.AuthInfo).count() == 0


@pytest.mark.usefixtures('aiida_localhost')
@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_all_with_authinfo(tmp_path):
    """Test archive creation that does include authinfo."""
    filename1 = tmp_path / 'export1.aiida'
    create_archive(None, filename=filename1, include_authinfos=True)
    with get_format().open(filename1, 'r') as archive:
        assert archive.querybuilder().append(orm.AuthInfo).count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_comp_with_authinfo(tmp_path, aiida_localhost):
    """Test archive creation that does include authinfo."""
    filename1 = tmp_path / 'export1.aiida'
    create_archive([aiida_localhost], filename=filename1, include_authinfos=True)
    with get_format().open(filename1, 'r') as archive:
        assert archive.querybuilder().append(orm.AuthInfo).count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_import_authinfo(aiida_profile, tmp_path, aiida_localhost):
    """Test archive import, including authinfo"""
    filename1 = tmp_path / 'export1.aiida'
    create_archive([aiida_localhost], filename=filename1, include_authinfos=True)
    aiida_profile.reset_storage()
    # create a computer + authinfo, so that the PKs are different than the original ones
    # (to check that they are correctly translated)
    computer = orm.Computer(
        label='localhost-other',
        description='localhost computer set up by test manager',
        hostname='localhost-other',
        workdir=str(tmp_path),
        transport_type='core.local',
        scheduler_type='core.direct',
    )
    computer.store()
    computer.set_minimum_job_poll_interval(0.0)
    computer.configure()
    assert orm.AuthInfo.collection.count() == 1
    import_archive(filename1, include_authinfos=False)
    assert orm.AuthInfo.collection.count() == 1
    import_archive(filename1, include_authinfos=True)
    assert orm.AuthInfo.collection.count() == 2
    # re-import should be a no-op
    import_archive(filename1, include_authinfos=True)
    assert orm.AuthInfo.collection.count() == 2
