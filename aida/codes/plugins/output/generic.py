"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""

# TODO : write this generic class

def parse_calculation_output( out_file , *args, **kwargs ):
    """
    Parses the output of a generic code for which there is no specific plugin
    
    Args: out_file (str) : path to the standard output file
    """
    raise NotImplementedError
