"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""

# TODO : write this generic class

class Parser(object):
    """
    Base class for a parser object.
    
    Receives a Calculation object. This should be in the PARSING state. 
    Raises ValueError otherwise 
    Looks for the attached parser_opts or input_settings nodes attached to the calculation.
    Get the child Folderdata, parse it and store the parsed data.
    """

    def __init__(self,calc):
        """
        Makes the checks that everything exists and is consistent
        """
        raise NotImplementedError

    def parse_local(self):
        """
        Returns:
            parameter data object
        """
        raise NotImplementedError
