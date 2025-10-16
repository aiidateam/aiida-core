###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests the `request_ProfileAccessManageraccess` class."""

from os import listdir
from pathlib import Path
from subprocess import PIPE, Popen

import psutil
import pytest

from aiida.common.exceptions import LockedProfileError, LockingProfileError
from aiida.manage.profile_access import ProfileAccessManager

###########################################################################
# SIMPLE UNIT TESTS
#
# This first section contains simple unit tests to verify the inner
# workings of the different methods. They are separated from a more
# global set of tests for the whole system.
#
###########################################################################


@pytest.fixture(name='profile_access_manager')
def fixture_profile_access_manager():
    """Create special SQLAlchemy engine for use with QueryBuilder - backend-agnostic"""
    from aiida.manage import get_manager

    aiida_profile = get_manager().get_profile()
    return ProfileAccessManager(aiida_profile)


def test_get_tracking_files(profile_access_manager):
    """Test the `_get_tracking_files` method for listing `.pid` and `.lock` files."""
    records_dir = profile_access_manager._dirpath_records

    # POPULATE WITH RECORDS
    filepath_list = [
        records_dir / 'file_1.pid',
        records_dir / 'file_2.pid',
        records_dir / 'file_3.pid',
        records_dir / 'file_4.lock',
        records_dir / 'file_5.lock',
        records_dir / 'file_6.etc',
    ]

    for filepath in filepath_list:
        filepath.touch()

    reference_set = {filename for filename in listdir(records_dir) if filename.endswith('.pid')}
    resulting_set = {filepath.name for filepath in profile_access_manager._get_tracking_files('.pid')}
    assert reference_set == resulting_set

    reference_set = {filename for filename in listdir(records_dir) if filename.endswith('.lock')}
    resulting_set = {filepath.name for filepath in profile_access_manager._get_tracking_files('.lock')}
    assert reference_set == resulting_set

    for filepath in filepath_list:
        filepath.unlink()


def test_check_methods(profile_access_manager, monkeypatch):
    """Test the `is_active` and `is_locked` methods.

    The underlying `_get_tracking_files` is tested elsewhere, so here it is mocked. For the
    tested methods, we just need to check that they evaluate to the right value when files
    are returned by `_get_tracking_files`, and when they are not.
    """

    def mockfun_return_path(*args, **kwargs):
        """Mock of _raise_if_locked."""
        return [Path('file.txt')]

    monkeypatch.setattr(profile_access_manager, '_get_tracking_files', mockfun_return_path)
    assert profile_access_manager.is_active()
    assert profile_access_manager.is_locked()

    def mockfun_return_empty(*args, **kwargs):
        """Mock of _raise_if_locked."""
        return []

    monkeypatch.setattr(profile_access_manager, '_get_tracking_files', mockfun_return_empty)
    assert not profile_access_manager.is_active()
    assert not profile_access_manager.is_locked()


def test_raise_methods(profile_access_manager, monkeypatch):
    """Test the `_raise_if_active` and `_raise_if_locked` methods.

    The underlying `_get_tracking_files` is tested elsewhere, so here it is mocked so that it
    always provides a single result of a temporary file with arbitrary content. For the tested
    methods, we just need to check that all the relevant information is passed and shown on the
    error message.
    """
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


def test_clear_locks(profile_access_manager):
    """Tests the `test_clear_locks` method.

    For this it creates an artificial lock file and uses the `is_locked` method
    (already tested elsewhere) to check if the profile is recognized as being
    locked in the different steps.
    """
    records_dir = profile_access_manager._dirpath_records
    lockfile = records_dir / '1234567890.lock'

    assert not profile_access_manager.is_locked()
    lockfile.touch()
    assert profile_access_manager.is_locked()
    profile_access_manager.clear_locks()
    assert not profile_access_manager.is_locked()


def test_clear_stale_pid_files(profile_access_manager):
    """Tests the `_clear_stale_pid_files` method."""
    records_dir = profile_access_manager._dirpath_records
    fake_filename = '1234567890.pid'
    fake_file = records_dir / fake_filename
    fake_file.touch()

    assert fake_filename in listdir(records_dir)
    profile_access_manager._clear_stale_pid_files()
    assert fake_filename not in listdir(records_dir)


###########################################################################
# SEMI INTEGRATION TESTS
#
# This second section contains more complex tests that go through more
# than one method to test the cohesion of the whole class when working
# with actual processes. It is therefore also dependant on the call to
# the class in:
#
#    >   aiida.manage.manager::Manager.get_profile_storage()
#
# Moreover, they also require the use of a separate construct to keep
# track of processes accessing aiida profiles with ease (MockProcess).
#
# This is separated from the more simple unit tests for each method.
#
###########################################################################


