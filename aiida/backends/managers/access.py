# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the manager that tracks the access and locking of the profile."""
import contextlib
import json
import os
import time

import psutil

from aiida.common import exceptions


class ProcessData():
    """Class to store and manage the data of processes"""

    def __init__(self, pid=None, filepath=None):
        """Initialization process for the ProcessData object.

        :param pid:
            pid of a process to be loaded from the ones running in the environment (if it is not
            provided it will just load the data of the process that is currently running).

        :param filepath:
            filepath of the process to be loaded from a file (if it is not provided it will just
            load the data of the process that is currently running).
        """

        if filepath is not None:
            self._read_from_file(filepath)
            return

        if pid is None:
            pid = os.getpid()

        self._pid = pid
        process_obj = psutil.Process(pid)
        process_cmd = process_obj.cmdline()
        process_ctm = time.localtime(process_obj.create_time())
        process_ctm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(process_obj.create_time()))

        self._data = {'cmd': process_cmd, 'ctime': process_ctm}

    def write_to_file(self, filepath):
        """Writes the info of the process to a file (filepath)"""
        json_data = {'pid': self._pid, 'data': self._data}
        with open(filepath, 'w') as json_file:  # pylint: disable=unspecified-encoding
            json.dump(json_data, json_file)

    def _read_from_file(self, filepath):
        """Reads the info of the process from a file (filepath)"""
        with open(filepath, 'r') as json_file:  # pylint: disable=unspecified-encoding
            json_data = json.load(json_file)
        self._pid = json_data['pid']
        self._data = json_data['data']

    def __eq__(self, other):
        """Define equivalency"""
        if isinstance(other, self.__class__):
            return (self.pid == other.pid) and (self.cmd == other.cmd)
        return False

    @property
    def pid(self):
        """pid"""
        return self._pid

    @property
    def cmd(self):
        """cmd"""
        return self._data['cmd']


