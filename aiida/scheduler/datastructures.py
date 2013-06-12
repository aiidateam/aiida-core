"""
This module defines the main data structures used by the scheduler.

In particular, there is the definition of possible job states (job_states),
the data structure to be filled for job submission (JobTemplate), and
the data structure that is returned when querying for jobs in the scheduler
(JobInfo).
"""
from aiida.common.extendeddicts import (
    DefaultFieldsAttributeDict, Enumerate)

class JobState(Enumerate):
    pass

# This is the list of possible job states
# Note on names: Jobs are the entities on a
#   scheduler; Calcs are the calculations in
#   the AiiDA database (whose list of possible
#   statuses is defined in aida.common.datastructures
#   with the calc_states Enumerate).
# NOTE: for the moment, I don't define FAILED
# (I put everything in DONE)
job_states = JobState((
        'UNDETERMINED',
        'QUEUED',
        'QUEUED_HELD',
        'RUNNING',
        'SUSPENDED',
        'DONE',
        ))

class JobTemplate(DefaultFieldsAttributeDict):
    """
    A template for submitting jobs. This contains all required information
    to create the job header.

    The required fields are: working_directory, job_name, num_machines,
      num_cpus_per_machine, argv.
    
    Fields:
      * submit_as_hold: if set, the job will be in a 'hold' status right
          after the submission
      * rerunnable: if the job is rerunnable (boolean)
      * job_environment: a dictionary with environment variables to set
          before the execution of the code.
      * working_directory: the working directory for this job. During
          submission, the transport will first do a 'chdir' to this directory,
          and then possibly set a scheduler parameter, if this is supported
          by the scheduler.
      * email: an email address for sending emails on job events.
      * email_on_started: if True, ask the scheduler to send an email when the
          job starts.
      * email_on_terminated: if True, ask the scheduler to send an email when
          the job ends. This should also send emails on job failure, when 
          possible.
      * job_name: the name of this job. The actual name of the job can be
          different from the one specified here, e.g. if there are unsupported
          characters, or the name is too long.
      * sched_output_path: a (relative) file name for the stdout of this job
      * sched_error_path: a (relative) file name for the stdout of this job
      * sched_join_files: if True, write both stdout and stderr on the same
          file (the one specified for stdout)
      * queue_name: the name of the scheduler queue (sometimes also called
          partition), on which the job will be submitted.
      * num_machines: how many machines (or nodes) should be used
      * num_cpus_per_machine: how many cpus or cores should be used on each
          machine (or node).
      * priority: a priority for this job. Should be in the format accepted
          by the specific scheduler.
      * max_memory_kb: The maximum amount of memory the job is allowed
         to allocate ON EACH NODE, in kilobytes
      * max_wallclock_seconds: The maximum wall clock time that all processes
          of a job are allowed to exist, in seconds
      * prepend_text: a (possibly multi-line) string to be inserted 
          in the scheduler script before the main execution line
      * argv: a list of strings with the command line arguments
          of the program to run. This is the main program to be executed.
          NOTE: The first one is the executable name.
          For MPI runs, this will probably be "mpirun" or a similar program; 
          this has to be chosen at a upper level.
      * stdin_name: the (relative) file name to be used as stdin for the 
          program specified with argv.
      * stdout_name: the (relative) file name to be used as stdout for the 
          program specified with argv.
      * stderr_name: the (relative) file name to be used as stderr for the 
          program specified with argv.
      * join_files: if True, stderr is redirected on the same file specified
          for stdout.
      * append_text: a (possibly multi-line) string to be inserted 
          in the scheduler script after the main execution line
    * TODO: validation? also call the validate function in the proper
          place then.
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

class JobInfo(DefaultFieldsAttributeDict):
    """
    Contains properties for a job in the queue.
    Most of the fields are taken from DRMAA v.2,

    Note that default fields may be undefined. This
    is an expected behavior and the application must cope with this
    case. An example for instance is the exit_status for jobs that have
    not finished yet; or features not supported by the given scheduler.

    Fields:
       * job_id: the job ID on the scheduler
       * title: the job title, as known by the scheduler
       * exit_status: the exit status of the job as reported by the operating
           system on the execution host
       * terminating_signal: the UNIX signal that was responsible for the end
           of the job.
       * annotation: human-readable description of the reason for the job
           being in the current state or substate.
       * job_state: the job state (one of those defined in
           aiida.scheduler.datastructures.job_states)
       * job_substate: a string with the implementation-specific sub-state
       * allocated_machines: a list of machines used for the current job.
           This is a list of MachineInfo objects.
       * job_owner: the job owner as reported by the scheduler
       * num_cpus: the *total* number of requested cores
       * num_machines: the number of machines (i.e., nodes), required by the
           job. If allocated_machines is not None, this number must be equal to
           len(allocated_machines). Otherwise, for schedulers not supporting
           the retrieval of the full list of allocated machines, this 
           attribute can be used to know at least the number of machines.
       * queue_name: The name of the queue in which the job is queued or
           running.
       * wallclock_time_seconds: the accumulated wallclock time, in seconds
       * requested_wallclock_time_seconds: the requested wallclock time,
           in seconds
       * cpu_time: the accumulated cpu time, in seconds
       * submission_time: the absolute time at which the job was submitted,
           of type datetime.datetime
       * dispatch_time: the absolute time at which the job first entered the
          'started' state, of type datetime.datetime
       * finish_time: the absolute time at which the job first entered the 
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
