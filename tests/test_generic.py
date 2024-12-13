###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the use of the DB."""

import pytest

from aiida import orm


@pytest.mark.usefixtures('suppress_internal_deprecations')
def test_code_local(aiida_localhost):
    """Test local code.

    Remove this test when legacy `Code` is removed in v3.0.
    """
    import tempfile

    from aiida.common.exceptions import ValidationError
    from aiida.orm import Code

    code = Code(local_executable='test.sh')
    with pytest.raises(ValidationError):
        # No file with name test.sh
        code.store()

    with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
        fhandle.write('#/bin/bash\n\necho test run\n')
        fhandle.flush()
        code.base.repository.put_object_from_filelike(fhandle, 'test.sh')

    code.store()
    assert code.can_run_on(aiida_localhost)
    assert code.get_local_executable(), 'test.sh'
    assert code.get_execname(), 'stest.sh'


@pytest.mark.usefixtures('suppress_internal_deprecations')
def test_code_remote(aiida_localhost):
    """Test remote code.

    Remove this test when legacy `Code` is removed in v3.0.
    """
    import tempfile

    from aiida.common.exceptions import ValidationError
    from aiida.orm import Code

    with pytest.raises(ValueError):
        # remote_computer_exec has length 2 but is not a list or tuple
        Code(remote_computer_exec='ab')

    # invalid code path
    with pytest.raises(ValueError):
        Code(remote_computer_exec=(aiida_localhost, ''))

    # Relative path is invalid for remote code
    with pytest.raises(ValueError):
        Code(remote_computer_exec=(aiida_localhost, 'subdir/run.exe'))

    # first argument should be a computer, not a string
    with pytest.raises(TypeError):
        Code(remote_computer_exec=('localhost', '/bin/ls'))

    code = Code(remote_computer_exec=(aiida_localhost, '/bin/ls'))
    with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
        fhandle.write('#/bin/bash\n\necho test run\n')
        fhandle.flush()
        code.base.repository.put_object_from_filelike(fhandle, 'test.sh')

    with pytest.raises(ValidationError):
        # There are files inside
        code.store()

    # If there are no files, I can store
    code.base.repository.delete_object('test.sh')
    code.store()

    assert code.get_remote_computer().pk == aiida_localhost.pk
    assert code.get_remote_exec_path() == '/bin/ls'
    assert code.get_execname() == '/bin/ls'

    assert code.can_run_on(aiida_localhost)
    othercomputer = orm.Computer(
        label='another_localhost',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.pbspro',
        workdir='/tmp/aiida',
    ).store()
    assert not code.can_run_on(othercomputer)


class TestBool:
    """Test AiiDA Bool class."""

    @staticmethod
    def test_bool_conversion():
        for val in [True, False]:
            assert val == bool(orm.Bool(val))

    @staticmethod
    def test_int_conversion():
        for val in [True, False]:
            assert int(val) == int(orm.Bool(val))
