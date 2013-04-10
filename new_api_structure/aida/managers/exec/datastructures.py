from aida.common.extendeddicts import DefaultFieldsAttributeDict

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
class JobInfo(ExtendedDict):
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