###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the ProfileAccessManager that tracks process access to the profile."""

import contextlib
import os
import shutil
import typing
from pathlib import Path

import psutil

from aiida.common.exceptions import LockedProfileError, LockingProfileError
from aiida.common.lang import type_check
from aiida.manage.configuration import Profile
from aiida.manage.configuration.settings import AiiDAConfigPathResolver


@typing.final
class ProfileAccessManager:
    """Class to manage access to a profile.

    Any process that wants to request access for a given profile, should first call:

        ProfileAccessManager(profile).request_access()

    If this returns normally, the profile can be used safely. It will raise if it is locked, in which case the profile
    should not be used. If a process wants to request exclusive access to the profile, it should use ``lock``:

        with ProfileAccessManager(profile).lock():
            pass

    If the profile is already locked or is currently in use, an exception is raised.

    Access and locks of the profile will be recorded in a directory with files with a ``.pid`` and ``.lock`` extension,
    respectively. In principle then, at any one time, there can either be a number of pid files, or just a single lock
    file. If there is a mixture or there are more than one lock files, we are in an inconsistent state.
    """

    def __init__(self, profile: Profile):
        """Class that manages access and locks to the given profile.

        :param profile: the profile whose access to manage.
        """
        _ = type_check(profile, Profile)
        self.profile = profile
        self.process = psutil.Process(os.getpid())
        self._dirpath_records = AiiDAConfigPathResolver().access_control_dir / profile.name
        self._dirpath_records.mkdir(exist_ok=True)

    def request_access(self) -> None:
        """Request access to the profile.

        If the profile is locked, a ``LockedProfileError`` is raised. Otherwise a PID file is created for this process
        and the function returns ``None``. The PID file contains the command of the process.

        :raises ~aiida.common.exceptions.LockedProfileError: if the profile is locked.
        """
        error_message = (
            f'process {self.process.pid} cannot access profile `{self.profile.name}` ' f'because it is being locked.'
        )
        self._raise_if_locked(error_message)

        filepath_pid = self._dirpath_records / f'{self.process.pid}.pid'
        filepath_tmp = self._dirpath_records / f'{self.process.pid}.tmp'

        try:
            # Write the content to a temporary file and then move it into place with an atomic operation.
            # This prevents the situation where another process requests a lock while this file is being
            # written: if that was to happen, when the locking process is checking for outdated records
            # it will read the incomplete command, won't be able to correctly compare it with its running
            # process, and will conclude the record is old and clean it up.
            filepath_tmp.write_text(str(self.process.cmdline()))
            shutil.move(filepath_tmp, filepath_pid)

            # Check again in case a lock was created in the time between the first check and creating the
            # access record file.
            error_message = (
                f'profile `{self.profile.name}` was locked while process ' f'{self.process.pid} was requesting access.'
            )
            self._raise_if_locked(error_message)

        except Exception as exc:
            filepath_tmp.unlink(missing_ok=True)
            filepath_pid.unlink(missing_ok=True)
            raise exc

    @contextlib.contextmanager
    def lock(self):
        """Request a lock on the profile for exclusive access.

        This context manager should be used if exclusive access to the profile is required. Access will be granted if
        the profile is currently not in use, nor locked by another process. During the context, the profile will be
        locked, which will be lifted automatically as soon as the context exits.

        :raises ~aiida.common.exceptions.LockingProfileError: if there are currently active processes using the profile.
        :raises ~aiida.common.exceptions.LockedProfileError: if there currently already is a lock on the profile.
        """
        error_message = (
            f'process {self.process.pid} cannot lock profile `{self.profile.name}` ' f'because it is already locked.'
        )
        self._raise_if_locked(error_message)

        self._clear_stale_pid_files()

        error_message = (
            f'process {self.process.pid} cannot lock profile `{self.profile.name}` ' f'because it is being accessed.'
        )
        self._raise_if_active(error_message)

        filepath = self._dirpath_records / f'{self.process.pid}.lock'
        filepath.touch()

        try:
            # Check if no other lock files were created in the meantime, which is possible if another
            # process was trying to obtain a lock at almost the same time.
            # By re-checking after creating the lock file we can ensure that racing conditions will never
            # cause two different processes to both think that they acquired the lock. It is still possible
            # that two processes that are trying to lock will think that the other acquired the lock first
            # and then both will fail, but this is a much safer case.
            error_message = (
                f'while process {self.process.pid} attempted to lock profile `{self.profile.name}`, '
                f'other process blocked it first.'
            )
            self._raise_if_locked(error_message)

            error_message = (
                f'while process {self.process.pid} attempted to lock profile `{self.profile.name}`, '
                f'other process started using it.'
            )
            self._raise_if_active(error_message)

            yield

        finally:
            filepath.unlink(missing_ok=True)

    def is_locked(self) -> bool:
        """Return whether the profile is locked."""
        return self._get_tracking_files('.lock', exclude_self=False) != []

    def is_active(self) -> bool:
        """Return whether the profile is currently in use."""
        return self._get_tracking_files('.pid', exclude_self=False) != []

    def clear_locks(self) -> None:
        """Clear all locks on this profile.

        .. warning:: This should only be used if the profile is currently still incorrectly locked because the lock was
            not automatically released after the ``lock`` contextmanager exited its scope.
        """
        for lock_file in self._get_tracking_files('.lock'):
            lock_file.unlink()

    def _clear_stale_pid_files(self) -> None:
        """Clear any stale PID files."""
        for path in self._get_tracking_files('.pid'):
            try:
                process = psutil.Process(int(path.stem))
            except psutil.NoSuchProcess:
                # The process no longer exists, so simply remove the PID file.
                path.unlink()
            else:
                # If the process exists but its command is different from what is written in the PID file,
                # we assume the latter is stale and remove it.
                if path.read_text() != str(process.cmdline()):
                    path.unlink()

    def _get_tracking_files(self, ext_string: str, exclude_self: bool = False) -> typing.List[Path]:
        """Return a list of all files that track the accessing and locking of the profile.

        :param ext_string:
            To get the files that track locking use `.lock`, to get the files that track access use `.pid`.

        :param exclude_self:
            If true removes from the returned list any tracking to the current process.
        """
        path_iterator = self._dirpath_records.glob('*' + ext_string)

        if exclude_self:
            filepath_self = self._dirpath_records / (str(self.process.pid) + ext_string)
            list_of_files = [filepath for filepath in path_iterator if filepath != filepath_self]

        else:
            list_of_files = list(path_iterator)

        return list_of_files

    def _raise_if_locked(self, message_start):
        """Raise a ``LockedProfileError`` if the profile is locked.

        :param message_start: Text to use as the start of the exception message.
        :raises ~aiida.common.exceptions.LockedProfileError: if the profile is locked.
        """
        list_of_files = self._get_tracking_files('.lock', exclude_self=True)

        if len(list_of_files) > 0:
            error_msg = message_start + '\nThe following processes are blocking the profile:\n'
            error_msg += '\n'.join(f' - pid {path.stem}' for path in list_of_files)
            raise LockedProfileError(error_msg)

    def _raise_if_active(self, message_start):
        """Raise a ``LockingProfileError`` if the profile is being accessed.

        :param message_start: Text to use as the start of the exception message.
        :raises ~aiida.common.exceptions.LockingProfileError: if the profile is active.
        """
        list_of_files = self._get_tracking_files('.pid', exclude_self=True)

        if len(list_of_files) > 0:
            error_msg = message_start + '\nThe following processes are accessing the profile:\n'
            error_msg += '\n'.join(f' - pid {path.stem} (`{path.read_text()}`)' for path in list_of_files)
            raise LockingProfileError(error_msg)
