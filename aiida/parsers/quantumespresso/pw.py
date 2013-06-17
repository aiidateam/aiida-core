from aiida.orm import Calculation
from aiida.orm.calculation.quantumespresso.pw import PwCalculation
from aiida.common.datastructures import calc_states
from aiida.parsers.quantumespresso.raw_parser_pw import *
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.common.folders import SandboxFolder
from aiida.orm import DataFactory
from aiida.parsers.parser import Parser
import copy

class PwParser(Parser):
    """
    This class is the implementation of the Parser class for PWscf.
    """

    def __init__(self,calculation,force=False):
        """
        Initialize the instance of PwParser

        Args:
            calculation
                the calculation object to be attached to
            force
                (optional boolean) if set to True
        """
        # First I need to check if I receive a valid input
        if not isinstance(calculation,PwCalculation):
            raise ValueError("calc must be a PwCalculation")

        state = calculation.get_state()

        if not force:
            if state is not 'PARSING':
                raise QEOutputParsingError("Calculation not in PARSING state")

        setattr(self,'calc',calculation)
        
    def parse_local(self):
        """
        Parses the datafolder, stores results.
        Main functionality of the class.
        """
        import os
        import glob
        
        # retrieve the whole list of input links
        calc_input_parameterdata = self.calc.get_inputs(type=ParameterData,also_labels=True)
        # then look for parameterdata only
        input_param_name = self.calc.get_linkname_parameters()
        # TODO count how many occurences of the same input params happen
        params = [i[1] for i in calc_input_parameterdata if i[0]==input_param_name]
        if len(params) != 1:
            raise QEOutputParsingError("Too many input_params are found: {}".format(params))
        calc_input = params[0]

        # look for eventual flags of the parser
        parser_opts_query = [i[1] for i in calc_input_parameterdata if i[0]=='parser_opts']
        # TODO : there should be a function returning the name of parser_opts
        if len(parser_opts_query)>1:
            raise QEOutputParsingError("Too many parser_opts attached are found: {}"
                                       .format(parser_opts_query))
        if parser_opts_query:
            parser_opts = parser_opts_query[0]
            # TODO this feature could be a set of flags to pass to the raw_parser
            # in order to moderate its verbosity (like storing bands in teh database
            raise NotImplementedError("The parser_options feature is not yet implemented")
        else:
            parser_opts = []

        # load the input dictionary
        # TODO: pass this input_dict to the parser. It might need it.            
        input_dict = calc_input.get_dict()
        
        # load all outputs
        #!        print self.calc.get_outputs(also_labels=True)
        calc_outputs = self.calc.get_outputs(type=FolderData,also_labels=True)
        # look for retrieved files only
        retrieved_files = [i[1] for i in calc_outputs if i[0]=='retrieved']
        # TODO : linkname 'retrieved' should be more given py PwCalculation
        if len(retrieved_files)!=1:
            raise QEOutputParsingError("Output folder should be found once, found it instead {} times"
                                       .format(len(retrieved_files)) )
        # select the folder object
        out_folder = calc_outputs[0][1]

        # check what is inside the folder
        list_of_files = out_folder.get_path_list()
        # at least the stdout should exist
        if not self.calc.OUTPUT_FILE_NAME in list_of_files:
            raise QEOutputParsingError()
        # if there is something more, I note it down, so to call the raw parser
        # with the right options
        # look for xml
        has_xml = False
        if self.calc.OUTPUT_XML_FILE_NAME in list_of_files:
            has_xml = True
        # look for bands
        has_bands = False
        if glob.glob( os.path.join(out_folder.get_abs_path('.'),'K[0-9][0-9][0-9][0-9][0-9]')):
            # Note: I hard-code that the format of the kpoints subfolder is Kxxxxx
            # I don't know what happens to QE in the case of 99999> points
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
        self.calc.add_link_to(output_params, label=self.get_linkname_outparams() )
        # TODO check name of the link input_parameters to be consistent with this
        # TODO : 'output_parameters' is the name of the link that the parser decides.
        # How does the Calculation know it?
        
    @classmethod
    def get_linkname_outparams(self):
        """
        The name of the link used for the output parameters
        """
        return 'output_parameters'
