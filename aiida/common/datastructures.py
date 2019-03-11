# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define commonly used data structures."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum, IntEnum

from .extendeddicts import DefaultFieldsAttributeDict

__all__ = ('CalcJobState', 'CalcInfo', 'CodeInfo', 'CodeRunMode')


class CalcJobState(Enum):
    """The sub state of a CalcJobNode while its Process is in an active state (i.e. Running or Waiting)."""

    UPLOADING = 'uploading'
    SUBMITTING = 'submitting'
    WITHSCHEDULER = 'withscheduler'
    RETRIEVING = 'retrieving'
    PARSING = 'parsing'


class CalcInfo(DefaultFieldsAttributeDict):
    """
    This object will store the data returned by the calculation plugin and to be
    passed to the ExecManager.

    In the following descriptions all paths have to be considered relative

    * retrieve_list: a list of strings or tuples that indicate files that are to be retrieved from the remote
        after the calculation has finished and stored in the repository in a FolderData.
        If the entry in the list is just a string, it is assumed to be the filepath on the remote and it will
        be copied to '.' of the repository with name os.path.split(item)[1]
        If the entry is a tuple it is expected to have the following format

            ('remotepath', 'localpath', depth)

        If the 'remotepath' is a file or folder, it will be copied in the repository to 'localpath'.
        However, if the 'remotepath' contains file patterns with wildcards, the 'localpath' should be set to '.'
        and the depth parameter should be an integer that decides the localname. The 'remotepath' will be split on
        file separators and the local filename will be determined by joining the N last elements, where N is
        given by the depth variable.

        Example: ('some/remote/path/files/pattern*[0-9].xml', '.', 2)

        Will result in all files that match the pattern to be copied to the local repository with path

            'files/pattern*[0-9].xml'

    * retrieve_temporary_list: a list of strings or tuples that indicate files that will be retrieved
        and stored temporarily in a FolderData, that will be available only during the parsing call.
        The format of the list is the same as that of 'retrieve_list'

    * retrieve_singlefile_list: a list of tuples with format
        ('linkname_from calc to singlefile', 'subclass of singlefile', 'filename')
        Each tuple represents a file that will be retrieved from cluster and saved in SinglefileData nodes

    * local_copy_list: a list of tuples with format ('node_uuid', 'filename', relativedestpath')
    * remote_copy_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * remote_symlink_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * codes_info: a list of dictionaries used to pass the info of the execution of a code
    * codes_run_mode: a string used to specify the order in which multi codes can be executed
    """

    _default_fields = (
        'job_environment',  # TODO UNDERSTAND THIS!
        'email',
        'email_on_started',
        'email_on_terminated',
        'uuid',
        'prepend_text',
        'append_text',
        'num_machines',
        'num_mpiprocs_per_machine',
        'priority',
        'max_wallclock_seconds',
        'max_memory_kb',
        'rerunnable',
        'retrieve_list',
        'retrieve_temporary_list',
        'retrieve_singlefile_list',
        'local_copy_list',
        'remote_copy_list',
        'remote_symlink_list',
        'codes_info',
        'codes_run_mode'
    )


class CodeInfo(DefaultFieldsAttributeDict):
    """
    This attribute-dictionary contains the information needed to execute a code.
    Possible attributes are:

    * ``cmdline_params``: a list of strings, containing parameters to be written on
      the command line right after the call to the code, as for example::

        code.x cmdline_params[0] cmdline_params[1] ... < stdin > stdout

    * ``stdin_name``: (optional) the name of the standard input file. Note, it is
      only possible to use the stdin with the syntax::

        code.x < stdin_name

      If no stdin_name is specified, the string "< stdin_name" will not be
      passed to the code.
      Note: it is not possible to substitute/remove the '<' if stdin_name is specified;
      if that is needed, avoid stdin_name and use instead the cmdline_params to
      specify a suitable syntax.
    * ``stdout_name``: (optional) the name of the standard output file. Note, it is
      only possible to pass output to stdout_name with the syntax::

        code.x ... > stdout_name

      If no stdout_name is specified, the string "> stdout_name" will not be
      passed to the code.
      Note: it is not possible to substitute/remove the '>' if stdout_name is specified;
      if that is needed, avoid stdout_name and use instead the cmdline_params to
      specify a suitable syntax.
    * ``stderr_name``: (optional) a string, the name of the error file of the code.
    * ``join_files``: (optional) if True, redirects the error to the output file.
      If join_files=True, the code will be called as::

        code.x ... > stdout_name 2>&1

      otherwise, if join_files=False and stderr is passed::

        code.x ... > stdout_name 2> stderr_name

    * ``withmpi``: if True, executes the code with mpirun (or another MPI installed
      on the remote computer)
    * ``code_uuid``: the uuid of the code associated to the CodeInfo
    """
    _default_fields = (
        'cmdline_params',  # as a list of strings
        'stdin_name',
        'stdout_name',
        'stderr_name',
        'join_files',
        'withmpi',
        'code_uuid'
    )


class CodeRunMode(IntEnum):
    """Enum to indicate the way the codes of a calculation should be run.

    For PARALLEL, the codes for a given calculation will be run in parallel by running them in the background::

        code1.x &
        code2.x &

    For the SERIAL option, codes will be executed sequentially by running for example the following::

        code1.x
        code2.x
    """

    SERIAL = 0
    PARALLEL = 1


class LazyStore(object):
    """
    A container that provides a mapping to objects based on a key, if the object is not
    found in the container when it is retrieved it will created using a provided factory
    method
    """

    def __init__(self):
        self._store = {}

    def get(self, key, factory):
        """
        Get a value in the store based on the key, if it doesn't exist it will be created
        using the factory method and returned

        :param key: the key of the object to get
        :param factory: the factory used to create the object if necessary
        :return: the object
        """
        try:
            return self._store[key]
        except KeyError:
            obj = factory()
            self._store[key] = obj
            return obj

    def pop(self, key):
        """
        Pop an object from the store based on the given key

        :param key: the object key
        :return: the object that was popped
        """
        return self._store.pop(key)
