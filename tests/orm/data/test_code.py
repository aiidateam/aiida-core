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
"""Tests for :class:`aiida.orm.nodes.data.code.Code` class."""
import tempfile

import pytest

from aiida.common.exceptions import NotExistent, UniquenessError, ValidationError
from aiida.orm import Code, Computer


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_local(aiida_localhost):
    """Test local code."""
    code = Code(local_executable='test.sh')
    code.label = 'label'

    with pytest.raises(ValidationError):
        # No file with name test.sh
        code.store()

    with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
        fhandle.write('#/bin/bash\n\necho test run\n')
        fhandle.flush()
        code.put_object_from_filelike(fhandle, 'test.sh')

    code.store()

    assert code.can_run_on(aiida_localhost)
    assert code.get_local_executable() == 'test.sh'
    assert code.get_execname() == './test.sh'


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_remote(aiida_localhost):
    """Test remote code."""
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
    code.label = 'label'

    with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
        fhandle.write('#/bin/bash\n\necho test run\n')
        fhandle.flush()
        code.put_object_from_filelike(fhandle, 'test.sh')

    with pytest.raises(ValidationError):
        # There are files inside
        code.store()

    # If there are no files, I can store
    code.delete_object('test.sh')
    code.store()

    assert code.get_remote_computer().pk == aiida_localhost.pk
    assert code.get_remote_exec_path() == '/bin/ls'
    assert code.get_execname() == '/bin/ls'

    assert code.can_run_on(aiida_localhost)
    othercomputer = Computer(
        label='another_localhost',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.pbspro',
        workdir='/tmp/aiida'
    ).store()
    assert not code.can_run_on(othercomputer)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.parametrize('label', ('', None))
def test_code_label_defined(aiida_localhost, label):
    """Verify that storing a code with no label (either ``None`` or an empty string) raises."""
    code = Code((aiida_localhost, '/bin/bash'))
    code.label = label

    with pytest.raises(ValidationError):
        code.store()


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_full_label_uniqueness(aiida_local_code_factory):
    """Verify that storing a code with an already existing full label (`label@computer.label`) raises."""
    label = 'some-label'
    code = aiida_local_code_factory('core.arithmetic.add', '/bin/bash', label=label)

    duplicate = Code((code.computer, '/bin/bash'))
    duplicate.label = code.label

    with pytest.raises(UniquenessError):
        duplicate.store()


@pytest.mark.usefixtures('clear_database_before_test')
def test_list_for_plugin(aiida_local_code_factory):
    """Test the ``Code.list_for_plugin`` classmethod."""
    entry_point = 'core.arithmetic.add'

    code1 = aiida_local_code_factory(entry_point, '/bin/true')
    code1.label = 'code1'
    code1.store()

    code2 = aiida_local_code_factory(entry_point, '/bin/true')
    code2.label = 'code2'
    code2.store()

    retrieved_pks = set(Code.list_for_plugin(entry_point, labels=False))
    assert retrieved_pks == {code1.pk, code2.pk}

    retrieved_labels = set(Code.list_for_plugin(entry_point, labels=True))
    assert retrieved_labels == {code1.label, code2.label}


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_get_from_string(aiida_localhost, aiida_local_code_factory):
    """Test the ``Code.get_from_string`` classmethod."""
    entry_point = 'core.arithmetic.add'

    code1 = aiida_local_code_factory(entry_point, '/bin/true')
    code1.label = 'code1'
    code1.store()

    code2 = aiida_local_code_factory(entry_point, '/bin/true')
    code2.label = 'code2'
    code2.store()

    # Test that the code1 can be loaded correctly with its label
    q_code_1 = Code.get_from_string(code1.label)
    assert q_code_1.id == code1.id
    assert q_code_1.label == code1.label
    assert q_code_1.get_remote_exec_path() == code1.get_remote_exec_path()

    # Test that the code2 can be loaded correctly with its label
    q_code_2 = Code.get_from_string(f'{code2.label}@{aiida_localhost.label}')  # pylint: disable=no-member
    assert q_code_2.id == code2.id
    assert q_code_2.label == code2.label
    assert q_code_2.get_remote_exec_path() == code2.get_remote_exec_path()

    # Calling get_from_string for a non string type raises exception
    with pytest.raises(TypeError):
        Code.get_from_string(code1.id)

    # Test that the lookup of a nonexistent code works as expected
    with pytest.raises(NotExistent):
        Code.get_from_string('nonexistent_code')


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_get(aiida_localhost, aiida_local_code_factory):
    """Test the ``Code.get`` classmethod."""
    entry_point = 'core.arithmetic.add'

    code1 = aiida_local_code_factory(entry_point, '/bin/true')
    code1.label = 'code1'
    code1.store()

    code2 = aiida_local_code_factory(entry_point, '/bin/true')
    code2.label = 'code2'
    code2.store()

    # Test that the code1 can be loaded correctly with its label only
    q_code_1 = Code.get(label=code1.label)
    assert q_code_1.id == code1.id
    assert q_code_1.label == code1.label
    assert q_code_1.get_remote_exec_path() == code1.get_remote_exec_path()

    # Test that the code1 can be loaded correctly with its id/pk
    q_code_1 = Code.get(code1.id)
    assert q_code_1.id == code1.id
    assert q_code_1.label == code1.label
    assert q_code_1.get_remote_exec_path() == code1.get_remote_exec_path()

    # Test that the code2 can be loaded correctly with its label and computername
    q_code_2 = Code.get(label=code2.label, machinename=aiida_localhost.label)  # pylint: disable=no-member
    assert q_code_2.id == code2.id
    assert q_code_2.label == code2.label
    assert q_code_2.get_remote_exec_path() == code2.get_remote_exec_path()

    # Test that the code2 can be loaded correctly with its id/pk
    q_code_2 = Code.get(code2.id)
    assert q_code_2.id == code2.id
    assert q_code_2.label == code2.label
    assert q_code_2.get_remote_exec_path() == code2.get_remote_exec_path()

    # Test that the lookup of a nonexistent code works as expected
    with pytest.raises(NotExistent):
        Code.get(label='nonexistent_code')

    # Add another code whose label is equal to pk of another code
    pk_label_duplicate = code1.pk
    code3 = Code()
    code3.set_remote_computer_exec((aiida_localhost, '/bin/true'))
    code3.label = pk_label_duplicate
    code3.store()

    # Since the label of code3 is identical to the pk of code1, calling
    # Code.get(pk_label_duplicate) should return code1, as the pk takes
    # precedence
    q_code_3 = Code.get(code3.label)
    assert q_code_3.id == code1.id
    assert q_code_3.label == code1.label
    assert q_code_3.get_remote_exec_path() == code1.get_remote_exec_path()


@pytest.mark.usefixtures('clear_database_before_test')
def test_code_description(aiida_localhost):
    """
    This test checks that the code description is retrieved correctly
    when the code is searched with its id and label.
    """
    # Create a code node
    code = Code()
    code.set_remote_computer_exec((aiida_localhost, '/bin/true'))
    code.label = 'test_code_label'
    code.description = 'test code description'
    code.store()

    q_code1 = Code.get(label=code.label)
    assert code.description == str(q_code1.description)

    q_code2 = Code.get(code.id)
    assert code.description == str(q_code2.description)
