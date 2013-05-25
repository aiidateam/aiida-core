from aida.common.extendeddicts import (
#    FixedFieldsAttributeDict,
    DefaultFieldsAttributeDict, Enumerate)

class JobState(Enumerate):
    pass

jobStates = JobState((
        'UNDETERMINED',
        'QUEUED',
        'QUEUED_HELD',
        'RUNNING',
        'SUSPENDED',
        'DONE',
        ))
# for the moment, I don't define FAILED (I put everything in DONE)
#        'FAILED',


class JobTemplate(DefaultFieldsAttributeDict):
    """
    A template for submitting jobs. This contains all required information
    to create the job header.
    
    Fields:
    * argv: a list of strings with the command line arguments
          of the program to run. The first one is the executable name. For
          MPI runs, this will probably be mpirun or a similar program; 
          this has to be chosen at a upper level.
    * max_memory_kb: The maximum amount of memory the job is allowed
         to allocate ON EACH NODE, in kilobyte
    * max_wallclock_seconds: The maximum wall clock time that all processes of 
         a job are allowed to exist, in seconds

    * TODO: refine this list and choose what we want to support.
    * TODO: validation? also call the validate function in the proper place then.
    """
    _default_fields = (
        'submit_as_hold',
        'rerunnable',
        'job_environment',
        'working_directory', 
        'email',
        'email_on_started',
        'email_on_terminated',
        'job_name',
        'sched_output_path',    
        'sched_error_path',     
        'sched_join_files',     
        'queue_name',
        'num_nodes',
        'num_cpus_per_node',
        'priority',
        'max_memory_kb', 
        'max_wallclock_seconds',

        'prepend_text',
        'append_text',
        'argv',
        'stdin_name',
        'stdout_name',
        'stderr_name',
        'join_files',
        )
 

class NodeInfo(DefaultFieldsAttributeDict):
    """
    Similarly to what is defined in the DRMAA v.2 as SlotInfo; this identifies
    each node on which a job is running, and how many CPUs are being
    used.

    * nodeName: name of the node
    * numCores: number of cores used by the job on this node
    """
    _default_fields = (
        'nodeName',
        'numCores',
        )

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
       allocatedNodes: a list of nodes used for the current job.
       submissionMachine: Name of the submission host for this job.
       jobOwner: the job owner as reported by the scheduler
       numCores: the number of requested cores (this more or less is what
           is called 'slots' in DRMAAv2)
       num_nodes: the number of nodes, required by the job.
           If allocatedNodes is not None, this number must be equal to
           len(allocatedNodes). Otherwise, for schedulers not supporting
           the retrieval of the full list of allocated nodes, this 
           attribute can be used to know at least the number of nodes
       queue_name: The name of the queue in which the job was queued or started
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
        'allocatedNodes',
        'submissionMachine',
        'jobOwner',
        'numCores',
        'num_nodes',
        'queue_name',
        'wallclockTime',
        'requestedWallclockTime',
        'cpuTime',
        'submissionTime',
        'dispatchTime',
        'finishTime',
        )
