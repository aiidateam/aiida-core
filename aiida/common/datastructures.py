# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module defines the main data structures used by Calculations.
"""
from aiida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

class CalcState(Enumerate):
    pass

_sorted_datastates = (
    'NEW',  # just created
    'TOSUBMIT',  # used by the executionmanager to submit new calculations scheduled to be submitted
    'SUBMITTING',  # being submitted to cluster
    'WITHSCHEDULER',  # on the scheduler (on any unfinished status: QUEUED, QUEUED_HELD, SUSPENDED, RUNNING)
    'COMPUTED',  # calculation finished on scheduler, not yet retrieved (both DONE and FAILED)
    'RETRIEVING',  # while retrieving data
    'PARSING',  # while parsing data
    'FINISHED',  # final state of the calculation: data retrieved and eventually parsed
    'SUBMISSIONFAILED',  # error occurred during submission phase
    'RETRIEVALFAILED',  # error occurred during retrieval phase
    'PARSINGFAILED',  # error occurred during parsing phase due to a problem in the parse
    'FAILED',  # the parser recognized the calculation as failed
    'IMPORTED',  # the calculation was imported from another DB
)

# The order of states is not random: is the order of precedence.
# This is used to verify that calculations always procede in the correct order.
# calc_states, instead, has a random order
calc_states = CalcState(_sorted_datastates)


def sort_states(list_states, use_key=False):
    """
    Given a list of state names, return a sorted list of states (the first
    is the most recent) sorted according to their logical appearance in
    the DB (i.e., NEW before of SUBMITTING before of FINISHED).

    .. note:: The order of the internal variable _sorted_datastates is
      used.

    :param list_states: a list (or tuple) of state strings.

    :param use_key: if True, expects that each element is not
        just a string, but a pair (someobject, string).
        Only string is used to sort (should be the state string),
        and only someobject is returned in the final list.

    :return: a sorted list of the given data states.

    :raise ValueError: if any of the given states is not a valid state.
    """
    datastates_order_dict = {state: idx for idx, state in enumerate(
        _sorted_datastates)}

    try:
        if use_key:
            list_to_sort = [(datastates_order_dict[st[1]], st[0])
                            for st in list_states]
        else:
            list_to_sort = [(datastates_order_dict[st], st)
                            for st in list_states]

    except KeyError as e:
        raise ValueError("At least one of the provided states is not "
                         "valid ({})".format(e.message))

    # In-place sort
    list_to_sort.sort()

    return [_[1] for _ in list_to_sort[::-1]]


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

    * local_copy_list: a list of tuples with format ('localabspath', 'relativedestpath')
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


class CodeRunmode(Enumerate):
    pass

# these are the possible ways to execute more than one code in the same scheduling job
# if parallel, the codes will be executed as something like:
#   code1.x &
#   code2.x &
#   wait
# if serial, it will be:
#   code1.x
#   code2.x
code_run_modes = CodeRunmode(('PARALLEL', 'SERIAL'))


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
    _default_fields = ('cmdline_params',  # as a list of strings
                       'stdin_name',
                       'stdout_name',
                       'stderr_name',
                       'join_files',
                       'withmpi',
                       'code_uuid'
                       )


class WorkflowState(Enumerate):
    pass


wf_states = WorkflowState((
    'CREATED',
    'INITIALIZED',
    'RUNNING',
    'FINISHED',
    'SLEEP',
    'ERROR'
))


class WorkflowDataType(Enumerate):
    pass


wf_data_types = WorkflowDataType((
    'PARAMETER',
    'RESULT',
    'ATTRIBUTE',
))


class WorkflowDataValueType(Enumerate):
    pass


wf_data_value_types = WorkflowDataValueType((
    'NONE',
    'JSON',
    'AIIDA',
))

wf_start_call = "start"
wf_exit_call = "exit"
wf_default_call = "none"

# TODO Improve/implement this!
# class DynResourcesInfo(AttributeDict):
#    """
#    This object will contain a list of 'dynamical' resources to be
#    passed from the code plugin to the ExecManager, containing
#    things like
#    * resources in the permanent repository, that will be simply
#      linked locally (but copied remotely on the remote computer)
#      to avoid a waste of permanent repository space
#    * remote resources to be directly copied over only remotely
#    """
#    pass
