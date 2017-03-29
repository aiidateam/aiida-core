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
This module defines the main data structures used by the Calculation.
"""
from aiida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

class CalcState(Enumerate):
    pass

_sorted_datastates = (
    'NEW',  # just created
    'TOSUBMIT',  # used by the executionmanager to submit new calculations scheduled to be submitted
    'SUBMITTING',  # being submitted to cluster
    'WITHSCHEDULER',  # on the scheduler (on any unfinished status:
    # QUEUED, QUEUED_HELD, SUSPENDED, RUNNING)
    'COMPUTED',  # Calculation finished on scheduler, not yet retrieved
    # (both DONE and FAILED)
    'RETRIEVING',  # while retrieving data
    'PARSING',  # while parsing data
    'FINISHED',  # Final state of the calculation: data retrieved and eventually parsed
    'SUBMISSIONFAILED',  # error occurred during submission phase
    'RETRIEVALFAILED',  # error occurred during retrieval phase
    'PARSINGFAILED',  # error occurred during parsing phase due to a problem in the parse
    'FAILED',  # The parser recognized the calculation as failed
    'IMPORTED',  # The calculation was imported from another DB
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
    passed to the ExecManager
    """
    # Note: some of the variables might have never been used in AiiDA
    #       one might want to clean all this stuff in a future revision
    # Note: probably some of the fields below are not used anymore inside
    #       calcinfo, but are rather directly set from calculation attributes to
    #       the JobInfo to be passed to the ExecManager
    #       (see, for instance, 'queue_name').

    _default_fields = (
        'job_environment',  # TODO UNDERSTAND THIS!
        'email',
        'email_on_started',
        'email_on_terminated',
        'uuid',
        'prepend_text',
        'append_text',
#        'cmdline_params',  # as a list of strings. These 5 variables are now in CalcInfo
#        'stdin_name',
#        'stdout_name',
#        'stderr_name',
#        'join_files',
        # 'queue_name', This is not used in CalcInfo, it is automatically set from
        # calculation attributes to JobInfo
        'num_machines',
        'num_mpiprocs_per_machine',
        'priority',
        'max_wallclock_seconds',
        'max_memory_kb',
        'rerunnable',
        'retrieve_list',  # a list of files or patterns to retrieve, with two
        # possible formats: [ 'remotepath',  # just the name of the file to retrieve. Will be put in '.' of the repositorym with name os.path.split(item)[1]
        # ['remotepath','localpath',depth]  ]
        # second format will copy the remotepath file/folder to localpath.
        # if remotepath is a file/folder, localpath will be its local name
        # if remotepath has file patterns, localpath should only be '.'
        # depth is an integer to decide the localname: will be os.path.join(localpath, filename )
        # where filename takes remotepath.split() and joins the last #depth elements
        # use the second option if you are using file patterns (*,[0-9],...)
        # ALL PATHS ARE RELATIVE!
        'local_copy_list',  # a list of length-two tuples with (localabspath, relativedestpath)
        'remote_copy_list',  # a list of length-three tuples with (remotemachinename, remoteabspath, relativedestpath)
        'remote_symlink_list',
        # a list of length-three tuples with (remotemachinename, remoteabspath, relativedestpath)
        'retrieve_singlefile_list',  # a list of files, that will be retrieved
        # from cluster and saved in SinglefileData nodes
        # in the following format:
        # ["linkname_from calc to singlefile","subclass of singlefile","filename"]
        # filename remote = filename local
        'codes_info',  # a list of dictionaries used to pass the info of the execution of a code.
        'codes_run_mode', # a string used to specify the order in which multi codes can be executed
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
code_run_modes = CodeRunmode(('PARALLEL',
                              'SERIAL'))


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
