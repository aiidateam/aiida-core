"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""

# TODO : write this generic class

class Parser(object):
    """
    Base class for a parser object.
    
    Receives a Calculation object. 
    Looks for the attached parser_opts or input_settings nodes attached to the calculation.
    Get the child Folderdata, parse it and store the parsed data.
    """

    def __init__(self,calculation):
        """
        Makes the checks that everything exists and is consistent
        """
        raise NotImplementedError

    def parse_out_folder(self,folder_obj):
        """
        Returns:
            parameter data object
        """
        raise NotImplementedError

    def store_data(self):
        """
        Stores data object in the db
        """
        raise NotImplementedError

    def attach_to_calc(self):
        """
        set links of output data object
        """
        raise NotImplementedError

