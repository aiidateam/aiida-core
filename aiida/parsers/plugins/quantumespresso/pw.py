from aiida.orm.calculation.quantumespresso.pw import PwCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_pw import *
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser#, ParserParamManager
from aiida.parsers.plugins.quantumespresso import convert_qe2aiida_structure
from aiida.common.datastructures import calc_states
from aiida.orm.data.structure import StructureData
from aiida.common.exceptions import UniquenessError,ValidationError

#TODO: I don't like the generic class always returning a name for the link to the output structure

class PwParser(Parser):
    """
    This class is the implementation of the Parser class for PWscf.
    """

    _outstruc_name = 'output_structure'

    def __init__(self,calculation):
        """
        Initialize the instance of PwParser
        """
        # check for valid input
        if not isinstance(calculation,PwCalculation):
            raise QEOutputParsingError("Input must calc must be a PwCalculation")
        
        # save calc for later use
        self._calc = calculation
        
        # here some logic to decide whether the parser has an output structure or not.
        # set it to None by default
        self._set_linkname_outstructure(None)
        if calculation.get_state in self._possible_after_parsing:
            # can have been already parsed: check for outstructure
            # find existing outputs of kind structuredata
            out_struc = calculation.get_outputs(type=StructureData,also_labels=True)
            # get only those with the linkame of this parser plugin
            parser_out_struc = [ i for i in out_struc if i[0] == self._outstruc_name ]
            if not parser_out_struc: # case with no struc found
                self._set_linkname_outstructure(None)
            elif len(parser_out_struc)>1: # case with too many struc found
                raise UniquenessError("Multiple output StructureData found ({})"
                                      "with same linkname".format(len(parser_out_struc)))
            else: # one structure is found, with the right name
                self._set_linkname_outstructure(self._outstruc_name)
        
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
        Main functionality of the class.
        """
        from aiida.common.exceptions import InvalidOperation
        import os
        import glob
        
        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )
        
        # retrieve the whole list of input links
        calc_input_parameterdata = self._calc.get_inputs(type=ParameterData,
                                                         also_labels=True)
        # then look for parameterdata only
        input_param_name = self._calc.get_linkname_parameters()
        params = [i[1] for i in calc_input_parameterdata if i[0]==input_param_name]
        if len(params) != 1:
            raise UniquenessError("Found {} input_params instead of one"
                                  .format(params))
        calc_input = params[0]

        # look for eventual flags of the parser
        parser_opts_query = [i[1] for i in calc_input_parameterdata if i[0]=='parser_opts']
        # TODO: there should be a function returning the name of parser_opts
        if len(parser_opts_query)>1:
            raise UniquenessError("Too many parser_opts attached are found: {}"
                                  .format(parser_opts_query))
        if parser_opts_query:
            parser_opts = parser_opts_query[0]
            # TODO: this feature could be a set of flags to pass to the raw_parser
            # in order to moderate its verbosity (like storing bands in teh database
            raise NotImplementedError("The parser_options feature is not yet implemented")
        else:
            parser_opts = []

        # load the input dictionary
        # TODO: pass this input_dict to the parser. It might need it.            
        input_dict = calc_input.get_dict()
        
        # load all outputs
        calc_outputs = self._calc.get_outputs(type=FolderData,also_labels=True)
        # look for retrieved files only
        retrieved_files = [i[1] for i in calc_outputs if i[0]==self._calc.get_linkname_retrieved()]
        if len(retrieved_files)!=1:
            raise QEOutputParsingError("Output folder should be found once, "
                                       "found it instead {} times"
                                       .format(len(retrieved_files)) )
        # select the folder object
        out_folder = calc_outputs[0][1]

        # check what is inside the folder
        list_of_files = out_folder.get_path_list()
        # at least the stdout should exist
        if not self._calc.OUTPUT_FILE_NAME in list_of_files:
            raise QEOutputParsingError("Standard output not found")
        # if there is something more, I note it down, so to call the raw parser
        # with the right options
        # look for xml
        has_xml = False
        if self._calc.DATAFILE_XML_BASENAME in list_of_files:
            has_xml = True
        # look for bands
        has_bands = False
        if glob.glob( os.path.join(out_folder.get_abs_path('.'),
                                   'K[0-9][0-9][0-9][0-9][0-9]')):
            # Note: assuming format of kpoints subfolder is Kxxxxx
            # I don't know what happens to QE in the case of 99999> points
            has_bands = True
            # TODO: maybe it can be more general than bands only?
        out_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc.OUTPUT_FILE_NAME )
        xml_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc.DATAFILE_XML_BASENAME )
        dir_with_bands = out_folder.get_abs_path('.')
        
        # call the raw parsing function
        parsing_args = [out_file,input_dict,parser_opts]
        if has_xml:
            parsing_args.append(xml_file)
        if has_bands:
            parsing_args.append(dir_with_bands)
        out_dict,successful = parse_raw_output(*parsing_args)
        
        # convert the dictionary into an AiiDA object
        output_params = ParameterData(out_dict)
        
        # save it into db
        output_params.store()
        self._calc._add_link_to(output_params, label=self.get_linkname_outparams() )
        
        in_struc = self._calc.get_inputs_dict()['structure']
        type_calc = input_dict['CONTROL']['calculation']
        if type_calc=='relax' or type_calc=='vc-relax':
            self._set_linkname_outstructure(self._outstruc_name)
            struc = convert_qe2aiida_structure(out_dict,input_structure=in_struc)
            struc.store()
            self._calc._add_link_to(struc, label=self.get_linkname_outstructure() )
        
        return successful

    def get_linkname_outstructure(self):
        """
        Returns the name of the link to the output_structure (None if not present)
        """
        return self.linkname_outstructure
    
    def _set_linkname_outstructure(self,linkname):
        """
        Set the name of the link to the output_structure
        """
        setattr(self,'linkname_outstructure',linkname)
        
    def get_energy_ev(self,all_values=False):
        """
        Returns the float value of energy.

        Args:
            all_values: if true returns a list of energies, else only a float
                (default=False)

        Raises:
            FailedError: calculation is failed
            InvalidOperation: calculation has not been parsed yet
            NotExistent: no output found
            UniquenessError: more than one output found
            ContentNotExistent: no key energy found in the results
        """
        from aiida.common.exceptions import InvalidOperation, FailedError
        from aiida.common.exceptions import NotExistent,UniquenessError,ContentNotExistent
        
        calc_state = self._calc.get_state()
        
        if 'FAILED' in calc_state:  # SUBMISSIONFAILED','RETRIEVALFAILED','PARSINGFAILED','FAILED',
            raise FailedError('Calculation is in state {}'
                              .format(calc_state))
        
        if calc_state != calc_states.FINISHED:
            raise InvalidOperation("Calculation is in state {}: "
                                   "doesn't have results yet".format(calc_state))
        
        out_parameters = self._calc.get_outputs(type=ParameterData,also_labels=True)
        out_parameterdata = [ i[1] for i in out_parameters if i[0]==self.get_linkname_outparams() ]
        
        if not out_parameterdata:
            raise NotExistent("No output ParameterData found")
        
        if len(out_parameterdata) > 1:
            raise UniquenessError("Output ParameterData should be found once, "
                              "found it instead {} times"
                              .format(len(out_parameterdata)) )
            
        out_parameterdata = out_parameterdata[0]
        
        try:
            if not all_values:
                energy = out_parameterdata.get_attr('energy')[-1]
            else:
                energy = out_parameterdata.get_attr('energy')
            # NOTE: in one case I return a list, in the other a float
        except AttributeError:
            raise ContentNotExistent("Key energy not found in results")
        
        return energy
    
    
    # def get_parsed_nodes(self,also_labels=False):
    #     """
    #     returns a list of the nodes created by the parser
    #     """
    #     if not self._is_res_unlocked():
    #         from aiida.common.exceptions import InvalidOperation
    #         raise InvalidOperation("Calculation not yet parsed")
    #     else:
    #         to_return = []
            
    #         all_params = self._calc.get_outputs(type=ParameterData,also_labels=True)
    #         this_params = [ i[1] for i in all_params if i[0]==self.get_linkname_outparams() ]
    #         if this_params is not None:
    #             if also_labels:
    #                 to_return.append( (self.get_linkname_outparams(),this_params) )
    #             else:
    #                 to_return.append( this_params )
                    
    #         all_structures = self._calc.get_outputs(type=StructureData,also_labels=True)
    #         this_structure = [ i[1] for i in all_structures if i[0]==self.get_linkname_outstructure() ]
    #         if this_structure is not None:
    #             if also_labels:
    #                 to_return.append( (self.get_linkname_outstructure(),this_structure) )
    #             else:
    #                 to_return.append( (self.get_linkname_outstructure(),this_structure) )

    #         return to_return

