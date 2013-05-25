from aida.common.extendeddicts import (
#    FixedFieldsAttributeDict,
    DefaultFieldsAttributeDict, Enumerate)

class JobState(Enumerate):
    pass

job_states = JobState((
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
        'num_machines',
        'num_cpus_per_machine',
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
 

class MachineInfo(DefaultFieldsAttributeDict):
    """
    Similarly to what is defined in the DRMAA v.2 as SlotInfo; this identifies
    each machine (also called 'node' on some schedulers)
    on which a job is running, and how many CPUs are being used.

    * name: name of the machine
    * num_cpus: number of cores used by the job on this machine
    """
    _default_fields = (
        'name',
        'num_cpus',
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

class JobInfo(DefaultFieldsAttributeDict):
    """
    Contains properties for a job in the queue.
    Most of the fields are taken from DRMAA v.2,

    Note that upon request, default fields may be undefined. This
    is an expected behavior and the application must cope with this
    case. An example for instance is the exit_status for jobs that have
    not finished yet; or features not supported by the given scheduler.

    Fields:
       job_id: the job ID on the scheduler
       title: the job title, as known by the scheduler
       exit_status: the exit status of the job as reported by the operating
           system on the execution host
       terminating_signal: the UNIX signal that was responsible for the end of
           the job.
       annotation: human-readable description of the reason for the job
           being in the current state or substate.
       job_state: the job state (one of those defined in aida.scheduler.states)
       job_substate: a string with the implementation-specific sub-state
       allocated_machines: a list of machines used for the current job.
       job_owner: the job owner as reported by the scheduler
       num_cpus: the number of requested cores (this more or less is what
           is called 'slots' in DRMAAv2)
       num_machines: the number of machines (i.e., nodes), required by the job.
           If allocated_machines is not None, this number must be equal to
           len(allocated_machines). Otherwise, for schedulers not supporting
           the retrieval of the full list of allocated machines, this 
           attribute can be used to know at least the number of machines
       queue_name: The name of the queue in which the job was queued or started
       wallclock_time_seconds: the accumulated wallclock time, in seconds
       requested_wallclock_time_seconds: the requested wallclock time, in seconds
       cpu_time: the accumulated cpu time, in seconds
       submission_time: the absolute time at which the job was submitted,
           of type datetime.datetime
       dispatch_time: the absolute time at which the job first entered the
           'started' state, of type datetime.datetime
       finish_time: the absolute time at which the job first entered the 
           'finished' state, of type datetime.datetime
    """
    _default_fields = (
        'job_id',
        'title',
        'exit_status',
        'terminating_signal',
        'annotation',
        'job_state',
        'job_substate',
        'allocated_machines',
        'job_owner',
        'num_cpus',
        'num_machines',
        'queue_name',
        'wallclock_time_seconds',
        'requested_wallclock_time_seconds',
        'cpu_time',
        'submission_time',
        'dispatch_time',
        'finish_time',
        )
