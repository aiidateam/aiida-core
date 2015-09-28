# -*- coding: utf-8 -*-
"""
This module defines the main data structures used by the Calculation.
"""
from aiida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Riccardo Sabatini"


class CalcState(Enumerate):
    pass


_sorted_datastates = (
    'NOTFOUND',  # not found in the DB
    'NEW',  # just created
    'TOSUBMIT',  # used by the executionmanager to submit new calculations scheduled to be submitted
    'SUBMITTING',  # being submitted to cluster
    'WITHSCHEDULER',  # on the scheduler (on any unfinished status:
    # QUEUED, QUEUED_HELD, SUSPENDED, RUNNING)
    'COMPUTED',  # Calculation finished on scheduler, not yet retrieved
    # (both DONE and FAILED)
    'RETRIEVING',  # while retrieving data
    'PARSING',  # while parsing data
    'UNDETERMINED',
    'FINISHED',  # Final state of the calculation: data retrieved and eventually parsed
    'SUBMISSIONFAILED',  # error occurred during submission phase
    'RETRIEVALFAILED',  # error occurred during retrieval phase
    'PARSINGFAILED',  # error occurred during parsing phase due to a problem in the parse
    'FAILED',  # The parser recognized the calculation as failed
    'IMPORTED',  # The calculation was imported from another DB
)

# The order of states is not random: is the order of precedence.
# However, this is never used at the moment in the code.
calc_states = CalcState(_sorted_datastates)


def sort_states(list_states):
    """
    Given a list of state names, return a sorted list of states (the first
    is the most recent) sorted according to their logical appearance in
    the DB (i.e., NEW before of SUBMITTING before of FINISHED).
    
    .. note:: The order of the internal variable _sorted_datastates is
      used.

    :param list_states: a list (or tuple) of state strings.
    
    :return: a sorted list of the given data states.

    :raise ValueError: if any of the given states is not a valid state.
    """
    datastates_order_dict = {state: idx for idx, state in enumerate(
        _sorted_datastates)}

    try:
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
    
    # TODO:
    * dynresources_info
    
    :todo: probably some of the fields below are not used anymore inside
      calcinfo, but are rather directly set from calculation attributes to
      the JobInfo to be passed to the ExecManager
      (see, for instance, 'queue_name').
    """
    _default_fields = (
        'job_environment',  # TODO UNDERSTAND THIS!
        'email',
        'email_on_started',
        'email_on_terminated',
        'uuid',
        'prepend_text',
        'append_text',
#        'cmdline_params',  # as a list of strings
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
        #                     ['remotepath','localpath',depth]  ]
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


code_run_modes = CodeRunmode(('PARALLEL', 
                              'SERIAL'))


class CodeInfo(DefaultFieldsAttributeDict):
    _default_fields = ('cmdline_params',  # as a list of strings
                       'stdin_name',
                       'stdout_name',
                       'stderr_name',
                       'join_files',
                       'withmpi',
                       'code_pk'
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
#class DynResourcesInfo(AttributeDict):
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

