from aida.common.extendeddicts import (
    DefaultFieldsAttributeDict,
    Enumerate)


class JobState(Enumerate):
    pass

jobStates = JobState((
        'UNDETERMINED',
        'QUEUED',
        'QUEUED_HELD',
        'RUNNING',
        'SUSPENDED',
        'DONE',
        'FAILED',
        ))
    

class QueueInfo(DefaultFieldsAttributeDict):
    _default_fields = ('name',)
    
class MachineResource(DefaultFieldsAttributeDict):
    # These should be the same defined in the DB for storage.
    # At some point we may decide to create dynamically the _default_fields
    # tuple from the DB model.
    _default_fields = (
        'hostname',         # FQDN
        'workdir',          # where to store, accepts {username} field
        'scheduler_type',   # a string to pick up the correct scheduler
        'transport_type',   # a string to pick up the correct transport
        'transport_options',# a dictionary with further options to be passed to the
                            # transport
        'active',           # set to False to disable the use of this machine
        )


## MachineInfo from DRMAA (to be returned when asked for, dynamically)
#string name;
#boolean available;
#long sockets;
#long coresPerSocket;
#long threadsPerCore;
#double load;
#long physMemory;
#long virtMemory;


## To be changed/adapted/improved!!
class JobInfo(DefaultFieldsAttributeDict):
    """
    Contains properties for a job in the queue.
    Most of the fields are taken from DRMAA v.2,

    Note that upon request, default fields may be undefined. This
    is an expected behavior and the application must cope with this
    case. An example for instance is the exitStatus for jobs that have
    not finished yet; or features not supported by the given scheduler.

    Fields:
       jobId: the job ID on the scheduler
       title: the job title, as known by the scheduler
       exitStatus: the exit status of the job as reported by the operating
           system on the execution host
       terminatingSignal: the UNIX signal that was responsible for the end of
           the job.
       annotation: human-readable description of the reason for the job
           being in the current state or substate.
       jobState: the job state (one of those defined in aida.scheduler.states)
       jobSubState: a string with the implementation-specific sub-state
       allocatedMachines: a list of machines used for the current job.
       submissionMachine: Name of the submission host for this job.
       jobOwner: the job owner as reported by the scheduler
       numCores: the number of requested cores (this more or less is what
           is called 'slots' in DRMAAv2)
       numMachines: the number of machines, or nodes, required by the job.
           If allocatedMachines is not None, this number must be equal to
           len(allocatedMachines). Otherwise, for schedulers not supporting
           the retrieval of the full list of allocated machines, this 
           attribute can be used to know at least the number of machines
       queueName: The name of the queue in which the job was queued or started
       wallclockTime: the accumulated wallclock time, in seconds
       requestedWallclockTime: the requested wallclock time, in seconds
       cpuTime: the accumulated cpu time, in seconds
       submissionTime: the absolute time at which the job was submitted,
           of type datetime.datetime
       dispatchTime: the absolute time at which the job first entered the
           'started' state, of type datetime.datetime
       finishTime: the absolute time at which the job first entered the 
           'finished' state, of type datetime.datetime
    """
    _default_fields = (
        'jobId',
        'title',
        'exitStatus',
        'terminatingSignal',
        'annotation',
        'jobState',
        'jobSubState',
        'allocatedMachines',
        'submissionMachine',
        'jobOwner',
        'numCores',
        'numMachines',
        'queueName',
        'wallclockTime',
        'requestedWallclockTime',
        'cpuTime',
        'submissionTime',
        'dispatchTime',
        'finishTime',
        )
