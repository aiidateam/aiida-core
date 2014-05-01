from aiida.orm.calculation.quantumespresso.cp import CpCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_cp import *
from aiida.parsers.plugins.quantumespresso.constants import *
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser
from aiida.parsers.plugins.quantumespresso import convert_qe2aiida_structure
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import UniquenessError
from aiida.orm.data.array.trajectory import TrajectoryData

class CpParser(Parser):
    """
    This class is the implementation of the Parser class for Cp.
    """
    
    _outtraj_name = 'output_structure'
    
    def __init__(self,calculation):
        """
        Initialize the instance of CpParser
        
        :param calculation: calculation object.
        """
        # check for valid input
        if not isinstance(calculation,CpCalculation):
            raise QEOutputParsingError("Input must calc must be a CpCalculation")

        # save calc for later use
        self._calc = calculation
        
        # here some logic to decide whether parser already saved the trajectory or not
        self._set_linkname_outtrajectory(None)
        if calculation.get_state in self._possible_after_parsing:
            # can have been already parsed: check for outstructure
            # find existing outputs of kind structuredata
            out_struc = calculation.get_outputs(type=TrajectoryData,also_labels=True)
            # get only those with the linkame of this parser plugin
            parser_out_struc = [ i for i in out_struc if i[0] == self._outstruc_name ]
            if not parser_out_struc: # case with no struc found
                self._set_linkname_outtrajectory(None)
            elif len(parser_out_struc)>1: # case with too many struc found
                raise UniquenessError("Multiple output TrajectoryData found ({})"
                                      "with same linkname".format(len(parser_out_struc)))
            else: # one structure is found, with the right name
                self._set_linkname_outtrajectory(self._outtraj_name)
        
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
        
        :return successful bool: to state if the calculation has Failed or not.
        """
        from aiida.common.exceptions import InvalidOperation
        import os,copy
        
        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )
        
        # retrieve the whole list of input links
        calc_input_parameterdata = self._calc.get_inputs(type=ParameterData,
                                                         also_labels=True)
        # then look for parameterdata only
        input_param_name = self._calc.get_linkname('parameters')
        params = [i[1] for i in calc_input_parameterdata if i[0]==input_param_name]
        if len(params) != 1:
            raise UniquenessError("Found {} input_params instead of one"
                                  .format(params))
        calc_input = params[0]

        # get the input structure
        input_structure = self._calc.get_inputs(type=StructureData)[0] # I'm supposing only one input structure

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
        retrieved_files = [i[1] for i in calc_outputs 
                           if i[0]==self._calc.get_linkname_retrieved()]
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
        out_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc.OUTPUT_FILE_NAME )

        xml_file = None
        if self._calc.DATAFILE_XML_BASENAME in list_of_files:
            xml_file = os.path.join( out_folder.get_abs_path('.'), 
                                     self._calc.DATAFILE_XML_BASENAME )
        
        xml_counter_file = None
        if self._calc.FILE_XML_PRINT_COUNTER in list_of_files:
            xml_counter_file = os.path.join( out_folder.get_abs_path('.'), 
                                             self._calc.FILE_XML_PRINT_COUNTER )
        
        parsing_args = [out_file,xml_file,xml_counter_file]
        
        # call the raw parsing function
        out_dict,successful = parse_cp_raw_output(*parsing_args)
        
        # parse the trajectory. Units in Angstrom, picoseconds and eV.
        # append everthing in the temporary dictionary raw_trajectory
        expected_configs = None
        raw_trajectory=False
        import numpy # TrajectoryData also uses numpy arrays
        evp_keys = ['electronic_kinetic_energy','cell_temperature','ionic_temperature',
                    'scf_total_energy','enthalpy','enthalpy_plus_kinetic',
                    'energy_constant_motion','volume','pressure']
        pos_vel_keys = ['cells','positions','times','velocities']
        # set a default null values

        # =============== POSITIONS trajectory ============================
        try:
            with open(os.path.join( out_folder.get_abs_path('.'), 
                                    '{}.pos'.format(self._calc.PREFIX) )) as posfile:
                pos_data = [l.split() for l in posfile]   
            #POSITIONS stored in angstrom
            traj_data = parse_cp_traj_stanzas(num_elements=out_dict['number_of_atoms'], 
                                              splitlines=pos_data, 
                                              prepend_name='positions_traj',
                                              rescale=bohr_to_ang)
            # here initialize the dictionary. If the parsing of positions fails, though, I don't have anything
            # out of the CP dynamics. Therefore, the calculation status is set to FAILED.
            raw_trajectory = self._set_default_dict('cells',pos_vel_keys,evp_keys,
                                                    out_dict['number_of_atoms'],
                                                    len(traj_data['positions_traj_times']))
            ordering_array = self._generate_sites_ordering(out_dict['cell']['atoms'],
                                                           traj_data['positions_traj_data'][-1])
            old_array = copy.copy(traj_data['positions_traj_data'])
            raw_trajectory['positions_traj_data'] = self._reorder_array(ordering_array,old_array)
            raw_trajectory['positions'] = numpy.array(traj_data['positions_traj_data'])
            raw_trajectory['times'] = numpy.array(traj_data['positions_traj_times'])
            
            self._check_configs(expected_configs,traj_data['positions_traj_steps'])
        except IOError:
            out_dict['warnings'].append("Unable to open the POS file... skipping.")
            successful = False
        except Exception as e:
            out_dict['warnings'].append("Error parsing POS file ({}). Skipping file."
                                        .format(e.message))
            successful = False
            
        # =============== CELL trajectory ============================
        try:
            with open(os.path.join( out_folder.get_abs_path('.'), 
                                    '{}.cel'.format(self._calc.PREFIX) )) as celfile:
                cel_data = [l.split() for l in celfile]   
            traj_data=parse_cp_traj_stanzas(num_elements=3, 
                                            splitlines=cel_data, 
                                            prepend_name='cell_traj',
                                            rescale=bohr_to_ang)
            raw_trajectory['cells'] = numpy.array(traj_data['cell_traj_data'])
            self._check_configs(expected_configs,traj_data['cell_traj_steps'])
        except IOError:
            out_dict['warnings'].append("Unable to open the CEL file... skipping.")
        except Exception as e:
            out_dict['warnings'].append("Error parsing CEL file ({}). Skipping file."
                                        .format(e.message))
            
        # =============== VELOCITIES trajectory ============================
        try:
            with open(os.path.join( out_folder.get_abs_path('.'), 
                                    '{}.vel'.format(self._calc.PREFIX) )) as velfile:
                vel_data = [l.split() for l in velfile]   
            traj_data=parse_cp_traj_stanzas(num_elements=out_dict['number_of_atoms'],
                                            splitlines=vel_data, 
                                            prepend_name='velocities_traj', 
                                            rescale=bohr_to_ang/timeau_to_sec*10**12) # velocities in ang/ps, 
            old_array = copy.copy(traj_data['velocities_traj_data'])
            raw_trajectory['velocities_traj_data'] = self._reorder_array(ordering_array,old_array)

            raw_trajectory['velocities'] = numpy.array(traj_data['velocities_traj_data'])
            self._check_configs(expected_configs,traj_data['velocities_traj_steps'])
        except IOError:
            out_dict['warnings'].append("Unable to open the VEL file... skipping.")
        except Exception as e:
            out_dict['warnings'].append("Error parsing VEL file ({}). Skipping file."
                                               .format(e.message))
            
        # =============== EVP trajectory ============================
        try:
            matrix = numpy.genfromtxt(os.path.join( out_folder.get_abs_path('.'), 
                                                    '{}.evp'.format(self._calc.PREFIX) ))
            steps = matrix[:,0]
            steps = numpy.array(steps,dtype=int)
            
            raw_trajectory['electronic_kinetic_energy'] = matrix[:,1] * hartree_to_ev    # EKINC, eV
            raw_trajectory['cell_temperature']          = matrix[:,2]                    # TEMPH, K
            raw_trajectory['ionic_temperature']         = matrix[:,3]                    # TEMPP, K
            raw_trajectory['scf_total_energy']          = matrix[:,4] * hartree_to_ev    # ETOT, eV
            raw_trajectory['enthalpy']                  = matrix[:,5] * hartree_to_ev    # ENTHAL, eV
            raw_trajectory['enthalpy_plus_kinetic']     = matrix[:,6] * hartree_to_ev    # ECONS, eV
            raw_trajectory['energy_constant_motion']    = matrix[:,7] * hartree_to_ev    # ECONT, eV
            raw_trajectory['volume']                    = matrix[:,8] * (bohr_to_ang**3) # volume, angstrom^3
            raw_trajectory['pressure']                  = matrix[:,9]                    # out_press, GPa
        except Exception as e:
            out_dict['warnings'].append("Error parsing EVP file ({}). Skipping file.".format(e.message))
        except IOError:
            out_dict['warnings'].append("Unable to open the EVP file... skipping.")
            


        raw_trajectory['symbols'] = raw_trajectory['times'][:out_dict['number_of_atoms']] #  <-----------------! + reshuffling
        traj = TrajectoryData()
        traj.set_trajectory(steps,
                            raw_trajectory['times'],
                            raw_trajectory['cells'],
                            raw_trajectory['symbols'],
                            raw_trajectory['positions'],
                            raw_trajectory['velocities'],
                            )
        for this_name in evp_keys:
            traj.set_array(this_name,raw_trajectory[this_name])
        traj.store()
        self._calc._add_link_to(traj, label=self.get_linkname_trajectory() )        
        self._set_linkname_outtrajectory(self._outtraj_name)
        
        # convert the dictionary into an AiiDA object
        output_params = ParameterData(dict=out_dict)
        
        # save it into db
        output_params.store()
        self._calc._add_link_to(output_params, label=self.get_linkname_outparams() )
        
        return successful

    def get_linkname_trajectory(self):
        """
        Returns the name of the link to the output_structure (None if not present)
        """
        return self.linkname_outtrajectory
    
    def _set_linkname_outtrajectory(self,linkname):
        """
        Set the name of the link to the output_structure
        """
        setattr(self,'linkname_outtrajectory',linkname)

    def _check_configs(self,expected,actual):
        # here I check the consistency of the output, since sometimes 
        # the same configuration is printed more than once
        if expected == None:
            expected = actual
        else:
            if expected != actual:
                raise ValueError('# configurations found ({}) different than what expected ({})'
                                 .format(actual,expected))
        return
    
    def _set_default_dict(self,cell_key,pos_vel_keys,evp_keys,nat,nstep):
        the_dict = {}
        the_dict[cell_key] = [ [[],[],[]] ] * nstep
        for this_key in pos_vel_keys:
            the_dict[this_key] =  [[[]]*nat]*nstep
        for this_key in evp_keys:
            the_dict[this_key] = [None]*nstep
        return the_dict
    
    def _generate_sites_ordering(self,xml_atoms,positions):
        """
        take the positions of xml and from file.pos of the LAST step and compare them 
        """
        import numpy
        xml_positions = [i[1] for i in xml_atoms]
        ordering = [0]*len(xml_positions)
        for xml_i,xml_atom in enumerate(xml_positions):
            read_pos = 0
            for read_i,read_atom in enumerate(positions):
                if numpy.linalg.norm(numpy.array(read_atom)-numpy.array(xml_atom)) < 1e-5:
                    ordering[xml_i] = read_i
                    break
        return ordering
        
    def _reorder_array(self,ordering,the_array):
        the_new_array = []
        for this_positions in the_array: # for each timestep
            the_new_array.append(
                [ this_positions[ordering[i]] for i in range(len(this_positions)) ]
                )
            
        return the_new_array

        