class AccessManager():
    """Class to manage and keep track of processes accessing and locking the profile."""

    def __init__(self, profile=None):
        """Initialization process for the access manager object.

        :param profile:
            profile to manage the access of (loaded profile by default).
        """
        from aiida.manage.configuration.settings import ACCESS_CONTROL_DIR
        from aiida.manage.manager import get_manager

        if profile is None:
            profile = get_manager().get_profile()

        self._temp_prefix = 'request_'
        self._profile = profile
        profile_access_path = ACCESS_CONTROL_DIR / profile.name
        profile_access_path.mkdir(exist_ok=True)

        self._path_to_tracked = profile_access_path / 'tracked'
        self._path_to_tracked.mkdir(exist_ok=True)

        self._path_to_locking = profile_access_path / 'locking'
        self._path_to_locking.mkdir(exist_ok=True)

    def get_processes_recorded_in(self, basepath, ignore_self=True):
        """Returns all processes tracked in a given path

        :param basepath:
            base path in which the records are being stored.

        :param ignore_self:
            flag to avoid returning the process that is requesting the information in the output
            (enabled by default).
        """
        process_datadicts = {}

        for filename in os.listdir(basepath):
            if not filename.startswith(self._temp_prefix):
                filepath = basepath / filename
                process_data = ProcessData(filepath=filepath)
                process_datadicts[process_data.pid] = process_data

        if ignore_self and os.getpid() in process_datadicts:
            process_datadicts.pop(os.getpid())

        return process_datadicts

    def get_locking_processes(self, ignore_self=True):
        """Returns all processes attempting to lock the profile

        :param ignore_self:
            flag to avoid returning the process that is requesting the information in the output
            (enabled by default).
        """
        return self.get_processes_recorded_in(self._path_to_locking, ignore_self=ignore_self)

    def get_tracked_processes(self, ignore_self=True):
        """Returns all processes recorded when trying to access the profile

        :param ignore_self:
            flag to avoid returning the process that is requesting the information in the output
            (enabled by default).
        """
        return self.get_processes_recorded_in(self._path_to_tracked, ignore_self=ignore_self)

    def acquire_lock(self):
        """Creates a locking file for the running process"""
        tracked_processes = self.get_tracked_processes()
        filtered_processes = self.separate_processes(tracked_processes)
        self.delete_process_records(filtered_processes['terminated'])

        if len(filtered_processes['remaining']) > 0:
            raise exceptions.LockingProfileError('can`t lock profile')

        process_data = ProcessData()
        process_idn = process_data.pid
        filepath_temp = self._path_to_locking / f'request_{process_idn}.pid'
        filepath_final = self._path_to_locking / f'{process_idn}.pid'
        process_data.write_to_file(filepath_temp)
        os.rename(filepath_temp, filepath_final)

        locking_processes = self.get_locking_processes()
        if len(locking_processes) > 0:
            os.remove(filepath_final)
            raise exceptions.LockedProfileError('can`t lock profile')

        tracked_processes = self.get_tracked_processes()
        if len(tracked_processes) > 0:
            os.remove(filepath_final)
            raise exceptions.LockedProfileError('can`t lock profile')

    def release_lock(self):
        """Releases the locking file of the running process"""
        process_data = ProcessData()
        process_idn = process_data.pid
        filepath = self._path_to_locking / f'{process_idn}.pid'
        with contextlib.suppress(FileNotFoundError):
            os.remove(filepath)

    @contextlib.contextmanager
    def profile_locking_context(self):
        """Context for working with a locked profile"""
        try:
            self.acquire_lock()
            yield
        finally:
            self.release_lock()

    def record_process_access(self, verify_lock=True):
        """Records the access of a process

        :param verify_lock:
            flag to check if there is a lock on the profile that would prevent access (True by default,
            otherwise it will ignore the lock and provide access anyway). The check is performed both
            at the start and the end of the process to check for any posible racing conditions.
        """
        if verify_lock:
            locking_processes = self.get_locking_processes()
            if len(locking_processes) > 0:
                raise exceptions.LockingProfileError('can`t access profile')

        process_data = ProcessData()
        process_idn = process_data.pid
        filepath_temp = self._path_to_tracked / f'request_{process_idn}.pid'
        filepath_final = self._path_to_tracked / f'{process_idn}.pid'
        process_data.write_to_file(filepath_temp)
        os.rename(filepath_temp, filepath_final)

        if verify_lock:
            locking_processes = self.get_locking_processes()
            if len(locking_processes) > 0:
                os.remove(filepath_final)
                raise exceptions.LockingProfileError('can`t access profile')

    def delete_process_records(self, process_datadicts, ignore_missing=True):
        """Deletes a list of tracked processes

        :param process_datadicts:
            a dict that has the pid of the process as keys and the ProcessData as values.

        :param ignore_missing:
            flag to ignore the case where a process id that was requested to have its record deleted
            doesn't have a record to delete (True by default, else it will raise).
        """
        for pid in process_datadicts.keys():
            filepath = self._path_to_tracked / f'{pid}.pid'
            try:
                os.remove(filepath)
            except OSError as exc:
                if not ignore_missing:
                    raise exc

    def separate_processes(self, process_datadicts):  # pylint: disable=no-self-use
        """Takes a list of processes and returns only the ones that might still be running.

        :param process_datadicts:
            a dict that has the pid of the process as keys and the ProcessData as values.
        """
        live_processes = {}

        for live_process in psutil.process_iter():
            try:
                pid = live_process.pid
                live_processes[pid] = ProcessData(pid=pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        terminated_processes = {}
        remaining_processes = {}

        for pid, process_data in process_datadicts.items():
            if (pid in live_processes) and (process_data == live_processes[pid]):
                remaining_processes[pid] = process_data
            else:
                terminated_processes[pid] = process_data

        return {'terminated': terminated_processes, 'remaining': remaining_processes}
