from aida.common.extendeddict import ExtendedDict

class CalcInfo(ExtendedDict):
    """
    This object will store the data returned by the code plugin and to be
    passed to the ExecManager 
    
    Contains at least:
    * cmdline_params
    * stdin
    * stdout
    * stderr
    * preexec_commands
    * postexec_commands
    * retrieve_output_list

    """
    pass

class DynResourcesInfo(ExtendedDict):
    """
    This object will contain a list of 'dynamical' resources to be 
    passed from the code plugin to the ExecManager, containing
    things like
    * resources in the permanent repository, that will be simply
      linked locally (but copied remotely on the remote computer)
      to avoid a waste of permanent repository space
    * remote resources to be directly copied over only remotely
    """
    pass
