from aida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

class CalcState(Enumerate):
    pass

calcStates = CalcState((
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


from aida.common.extendeddicts import DefaultFieldsAttributeDict

class CalcInfo(DefaultFieldsAttributeDict):
    """
    This object will store the data returned by the code plugin and to be
    passed to the ExecManager 
    
    # TODO:
    * dynresources_info
    """
    _default_fields = (
        'jobEnvironment', # TODO UNDERSTAND THIS!
        'email',
        'emailOnStarted',
        'emailOnTerminated',
        'uuid',
        'prependText', 
        'appendText',  
        'cmdlineParams',  # as a list of strings
        'stdinName',
        'stdoutName',
        'stderrName',
        'joinFiles',
        'queueName', 
        'numNodes',
        'numCpusPerNode',
        'priority',
        'maxWallclockSeconds',
        'maxMemoryKb',
        'rerunnable',
        'retrieve_list', # a list of files or patterns to retrieve
        'local_file_list', # a list of length-two tuples with (localabspath, relativedestpath)
        'remote_file_list', # a list of length-three tuples with (remotemachinename, remoteabspath, relativedestpath)
        )



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

