from aiida.orm import Calculation
from aiida.orm.calculation.quantumespresso.pw import PwCalculation
from aiida.common.datastructures import calc_states
from aiida.parsers.quantumespresso.raw_parser_pw import *
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.common.folders import SandboxFolder
from aiida.orm import DataFactory

class PwscfParser(Parser):
    """
    This class is the implementation of the Parser class for PWscf.
    """
    def __init__(self,calc):
        # First I need to check if I receive a valid input
        if not isinstance(calc,PwCalculation):
            raise ValueError("calc must be a PwCalculation")

        state = calc.get_state
        
        if state not in calc_states:
            raise QEOutputParsingError("Calculation state was not recognized")
        
        if state is not 'PARSING':
            raise QEOutputParsingError("Calculation not in PARSING state")

    def parse_local(self):
        """
        Parses the datafolder, stores results.
        Main functionality of the class.
        """
        import os
        import glob
        
        calc_input_name = self.calc.get_linkname_parameters()
        #calc_inputs = self.calc.query( DataFactory('parameter'), _with_link_to_calc_of_the_same_name_that_I_just_got_above ) # TODO: fix this
        calc_input_parameterdata = self.calc.get_inputs() # retrieve the whole list of input links
        
        # TODO count how many occurences of the same input params happen
        # and check that they occur only once
        if parser_opts occur_more_than_once:
            raise QEOutputParsingError("Too many parser_opts attached are found: {}".format(the_num))
        if input_params occur_not_once:
            raise QEOutputParsingError("Too many input_params are found: {}".format(the_num))
        
        for this_obj in calc_input_parameterdata:
            if this_obj is parser_opts: # TODO fix it
                parser_opts = copy.deepcopy(this_obj)
            if this_obj is input_params: # TODO fix it
                calc_input = copy.deepcopy(this_obj)

        # TODO: pass this input_dict to the parser. It might need it.            
        input_dict = calc_input.get_dict()
        
        if parser_opts:
            # TODO this feature could be a set of flags to pass to the raw_parser
            # in order to moderate its verbosity (like storing bands in teh database
            raise NotImplementedError("The parser_options feature is not yet implemented")
        parser_opts = []
        
        calc_outputs = self.calc.get_outputs()
        # TODO : look for outputs of class SandboxFolder() with link to calc called "retrieved"
        if len(calc_outputs)!=1:
            raise QEOutputParsingError("Output folder should be found once, found it instead {} times".format(len(calc_outputs)) )
        out_folder = calc_outputs[0]
        
        # check what is inside the folder
        list_of_files = out_folder.get_content_list()
        if not self.calc.OUTPUT_FILE_NAME in list_of_files:
            raise QEOutputParsingError()
        if self.calc.OUTPUT_XML_FILE_NAME in list_of_files:
            has_xml = True
        # If I find k points, I try by default to parse the bands
        if glob.glob( os.path.join(out_folder.get_abs_path('.'),'K[0-9][0-9][0-9][0-9][0-9]')):
            # Note: I assume that the format of the kpoints subfolder is Kxxxxx
            has_bands = True
            # TODO: maybe it can be more general than bands only?
        out_file = os.path.join( out_folder.get_abs_path('.'), self.calc.OUTPUT_FILE_NAME )
        xml_file = os.path.join( out_folder.get_abs_path('.'), self.calc.OUTPUT_XML_FILE_NAME )
        dir_with_bands = out_folder.get_abs_path('.')
        
        # call the raw parsing function
        parsing_args = [out_file,input_dict,parser_opts]
        if has_xml:
            parsing_args.append(xml_file)
        if has_bands:
            parsing_args.append(dir_with_bands)
        out_dict = parse_raw_output(*parsing_args)
        
        # convert the dictionary into an AiiDA object
        output_params = ParameterData(out_dict)
        
        # save it into db
        output_params.store()
        self.calc.add_link_from(output_params, label='output_parameters') 
        # TODO check name of the link
        #TODO in this way, we should call the input one as 'input_parameters'

        
