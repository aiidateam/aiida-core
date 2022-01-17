# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests the `request_ProfileAccessManageraccess` class."""
# pylint: disable=protected-access

from os import listdir
from subprocess import PIPE, Popen

import psutil
import pytest

from aiida.backends.managers.profile_access import ProfileAccessManager
from aiida.common.exceptions import LockedProfileError, LockingProfileError


@pytest.fixture(name='profile_access_manager')
def fixture_profile_access_manager():
    """Create special SQLAlchemy engine for use with QueryBuilder - backend-agnostic"""
    from aiida.manage.manager import get_manager
    aiida_profile = get_manager().get_profile()
    return ProfileAccessManager(aiida_profile)


class TestProcess():
    """Object that can start/stop an aiida process.

    After starting an aiida process, there has to be a time delay after the Popen
    command to allow some time for the process to be recorded.
    """

    def __init__(self):
        self._process = None

    def start(self, should_raise=False, run_secs=30, wait_secs=1):
        """Starts a new process."""
        import time

        if self._process is not None:
            self.stop()

        with open('temp_file.py', 'w', encoding='utf-8') as fileobj:
            fileobj.write('import time\n')
            fileobj.write(f'time.sleep({run_secs})\n')

        self._process = Popen(['verdi', 'run', 'temp_file.py'], stderr=PIPE)  # pylint: disable=consider-using-with
        if should_raise:
            error = self._process.communicate()
            return self._process.pid, error

        time.sleep(wait_secs)
        return self._process.pid

    def stop(self):
        """Kills the current process."""
        if self._process is not None:
            self._process.stderr.close()
            self._process.kill()
            self._process.wait()
        self._process = None


def test_access_control(profile_access_manager):
    """Tests the request of access and the `_clear_stale_pid_files` method.

    Here we are also testing the `request_access` method indirectly.
    """
    records_dir = profile_access_manager._dirpath_records

    # Note: `is_active` will currently also be triggered by the test instance as
    # well, but this is incidental and we should not depend on it. Moreover, it
    # is not
    accessing_process = TestProcess()
    accessing_pid = accessing_process.start()
    assert profile_access_manager.is_active()
    accessing_process.stop()

    process_file = str(accessing_pid) + '.pid'
    process_temp = str(accessing_pid) + '.tmp'

    assert process_file in listdir(records_dir)
    assert process_temp not in listdir(records_dir)

    profile_access_manager._clear_stale_pid_files()
    assert process_file not in listdir(records_dir)


def test_lock(profile_access_manager, monkeypatch):
    """Tests the `lock` method.

    Not that all underlying methods are already being tested elsewhere and can be
    thinker with. This includes:

     - `_raise_if_locked`
     - `_raise_if_active`
     - `_clear_stale_pid_files`

    """
    locking_proc = TestProcess()
    locking_pid = locking_proc.start()
    monkeypatch.setattr(profile_access_manager, 'process', psutil.Process(locking_pid))

    # It will not lock if there is a process accessing.
    access_proc = TestProcess()
    access_pid = access_proc.start()
    with pytest.raises(LockingProfileError) as exc:
        with profile_access_manager.lock():
            pass
    assert str(locking_pid) in str(exc.value)
    assert str(access_pid) in str(exc.value)
    access_proc.stop()

    # It will not let other process access if it locks.
    # We need to mock the check on other accessing processes because otherwise
    # it will detect the pytest process.
    def mock_raise_if_1(error_message):  # pylint: disable=unused-argument
        """Mock function for the `raise_if` methods."""

    monkeypatch.setattr(profile_access_manager, '_raise_if_active', mock_raise_if_1)

    with profile_access_manager.lock():
        assert profile_access_manager.is_locked()
        access_proc = TestProcess()
        access_pid, error = access_proc.start(should_raise=True)
        access_proc.stop()
        assert str(locking_pid) in str(error[1])
        assert str(access_pid) in str(error[1])
    assert not profile_access_manager.is_locked()

    # This will raise after the lock file is created, allowing to test for
    # racing conditions
    records_dir = profile_access_manager._dirpath_records

    def mock_raise_if_2(message_start):
        """Mock function for the `raise_if` methods."""
        for filename in listdir(records_dir):
            if 'lock' in filename:
                raise RuntimeError(message_start)

    monkeypatch.setattr(profile_access_manager, '_raise_if_locked', mock_raise_if_2)

    with pytest.raises(RuntimeError) as exc:
        with profile_access_manager.lock():
            pass
    assert str(locking_pid) in str(exc.value)

    # To test the second call to `_raise_if_active` we need to unset `_raise_if_locked`
    # in case that is called first, but then we need to set again the internal PID
    monkeypatch.undo()
    monkeypatch.setattr(profile_access_manager, 'process', psutil.Process(locking_pid))
    monkeypatch.setattr(profile_access_manager, '_raise_if_active', mock_raise_if_2)

    with pytest.raises(RuntimeError) as exc:
        with profile_access_manager.lock():
            pass
    assert str(locking_pid) in str(exc.value)

    locking_proc.stop()


