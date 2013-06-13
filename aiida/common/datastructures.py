"""
This module defines the main data structures used by the Calculation.
"""
from aiida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

class CalcState(Enumerate):
    pass

calc_states = CalcState((
        'UNDETERMINED',
        'NEW', # just created
        'SUBMITTING', # being submitted to cluster
        'WITHSCHEDULER', # on the scheduler (on any unfinished status:
                         # QUEUED, QUEUED_HELD, SUSPENDED, RUNNING)
        'FINISHED',   # Calculation finished on scheduler, not yet retrieved
                      # (both DONE and FAILED)
        'RETRIEVING', # while retrieving data
        'PARSING', # while parsing data
        'RETRIEVED',  # data retrieved, no more need to connect to scheduler
        'SUBMISSIONFAILED', # error occurred during submission phase
        'RETRIEVALFAILED', # error occurred during retrieval phase
        ))


class CalcInfo(DefaultFieldsAttributeDict):
    """
    This object will store the data returned by the code plugin and to be
    passed to the ExecManager 
    
    # TODO:
    * dynresources_info
    """
    _default_fields = (
        'job_environment', # TODO UNDERSTAND THIS!
        'email',
        'email_on_started',
        'email_on_terminated',
        'uuid',
        'prepend_text', 
        'append_text',  
        'cmdline_params',  # as a list of strings
        'stdin_name',
        'stdout_name',
        'stderr_name',
        'join_files',
        'queue_name', 
        'num_machines',
        'num_cpus_per_machine',
        'priority',
        'max_wallclock_seconds',
        'max_memory_kb',
        'rerunnable',
        'retrieve_list', # a list of files or patterns to retrieve
        'local_file_list', # a list of length-two tuples with (localabspath, relativedestpath)
        'remote_file_list', # a list of length-three tuples with (remotemachinename, remoteabspath, relativedestpath)
        )

class WorkflowState(Enumerate):
    pass

wf_states = WorkflowState((
        'INITIATED',
        'RUNNING',
        'FINISHED',
        ))

wf_start_call = "start"
wf_exit_call = "exit"

#TODO Improve/implement this!
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

