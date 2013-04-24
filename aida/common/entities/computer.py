from aida.common.extendeddict import ExtendedDict

class Computer(ExtendedDict):
    """
    This class contains all the information of a computational resource.
    
    Attributes (some compulsory):
      * scheduler type
      * specific configurations
        - mpirun command
        - num cores per node
        - max num cores
        - allocate full node = True or False
        - ... (further limits per user etc.)
        - transport type (ssh, local, ... - see Transport class)
        - FQDN of the cluster
    """
    pass