class MockProcess:
    """Object that can start/stop an aiida process.

    After starting an aiida process, we need to check that the profile was loaded
    successfully. We do so by having a line in the script that creates a check file.
    We can then wait for this file to be created before returning control to the caller.
    """

    def __init__(self, profile):
        self._process = None
        self._profile = profile

    def _write_codefile(self, temppath_codefile, temppath_checkfile, runtime_secs=60):
        """Auxiliary function to write the code for the process."""
        with temppath_codefile.open('w', encoding='utf-8') as fileobj:
            fileobj.write('import time\n')
            fileobj.write('from pathlib import Path\n')
            fileobj.write(f'logger_file = Path("{temppath_checkfile.resolve()}")\n')
            fileobj.write('logger_file.touch()\n')
            fileobj.write(f'time.sleep({runtime_secs})\n')

    def _wait_for_checkfile(self, temppath_checkfile):
        """Auxiliary function that waits for the checkfile to be written."""
        import time

        check_count = 0
        max_check_count = 400

        while check_count < max_check_count and not temppath_checkfile.exists():
            time.sleep(0.1)
            check_count += 1

        if check_count == max_check_count:
            raise RuntimeError('Process loading was too slow!')

    def start(self, should_raise=False, runtime_secs=60):
        """Starts a new process."""
        if self._process is not None:
            self.stop()

        temppath_codefile = Path('temp_file.py')
        temppath_checkfile = Path('temp_file.log')

        try:
            self._write_codefile(temppath_codefile, temppath_checkfile, runtime_secs)

            self._process = Popen(['verdi', '-p', self._profile.name, 'run', 'temp_file.py'], stderr=PIPE)

            if should_raise:
                error = self._process.communicate()
                return_vals = (self._process.pid, error)

            else:
                self._wait_for_checkfile(temppath_checkfile)
                return_vals = self._process.pid

        finally:
            temppath_codefile.unlink(missing_ok=True)
            temppath_checkfile.unlink(missing_ok=True)

        return return_vals

    def stop(self):
        """Kills the current process."""
        if self._process is not None:
            self._process.stderr.close()
            self._process.kill()
            self._process.wait()
        self._process = None


def test_access_control(profile_access_manager):
    """Tests the request_access method indirectly.

    This test is performed in an integral way because the underlying methods used
    have all been tested elsewhere, and it is more relevant to indirectly verify
    that this method works in real life scenarios, rather than checking the specifics
    of its internal logical structure.
    """
    accessing_process = MockProcess(profile_access_manager.profile)
    accessing_pid = accessing_process.start()
    assert profile_access_manager.is_active()
    accessing_process.stop()

    process_file = str(accessing_pid) + '.pid'
    tracking_files = [filepath.name for filepath in profile_access_manager._get_tracking_files('.pid')]
    assert process_file in tracking_files


@pytest.mark.parametrize('text_pattern', ['is being locked', 'was locked while'])
def test_request_access_errors(profile_access_manager, monkeypatch, text_pattern):
    """Tests the `request_access` method errors when blocked.

    This test requires the use of the MockProcess class because part of what we are
    checking is that the error shows the process ID that is trying to access the
    profile (without relying on the test instance). The feature being tested is
    intrinsically related to the live process instance that is stored as a property
    of the `ProfileAccessManager` class.
    """
    accessing_process = MockProcess(profile_access_manager.profile)
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


def test_lock(profile_access_manager, monkeypatch):
    """Tests the locking mechanism.

    This test is performed in an integral way because the underlying methods used
    have all been tested elsewhere, and it is more relevant to indirectly verify
    that this method works in real life scenarios, rather than checking the specifics
    of its internal logical structure.
    """
    locking_proc = MockProcess(profile_access_manager.profile)
    locking_pid = locking_proc.start()
    monkeypatch.setattr(profile_access_manager, 'process', psutil.Process(locking_pid))

    # It will not lock if there is a process accessing.
    access_proc = MockProcess(profile_access_manager.profile)
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
    def mock_raise_if_1(error_message):
        """Mock function for the `raise_if` methods."""

    monkeypatch.setattr(profile_access_manager, '_raise_if_active', mock_raise_if_1)

    with profile_access_manager.lock():
        assert profile_access_manager.is_locked()
        access_proc = MockProcess(profile_access_manager.profile)
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