def test_clear_locks(profile_access_manager):
    """Tests the `test_clear_locks` method."""
    records_dir = profile_access_manager._dirpath_records
    lockfile = records_dir / '1234567890.lock'

    assert not profile_access_manager.is_locked()
    lockfile.touch()
    assert profile_access_manager.is_locked()
    profile_access_manager.clear_locks()
    assert not profile_access_manager.is_locked()


@pytest.mark.parametrize('text_pattern', ['is being locked', 'was locked while'])
def test_access_requested_errors(profile_access_manager, monkeypatch, text_pattern):
    """Tests the `request_access` method errors when blocked."""
    accessing_process = TestProcess()
    accessing_pid = accessing_process.start()

    def mock_raise_if_locked(error_message):
        """Mock of _raise_if_locked."""
        if text_pattern in error_message:
            raise LockedProfileError(error_message)

    monkeypatch.setattr(profile_access_manager, '_raise_if_locked', mock_raise_if_locked)
    monkeypatch.setattr(profile_access_manager, 'process', psutil.Process(accessing_pid))

    with pytest.raises(LockedProfileError) as exc:
        profile_access_manager.request_access()
    accessing_process.stop()

    assert profile_access_manager.profile.name in str(exc.value)
    assert str(accessing_pid) in str(exc.value)


def test_raise_methods(profile_access_manager, monkeypatch):
    """Test the `_raise_if_active` and `_raise_if_locked` methods.

    The underlying `_get_tracking_files` method is mocked, so it always provides a single
    result of a temporary file with arbitrary content, and we are just checking that the
    relevant information is being passed and shown on the error message.
    """
    from pathlib import Path

    pass_message = 'This message should be on the error value'
    file_content = 'This is the file content'
    file_stem = '123456'

    tempfile = Path(file_stem + '.txt')
    tempfile.write_text(file_content, encoding='utf-8')

    def mock_get_tracking_files(*args, **kwargs):
        """Mock of _raise_if_locked."""
        return [tempfile]

    monkeypatch.setattr(profile_access_manager, '_get_tracking_files', mock_get_tracking_files)

    with pytest.raises(LockingProfileError) as exc:
        profile_access_manager._raise_if_active(pass_message)
    error_message = str(exc.value)
    assert pass_message in error_message
    assert tempfile.stem in error_message
    assert file_content in error_message

    with pytest.raises(LockedProfileError) as exc:
        profile_access_manager._raise_if_locked(pass_message)
    error_message = str(exc.value)
    assert pass_message in error_message
    assert tempfile.stem in error_message

    tempfile.unlink()


def test_get_tracking_files(profile_access_manager):
    """Test the `_get_tracking_files` method for listing `.pid` and `.lock` files."""
    records_dir = profile_access_manager._dirpath_records

    reference_set = {filename for filename in listdir(records_dir) if filename.endswith('.pid')}
    resulting_set = {filepath.name for filepath in profile_access_manager._get_tracking_files('.pid')}
    assert reference_set == resulting_set

    with profile_access_manager.lock():
        reference_set = {filename for filename in listdir(records_dir) if filename.endswith('.lock')}
        resulting_set = {filepath.name for filepath in profile_access_manager._get_tracking_files('.lock')}
        assert reference_set == resulting_set
