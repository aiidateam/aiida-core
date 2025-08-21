###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define commonly used data structures."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import TYPE_CHECKING

from .extendeddicts import DefaultFieldsAttributeDict

__all__ = ('CalcInfo', 'CalcJobState', 'CodeInfo', 'CodeRunMode', 'StashMode', 'UnstashTargetMode')


class StashMode(Enum):
    """Mode to use when stashing files from the working directory of a completed calculation job for safekeeping."""

    COPY = 'copy'
    COMPRESS_TAR = 'tar'
    COMPRESS_TARBZ2 = 'tar.bz2'
    COMPRESS_TARGZ = 'tar.gz'
    COMPRESS_TARXZ = 'tar.xz'
    SUBMIT_CUSTOM_CODE = 'submit_custom_code'


class UnstashTargetMode(Enum):
    """Mode to use when unstashing files."""

    OriginalPlace = 'OriginalPlace'
    NewRemoteData = 'NewRemoteData'


class CalcJobState(Enum):
    """The sub state of a CalcJobNode while its Process is in an active state (i.e. Running or Waiting)."""

    UPLOADING = 'uploading'
    SUBMITTING = 'submitting'
    WITHSCHEDULER = 'withscheduler'
    STASHING = 'stashing'
    UNSTASHING = 'unstashing'
    RETRIEVING = 'retrieving'
    PARSING = 'parsing'


class FileCopyOperation(IntEnum):
    """Enum to represent the copy operations that are used when creating the working directory of a ``CalcJob``.

    There are three different sources of files that are copied to the working directory on the remote computer where a
    calculation job is executed:

        * Local: files written to the temporary sandbox folder by the engine based on the ``local_copy_list`` defined
          by the plugin in the ``prepare_for_submission`` method.
        * Remote: files written directly to the remote working directory by the engine base on the ``remote_copy_list``
          defined by the plugin in the ``prepare_for_submission`` method.
        * Sandbox: files written to a temporary sandbox folder on the local file system written by the ``CalcJob``
          plugin, first in the ``prepare_for_submission`` method, followed by the ``presubmit`` of the base class.

    Historically, these operations were performed in the order of sandbox, local and remote. For certain use cases,
    however, this was deemed non-ideal, for example because files from the remote would override files written by the
    plugin itself in the sandbox. The ``CalcInfo.file_copy_operation_order`` attribute can be used to specify a list
    of this enum to indicate the desired order for file copy operations.
    """

    LOCAL = 0
    REMOTE = 1
    SANDBOX = 2


class CalcInfo(DefaultFieldsAttributeDict):
    """This object will store the data returned by the calculation plugin and to be
    passed to the ExecManager.

    In the following descriptions all paths have to be considered relative

    * retrieve_list: a list of strings or tuples that indicate files that are to be retrieved from the remote after the
        calculation has finished and stored in the ``retrieved_folder`` output node of type ``FolderData``. If the entry
        in the list is just a string, it is assumed to be the filepath on the remote and it will be copied to the base
        directory of the retrieved folder, where the name corresponds to the basename of the remote relative path. This
        means that any remote folder hierarchy is ignored entirely.

        Remote folder hierarchy can be (partially) maintained by using a tuple instead, with the following format

            (source, target, depth)

        The ``source`` and ``target`` elements are relative filepaths in the remote and retrieved folder. The contents
        of ``source`` (whether it is a file or folder) are copied in its entirety to the ``target`` subdirectory in the
        retrieved folder. If no subdirectory should be created, ``'.'`` should be specified for ``target``.

        The ``source`` filepaths support glob patterns ``*`` in case the exact name of the files that are to be
        retrieved are not know a priori.

        The ``depth`` element can be used to control what level of nesting of the source folder hierarchy should be
        maintained. If ``depth`` equals ``0`` or ``1`` (they are equivalent), only the basename of the ``source``
        filepath is kept. For each additional level, another subdirectory of the remote hierarchy is kept. For example:

            ('path/sub/file.txt', '.', 2)

        will retrieve the ``file.txt`` and store it under the path:

            sub/file.txt

    * retrieve_temporary_list: a list of strings or tuples that indicate files that will be retrieved
        and stored temporarily in a FolderData, that will be available only during the parsing call.
        The format of the list is the same as that of 'retrieve_list'

    * local_copy_list: a list of tuples with format ('node_uuid', 'filename', relativedestpath')
    * remote_copy_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * remote_symlink_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * provenance_exclude_list: a sequence of relative paths of files in the sandbox folder of a `CalcJob` instance that
        should not be stored permanantly in the repository folder of the corresponding `CalcJobNode` that will be
        created, but should only be copied to the remote working directory on the target computer. This is useful for
        input files that should be copied to the working directory but should not be copied as well to the repository
        either, for example, because they contain proprietary information or because they are big and their content is
        already indirectly present in the repository through one of the data nodes passed as input to the calculation.
    * codes_info: a list of dictionaries used to pass the info of the execution of a code
    * codes_run_mode: the mode of execution in which the codes will be run (`CodeRunMode.SERIAL` by default,
        but can also be `CodeRunMode.PARALLEL`)
    * skip_submit: a flag that, when set to True, orders the engine to skip the submit/update steps (so no code will
        run, it will only upload the files and then retrieve/parse).
    * file_copy_operation_order: Order in which input files are copied to the working directory. Should be a list of
      :class:`aiida.common.datastructures.FileCopyOperation` instances.
    """

    _default_fields = (
        'job_environment',
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
        'local_copy_list',
        'remote_copy_list',
        'remote_symlink_list',
        'provenance_exclude_list',
        'codes_info',
        'codes_run_mode',
        'skip_submit',
        'file_copy_operation_order',
    )

    if TYPE_CHECKING:
        job_environment: None | dict[str, str]
        email: None | str
        email_on_started: bool
        email_on_terminated: bool
        uuid: None | str
        prepend_text: None | str
        append_text: None | str
        num_machines: None | int
        num_mpiprocs_per_machine: None | int
        priority: None | int
        max_wallclock_seconds: None | int
        max_memory_kb: None | int
        rerunnable: bool
        retrieve_list: None | list[str | tuple[str, str, str]]
        retrieve_temporary_list: None | list[str | tuple[str, str, str]]
        local_copy_list: None | list[tuple[str, str, str]]
        remote_copy_list: None | list[tuple[str, str, str]]
        remote_symlink_list: None | list[tuple[str, str, str]]
        provenance_exclude_list: None | list[str]
        codes_info: None | list[CodeInfo]
        codes_run_mode: None | CodeRunMode
        skip_submit: None | bool
        file_copy_operation_order: None | list[FileCopyOperation]


class CodeInfo(DefaultFieldsAttributeDict):
    """This attribute-dictionary contains the information needed to execute a code.
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
        'code_uuid',
    )

    if TYPE_CHECKING:
        cmdline_params: None | list[str]
        stdin_name: None | str
        stdout_name: None | str
        stderr_name: None | str
        join_files: None | bool
        withmpi: None | bool
        code_uuid: None | str


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
