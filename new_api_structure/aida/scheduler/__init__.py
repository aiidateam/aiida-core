from aida.common.extendeddict import ExtendedDict

class Scheduler(object):
    """
    Note: probably we want to inherit from some more reasonable class.

    Base class for all schedulers
    """
    def __init__(self, computer):
        """
        Store the computer (of type aida.common.entities.computer.Computer) 
        in a internal variable, and load the specific subclass from 
        the plugins subfolder reading the value computer.scheduler
        """
        pass

    def get_submit_script(self, calcinfo):
        """
        Return the submit script.
        calcinfo of type aida.managers.job.calcinfo.CalcInfo
        
        This must be implemented by the plugin subclass, but every
        subclass will always call this class _get_script_main_content
        method that is general.

        The plugin return something like

        #!/bin/bash -l <- this shebang line could be configurable in the future
        scheduler_dependent stuff to choose numnodes, numcores, walltime, ...
        prepend_computer
        prepend_code [from calcinfo]
        in the future: environment_variables [from calcinfo, possibly,
            and from scheduler_requirements e.g. for OpenMP? or maybe
            the openmp part is better managed in the scheduler_dependent
            part above since it will be machine-dependent]
        output of _get_script_main_content
        postpend_code
        postpend_computer
       
        
        """
        raise NotImplementedError

    def _get_script_main_content(self, calcinfo):
        """
        calcinfo of type aida.managers.job.calcinfo.CalcInfo
        
        Defined in the base class, returns a string in the format
        
        [mpirun_str % numprocs] [executable] [args] {[ < stdin ]}
        {[ < stdout ]} {[2>&1 | 2 > stderr]}
        """
        pass
    
    def get_queue_command(jobid=None):
        """
        Return a list with the qsub (or equivalent) command to run + 
        required parameters to get the most complete description possible;
        the format will be the one used by the parse_queue_output.

        Must be implemented in the plugin.

        if jobid=None, pass the string to get all jobs, otherwise restrict
        the output the the specified job.
        """
        pass

    def parse_queue_output(output_txt):
        """
        a suitable function to parse the queue output, as returned by the
        get_queue_command command.
        
        To be implemented in the plugin
        
        return a list of QueueInfo objects, one of each job, 
        each with at least its default params implemented.
        """
        pass

class QueueInfo(ExtendedDict):
    """
    Contains properties for a job in the queue.
    Contains at least:
    * jobid
    * user
    * queue
    * wall
    * status
    * numnodes
    * numcores
    * jobtitle

    The status is encoded in a well-defined, scheduler_independent set of
    statuses including (for the list, see DMRAA or Saga for instance):
    * running (should all 'finishing' statuses be here?)
    * queued (should 'held' be included in queued?)
    * finished
    * error
    * unknown (e.g. if network was not available)

    DRMAA API 1.0 - python language bindings definitions:
        UNDETERMINED='undetermined'
        QUEUED_ACTIVE='queued_active'
        SYSTEM_ON_HOLD='system_on_hold'
        USER_ON_HOLD='user_on_hold'
        USER_SYSTEM_ON_HOLD='user_system_on_hold'
        RUNNING='running' 
        SYSTEM_SUSPENDED='system_suspended'
        USER_SUSPENDED='user_suspended'
        USER_SYSTEM_SUSPENDED='user_system_suspended' DONE='done'
        FAILED='failed' 
    """
    pass
