# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_pw import (
                            parse_raw_output,QEOutputParsingError)
from aiida.orm.data.parameter import ParameterData
from aiida.parsers.parser import Parser#, ParserParamManager
from aiida.parsers.plugins.quantumespresso import convert_qe2aiida_structure
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import UniquenessError
from aiida.orm.data.array.bands import BandsData
from aiida.orm.data.array.bands import KpointsData

#TODO: I don't like the generic class always returning a name for the link to the output structure


class PwParser(Parser):
    """
    This class is the implementation of the Parser class for PWscf.
    """

    _setting_key = 'parser_options'

    def __init__(self,calc):
        """
        Initialize the instance of PwParser
        """
        self._possible_symmetries = self._get_qe_symmetry_list()
        # check for valid input
        if not isinstance(calc,PwCalculation):
            raise QEOutputParsingError("Input calc must be a PwCalculation")
        
        super(PwParser, self).__init__(calc)
                
    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """        
        from aiida.common.exceptions import InvalidOperation
        import os
        import glob
                
        successful = True 
        
        # check if I'm not to overwrite anything
        #state = self._calc.get_state()
        #if state != calc_states.PARSING:
        #    raise InvalidOperation("Calculation not in {} state"
        #                           .format(calc_states.PARSING) )
        
        # look for eventual flags of the parser
        try:
            parser_opts = self._calc.inp.settings.get_dict()[self.get_parser_settings_key()]
        except (AttributeError,KeyError):
            parser_opts = {}
        
        # load the input dictionary
        # TODO: pass this input_dict to the parser. It might need it.            
        input_dict = self._calc.inp.parameters.get_dict()
       
        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("No retrieved folder found")
            return False, ()

        
        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        # at least the stdout should exist
        if not self._calc._OUTPUT_FILE_NAME in list_of_files:
            self.logger.error("Standard output not found")
            successful = False
            return successful,()
        # if there is something more, I note it down, so to call the raw parser
        # with the right options
        # look for xml
        has_xml = False
        if self._calc._DATAFILE_XML_BASENAME in list_of_files:
            has_xml = True
        # look for bands
        has_bands = False
        if glob.glob( os.path.join(out_folder.get_abs_path('.'),
                                   'K*[0-9]')):
            # Note: assuming format of kpoints subfolder is K*[0-9]
            has_bands = True
            # TODO: maybe it can be more general than bands only?
        out_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc._OUTPUT_FILE_NAME )
        xml_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc._DATAFILE_XML_BASENAME )
        dir_with_bands = out_folder.get_abs_path('.')
        
        # call the raw parsing function
        parsing_args = [out_file,input_dict,parser_opts]
        if has_xml:
            parsing_args.append(xml_file)
        if has_bands:
            if not has_xml:
                self.logger.warning("Cannot parse bands if xml file not "
                                     "found")
            else:
                parsing_args.append(dir_with_bands)
        
        out_dict,trajectory_data,structure_data,bands_data,raw_successful = parse_raw_output(*parsing_args)
        
        # if calculation was not considered failed already, use the new value
        successful = raw_successful if successful else successful
        
        # The symmetry info has large arrays, that occupy most of the database.
        # turns out most of this is due to 64 matrices that are repeated over and over again.
        # therefore I map part of the results in a list of dictionaries wrote here once and for all
        # if the parser_opts has a key all_symmetries set to True, I don't reduce it
        all_symmetries = parser_opts.get('all_symmetries',False)
        if not all_symmetries:
            try:
                if 'symmetries' in out_dict.keys():
                    old_symmetries = out_dict['symmetries']
                    new_symmetries = []
                    for this_sym in old_symmetries:
                        name = this_sym['name']
                        index = None
                        for i,this in enumerate(self._possible_symmetries):
                            if name in this['name']:
                                index = i
                        if index is None:
                            self.logger.error("Symmetry {} not found".format(name))
                        new_dict = {}
                        # note: here I lose the information about equivalent 
                        # ions and fractional_translation.
                        # They will be present with all_symmetries=True
                        new_dict['t_rev'] = this_sym['t_rev']
                        new_dict['symmetry_number'] = index
                        new_symmetries.append(new_dict)
                    out_dict['symmetries'] = new_symmetries # and overwrite the old one
            except KeyError: # no symmetries were parsed (failed case, likely)
                self.logger.error("No symmetries were found in output")
        
        new_nodes_list = []
        
        # I eventually save the new structure. structure_data is unnecessary after this
        in_struc = self._calc.get_inputs_dict()['structure']
        type_calc = input_dict['CONTROL']['calculation']
        struc = in_struc
        if type_calc in ['relax','vc-relax','md','vc-md']:
            if 'cell' in structure_data.keys():
                struc = convert_qe2aiida_structure(structure_data,input_structure=in_struc)
                new_nodes_list.append((self.get_linkname_outstructure(),struc))
        
        k_points_list = trajectory_data.pop('k_points',None)
        k_points_weights_list = trajectory_data.pop('k_points_weights',None)
        
        if k_points_list is not None:
            
            # build the kpoints object
            if out_dict['k_points_units'] not in ['2 pi / Angstrom']:
                raise QEOutputParsingError('Error in kpoints units (should be cartesian)')
            # converting bands into a BandsData object (including the kpoints)
            
            kpoints_from_output = KpointsData()
            kpoints_from_output.set_cell_from_structure(struc)
            kpoints_from_output.set_kpoints(k_points_list, cartesian=True,
                                            weights = k_points_weights_list)
            kpoints_from_input = self._calc.inp.kpoints
            
            if not bands_data:
                try:
                    kpoints_from_input.get_kpoints()
                except AttributeError:
                    new_nodes_list += [(self.get_linkname_out_kpoints(),kpoints_from_output)]
            
            if bands_data:
                import numpy
                # converting bands into a BandsData object (including the kpoints)
                
                kpoints_for_bands = kpoints_from_output
                
                try:
                    kpoints_from_input.get_kpoints()
                    kpoints_for_bands.labels = kpoints_from_input.labels
                except (AttributeError,ValueError,TypeError):
                    # AttributeError: no list of kpoints in input
                    # ValueError: labels from input do not match the output 
                    #      list of kpoints (some kpoints are missing)
                    # TypeError: labels are not set, so kpoints_from_input.labels=None
                    pass
                
                # get the bands occupations.
                # correct the occupations of QE: if it computes only one component,
                # it occupies it with half number of electrons
                try:
                    bands_data['occupations'][1]
                    the_occupations = bands_data['occupations']
                except IndexError:
                    the_occupations = 2.*numpy.array(bands_data['occupations'][0])
                
                try:
                    bands_data['bands'][1]
                    bands_energies = bands_data['bands']
                except IndexError:
                    bands_energies = bands_data['bands'][0]
                
                the_bands_data = BandsData()
                the_bands_data.set_kpointsdata(kpoints_for_bands)
                the_bands_data.set_bands(bands_energies,
                                         units = bands_data['bands_units'],
                                         occupations = the_occupations)
                
                new_nodes_list += [('output_band',the_bands_data)]
                out_dict['linknames_band'] = ['output_band']
        
        # convert the dictionary into an AiiDA object
        output_params = ParameterData(dict=out_dict)
        # return it to the execmanager
        new_nodes_list.append((self.get_linkname_outparams(),output_params))
        
        if trajectory_data:
            import numpy
            from aiida.orm.data.array.trajectory import TrajectoryData
            from aiida.orm.data.array import ArrayData
            try:
                positions = numpy.array( trajectory_data.pop('atomic_positions_relax') )
                try:
                    cells = numpy.array( trajectory_data.pop('lattice_vectors_relax') )
                    # if KeyError, the MD was at fixed cell
                except KeyError:
                    cells = numpy.array( [in_struc.cell]*len(positions) )
            
                symbols = numpy.array( [ str(i.kind_name) for i in in_struc.sites ] )
                stepids = numpy.arange( len(positions) ) # a growing integer per step
                # I will insert time parsing when they fix their issues about time 
                # printing (logic is broken if restart is on)

                traj = TrajectoryData()
                traj.set_trajectory(stepids = stepids,
                                    cells = cells,
                                    symbols = symbols,
                                    positions = positions,
                                    )
                for x in trajectory_data.iteritems():
                    traj.set_array(x[0],numpy.array(x[1]))
                # return it to the execmanager
                new_nodes_list.append((self.get_linkname_outtrajectory(),traj))
                
            except KeyError:
                # forces, atomic charges and atomic mag. moments, in scf 
                # calculation (when outputed)
                arraydata = ArrayData()
                for x in trajectory_data.iteritems():
                    arraydata.set_array(x[0],numpy.array(x[1]))
                # return it to the execmanager
                new_nodes_list.append((self.get_linkname_outarray(),arraydata))
            
        return successful,new_nodes_list

    def get_parser_settings_key(self):
        """
        Return the name of the key to be used in the calculation settings, that
        contains the dictionary with the parser_options 
        """
        return 'parser_options'

    def get_linkname_outstructure(self):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'
            
    def get_linkname_outtrajectory(self):
        """
        Returns the name of the link to the output_trajectory.
        Node exists in case of calculation='md', 'vc-md', 'relax', 'vc-relax'
        """
        return 'output_trajectory'

    def get_linkname_outarray(self):
        """
        Returns the name of the link to the output_array
        Node may exist in case of calculation='scf'
        """
        return 'output_array'
    
    def get_linkname_out_kpoints(self):
        """
        Returns the name of the link to the output_kpoints
        Node exists if cell has changed and no bands are stored.
        """
        return 'output_kpoints'
    
    def get_extended_symmetries(self):
        """
        Return the extended dictionary of symmetries.
        """
        datas = self._calc.get_outputs(type=ParameterData,also_labels = True)
        all_data = [ i[1] for i in datas if i[0]==self.get_linkname_outparams() ]
        if len(all_data)>1:
            raise UniquenessError('More than one output parameterdata found.')
        elif not all_data:
            return []
        else:
            compact_list = all_data[0].get_dict()['symmetries']  # rimetti lo zero
            new_list = []
            # copy what wasn't compact
            for element in compact_list:
                new_dict = {}
                for keys in ['t_rev','equivalent_ions','fractional_translation']:
                    try:
                        new_dict[keys] = element[keys]
                    except KeyError:
                        pass
                # expand the rest
                new_dict['name'] = self._possible_symmetries[element['symmetry_number']]['name']
                new_dict['rotation'] = self._possible_symmetries[element['symmetry_number']]['matrix']
                new_dict['inversion'] = self._possible_symmetries[element['symmetry_number']]['inversion']
                new_list.append(new_dict)
            return new_list
            
    def _get_qe_symmetry_list(self):
        """
        Hard coded names and rotation matrices + inversion from QE v 5.0.2
        Function for Parser class usage only.
        :return: a list of dictionaries, each containing name (string),
                 inversion (boolean) and matrix (list of lists)
        """
        sin3 = 0.866025403784438597
        cos3 = 0.5
        msin3 =-0.866025403784438597
        mcos3 = -0.5
    
        # 32 rotations that are checked + inversion
        matrices = [[[1.,  0.,  0.],  [0.,  1.,  0.],  [0.,  0.,  1.]],
                [[-1., 0.,  0.],  [0., -1.,  0.],  [0.,  0.,  1.]],
                [[-1., 0.,  0.],  [0.,  1.,  0.],  [0.,  0., -1.]],
                [[1.,  0.,  0.],  [0., -1.,  0.],  [0.,  0., -1.]],
                [[0.,  1.,  0.],  [1.,  0.,  0.],  [0.,  0., -1.]],
                [[0., -1.,  0.], [-1.,  0.,  0.],  [0.,  0., -1.]],
                [[0., -1.,  0.],  [1.,  0.,  0.],  [0.,  0.,  1.]],
                [[0.,  1.,  0.], [-1.,  0.,  0.],  [0.,  0.,  1.]],
                [[0.,  0.,  1.],  [0., -1.,  0.],  [1.,  0.,  0.]],
                [[0.,  0., -1.],  [0., -1.,  0.], [-1.,  0.,  0.]],
                [[0.,  0., -1.],  [0.,  1.,  0.],  [1.,  0.,  0.]],
                [[0.,  0.,  1.],  [0.,  1.,  0.], [-1.,  0.,  0.]],
                [[-1., 0.,  0.],  [0.,  0.,  1.],  [0.,  1.,  0.]],
                [[-1., 0.,  0.],  [0.,  0., -1.],  [0., -1.,  0.]],
                [[1.,  0.,  0.],  [0.,  0., -1.],  [0.,  1.,  0.]],
                [[1.,  0.,  0.],  [0.,  0.,  1.],  [0., -1.,  0.]],
                [[0.,  0.,  1.],  [1.,  0.,  0.],  [0.,  1.,  0.]],
                [[0.,  0., -1.], [-1.,  0.,  0.],  [0.,  1.,  0.]],
                [[0.,  0., -1.],  [1.,  0.,  0.],  [0., -1.,  0.]],
                [[0.,  0.,  1.], [-1.,  0.,  0.],  [0., -1.,  0.]],
                [[0.,  1.,  0.],  [0.,  0.,  1.],  [1.,  0.,  0.]],
                [[0., -1.,  0.],  [0.,  0., -1.],  [1.,  0.,  0.]],
                [[0., -1.,  0.],  [0.,  0.,  1.], [-1.,  0.,  0.]],
                [[0.,  1.,  0.],  [0.,  0., -1.], [-1.,  0.,  0.]],
                [[ cos3,  sin3, 0.], [msin3,  cos3, 0.], [0., 0.,  1.]],
                [[ cos3, msin3, 0.],  [sin3,  cos3, 0.], [0., 0.,  1.]],
                [[mcos3,  sin3, 0.], [msin3, mcos3, 0.], [0., 0.,  1.]],
                [[mcos3, msin3, 0.],  [sin3, mcos3, 0.], [0., 0.,  1.]],
                [[ cos3, msin3, 0.], [msin3, mcos3, 0.], [0., 0., -1.]],
                [[ cos3,  sin3, 0.],  [sin3, mcos3, 0.], [0., 0., -1.]],
                [[mcos3, msin3, 0.], [msin3,  cos3, 0.], [0., 0., -1.]],
                [[mcos3,  sin3, 0.],  [sin3,  cos3, 0.], [0., 0., -1.]],
               ]
        
        # names for the 32 matrices, with and without inversion
        matrices_name = ['identity                                     ',
                    '180 deg rotation - cart. axis [0,0,1]        ',
                    '180 deg rotation - cart. axis [0,1,0]        ',
                    '180 deg rotation - cart. axis [1,0,0]        ',
                    '180 deg rotation - cart. axis [1,1,0]        ',
                    '180 deg rotation - cart. axis [1,-1,0]       ',
                    ' 90 deg rotation - cart. axis [0,0,-1]       ',
                    ' 90 deg rotation - cart. axis [0,0,1]        ',
                    '180 deg rotation - cart. axis [1,0,1]        ',
                    '180 deg rotation - cart. axis [-1,0,1]       ',
                    ' 90 deg rotation - cart. axis [0,1,0]        ',
                    ' 90 deg rotation - cart. axis [0,-1,0]       ',
                    '180 deg rotation - cart. axis [0,1,1]        ',
                    '180 deg rotation - cart. axis [0,1,-1]       ',
                    ' 90 deg rotation - cart. axis [-1,0,0]       ',
                    ' 90 deg rotation - cart. axis [1,0,0]        ',
                    '120 deg rotation - cart. axis [-1,-1,-1]     ',
                    '120 deg rotation - cart. axis [-1,1,1]       ',
                    '120 deg rotation - cart. axis [1,1,-1]       ',
                    '120 deg rotation - cart. axis [1,-1,1]       ',
                    '120 deg rotation - cart. axis [1,1,1]        ',
                    '120 deg rotation - cart. axis [-1,1,-1]      ',
                    '120 deg rotation - cart. axis [1,-1,-1]      ',
                    '120 deg rotation - cart. axis [-1,-1,1]      ',
                    ' 60 deg rotation - cryst. axis [0,0,1]       ',
                    ' 60 deg rotation - cryst. axis [0,0,-1]      ',
                    '120 deg rotation - cryst. axis [0,0,1]       ',
                    '120 deg rotation - cryst. axis [0,0,-1]      ',
                    '180 deg rotation - cryst. axis [1,-1,0]      ',
                    '180 deg rotation - cryst. axis [2,1,0]       ',
                    '180 deg rotation - cryst. axis [0,1,0]       ',
                    '180 deg rotation - cryst. axis [1,1,0]       ',
                    'inversion                                    ',
                    'inv. 180 deg rotation - cart. axis [0,0,1]   ',
                    'inv. 180 deg rotation - cart. axis [0,1,0]   ',
                    'inv. 180 deg rotation - cart. axis [1,0,0]   ',
                    'inv. 180 deg rotation - cart. axis [1,1,0]   ',
                    'inv. 180 deg rotation - cart. axis [1,-1,0]  ',
                    'inv.  90 deg rotation - cart. axis [0,0,-1]  ',
                    'inv.  90 deg rotation - cart. axis [0,0,1]   ',
                    'inv. 180 deg rotation - cart. axis [1,0,1]   ',
                    'inv. 180 deg rotation - cart. axis [-1,0,1]  ',
                    'inv.  90 deg rotation - cart. axis [0,1,0]   ',
                    'inv.  90 deg rotation - cart. axis [0,-1,0]  ',
                    'inv. 180 deg rotation - cart. axis [0,1,1]   ',
                    'inv. 180 deg rotation - cart. axis [0,1,-1]  ',
                    'inv.  90 deg rotation - cart. axis [-1,0,0]  ',
                    'inv.  90 deg rotation - cart. axis [1,0,0]   ',
                    'inv. 120 deg rotation - cart. axis [-1,-1,-1]',
                    'inv. 120 deg rotation - cart. axis [-1,1,1]  ',
                    'inv. 120 deg rotation - cart. axis [1,1,-1]  ',
                    'inv. 120 deg rotation - cart. axis [1,-1,1]  ',
                    'inv. 120 deg rotation - cart. axis [1,1,1]   ',
                    'inv. 120 deg rotation - cart. axis [-1,1,-1] ',
                    'inv. 120 deg rotation - cart. axis [1,-1,-1] ',
                    'inv. 120 deg rotation - cart. axis [-1,-1,1] ',
                    'inv.  60 deg rotation - cryst. axis [0,0,1]  ',
                    'inv.  60 deg rotation - cryst. axis [0,0,-1] ',
                    'inv. 120 deg rotation - cryst. axis [0,0,1]  ',
                    'inv. 120 deg rotation - cryst. axis [0,0,-1] ',
                    'inv. 180 deg rotation - cryst. axis [1,-1,0] ',
                    'inv. 180 deg rotation - cryst. axis [2,1,0]  ',
                    'inv. 180 deg rotation - cryst. axis [0,1,0]  ',
                    'inv. 180 deg rotation - cryst. axis [1,1,0]  ']

        # unfortunately, the naming is done in a rather fortran-style way
        rotations = []
        x=0
        for key,value in zip(matrices_name[:len(matrices)],matrices):
            rotations.append({'name':key,'matrix':value,'inversion':False})
            x += 1
        for key,value in zip(matrices_name[len(matrices):],matrices):
            rotations.append({'name':key,'matrix':value,'inversion':True})
            x += 1

        return rotations
        
