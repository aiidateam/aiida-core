"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""
from aiida.common.datastructures import calc_states

class Parser(object):
    """
    Base class for a parser object.
    
    Receives a Calculation object. This should be in the PARSING state. 
    Raises ValueError otherwise 
    Looks for the attached parser_opts or input_settings nodes attached to the calculation.
    Get the child Folderdata, parse it and store the parsed data.
    """

    _possible_after_parsing = [calc_states.FINISHED,calc_states.PARSINGFAILED,
                               calc_states.UNDETERMINED,calc_states.FAILED]

    _linkname_outparams = 'output_parameters'

    def __init__(self,calc):
        """
        Init
        """
        self._calc = calc
        
        
    def parse_from_data(self,data):
        """
        Receives in input a datanode.
        To be implemented.
        Will be used by the user for eventual re-parsing of out-data,
        for example with another or updated version of the parser
        """
        raise NotImplementedError
            
    def parse_from_calc(self):
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
    

    def _is_res_unlocked(self):
        """
        verify if the calculation has been parsed yet or not
        """
        is_unlocked = False
        if self._calc.get_state() in self._possible_after_parsing:
            is_unlocked = True
        return is_unlocked


    def get_results(self,key_name):
        """
        Access the parameters of the output.
        The following method will should work for a generic parser,
        provided it has to query only one ParameterData object.
        """
        from aiida.orm.data.parameter import ParameterData
        
        calc_state = self._calc.get_state()
        
        # I decide not to give warnings if the calculation is FAILED,
        # this method just passes the result, if found
        
        if not self._is_res_unlocked(): # calculation status < PARSING
            from aiida.common.exceptions import InvalidOperation
            raise InvalidOperation("Calculation is in state {}: "
                                   "doesn't have results yet".format(calc_state))
        
        out_parameters = self._calc.get_outputs(type=ParameterData,also_labels=True)
        out_parameterdata = [ i[1] for i in out_parameters if i[0]==self.get_linkname_outparams() ]
        
        if not out_parameterdata:
            from aiida.common.exceptions import NotExistent
            raise NotExistent("No output ParameterData found")
        
        if len(out_parameterdata) > 1:
            from aiida.common.exceptions import UniquenessError
            raise UniquenessError("Output ParameterData should be found once, "
                                  "found it instead {} times"
                                  .format(len(out_parameterdata)) )
        
        out_parameterdata = out_parameterdata[0]
        
        try:
            value = out_parameterdata.get_attr(key_name)
        except KeyError:
            from aiida.common.exceptions import ContentNotExistent
            raise ContentNotExistent("Key energy not found in results")
        
        #TODO: eventually, here insert further operations
        # (ex: key_name = energy_float_rydberg could return only the last element of a list,
        # and convert in the right units)
        
        return value

