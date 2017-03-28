# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os

from django.db import transaction

from aiida.orm.implementation.general.code import AbstractCode
from aiida.orm.implementation import Computer
from aiida.common.exceptions import (NotExistent, MultipleObjectsError,
                                     InvalidOperation)



class Code(AbstractCode):

    @classmethod
    def get(cls, pk=None, label=None, machinename=None):
        return super(Code, cls).get(pk, label, machinename)

    @classmethod
    def get_from_string(cls, code_string):
        return super(Code, cls).get_from_string(code_string)

    @classmethod
    def list_for_plugin(cls, plugin, labels=True):
        """
        Return a list of valid code strings for a given plugin.

        :param plugin: The string of the plugin.
        :param labels: if True, return a list of code names, otherwise
          return the code PKs (integers).
        :return: a list of string, with the code names if labels is True,
          otherwise a list of integers with the code PKs.
        """
        valid_codes = list(cls.query(
            dbattributes__key="input_plugin",
            dbattributes__tval=plugin))

        if labels:
            return [c.label for c in valid_codes]
        else:
            return [c.pk for c in valid_codes]

    def set_remote_computer_exec(self, remote_computer_exec):
        """
        Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.

        Args:
            remote_computer_exec: a tuple (computer, remote_exec_path), where
              computer is a aiida.orm.Computer or an
              aiida.backends.djsite.db.models.DbComputer object, and
              remote_exec_path is the absolute path of the main executable on
              remote computer.
        """
        from aiida.backends.djsite.db.models import DbComputer
        if (not isinstance(remote_computer_exec, (list, tuple))
            or len(remote_computer_exec) != 2):
            raise ValueError("remote_computer_exec must be a list or tuple "
                             "of length 2, with machine and executable "
                             "name")

        computer, remote_exec_path = tuple(remote_computer_exec)

        if not os.path.isabs(remote_exec_path):
            raise ValueError(
                "exec_path must be an absolute path (on the remote machine)")

        remote_dbcomputer = computer
        if isinstance(remote_dbcomputer, Computer):
            remote_dbcomputer = remote_dbcomputer.dbcomputer
        if not (isinstance(remote_dbcomputer, DbComputer)):
            raise TypeError(
                "computer must be either a Computer or DbComputer object")

        self._set_remote()

        self.dbnode.dbcomputer = remote_dbcomputer
        self._set_attr('remote_exec_path', remote_exec_path)

    def _set_local(self):
        """
        Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        self._set_attr('is_local', True)
        self.dbnode.dbcomputer = None
        try:
            self._del_attr('remote_exec_path')
        except AttributeError:
            pass

    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        from aiida.backends.djsite.db.models import DbComputer
        if self.is_local():
            return True
        else:
            dbcomputer = computer
            if isinstance(dbcomputer, Computer):
                dbcomputer = dbcomputer.dbcomputer
            if not isinstance(dbcomputer, DbComputer):
                raise ValueError(
                    "computer must be either a Computer or DbComputer object")
            dbcomputer = DbComputer.get_dbcomputer(computer)
            return (dbcomputer.pk ==
                    self.get_remote_computer().dbcomputer.pk)


def delete_code(code):
    """
    Delete a code from the DB.
    Check before that there are no output nodes.

    NOTE! Not thread safe... Do not use with many users accessing the DB
    at the same time.

    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling
    computer.delete().
    """
    if not isinstance(code, Code):
        raise TypeError("code must be an instance of "
                        "aiida.orm.computer.Code")

    existing_outputs = code.get_outputs()

    if len(existing_outputs) != 0:
        raise InvalidOperation("Unable to delete the requested code because it "
                               "has {} output links".format(
            len(existing_outputs)))
    else:
        repo_folder = code._repository_folder
        with transaction.atomic():
            code.dbnode.delete()
            repo_folder.erase()
