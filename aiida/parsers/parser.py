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

    _linkname_outparams = 'output_parameters'

    def __init__(self):
        """
        Init
        """
        raise NotImplementedError

    def parse_from_data(self,data):
        """
        Receives in input a datanode.
        To be implemented.
        Will be used by the user for eventual re-parsing of out-data,
        for example with another or updated version of the parser
        """
        raise NotImplementedError
            
    def parse_from_calc(self,calc):
        """
        Parses the datafolder, stores results.
        Used by the Execmanager.
        """
        raise NotImplementedError

        
    @classmethod
    def get_linkname_outparams(self):
        """
        The name of the link used for the output parameters
        """
        return self._linkname_outparams
