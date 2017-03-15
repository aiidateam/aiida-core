# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
A collection of function that are used to parse the output of Quantum Espresso PHonon.
The function that needs to be called from outside is parse_raw_ph_output().
Ideally, the functions should work even without aiida and will return a dictionary with parsed keys.
"""
from xml.dom.minidom import parseString
from aiida.parsers.plugins.quantumespresso.constants import *
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.parsers.plugins.quantumespresso.raw_parser_pw import parse_xml_child_bool,read_xml_card,convert_qe_time_to_sec
import numpy

def parse_raw_ph_output(out_file, tensor_file=None, dynmat_files=[]):
    """
    Parses the output of a calculation
    Receives in input the paths to the output file and the xml file.
    
    Args: 
        out_file 
            path to ph std output
    
    Returns:
        out_dict
            a dictionary with parsed data
        successful
            a boolean that is False in case of failed calculations
            
    Raises:
        QEOutputParsingError
            for errors in the parsing

    2 different keys to check in output: parser_warnings and warnings.
    On an upper level, these flags MUST be checked.
    The first two are expected to be empty unless QE failures or unfinished jobs.
    """
    
    job_successful = True
    
    parser_version = '0.1'
    parser_info = {}
    parser_info['parser_warnings'] = []
    parser_info['parser_info'] = 'AiiDA QE-PH Parser v{}'.format(parser_version)
    
    # load QE out file
    try:
        with open(out_file,'r') as f:
            out_lines = f.readlines()
    except IOError:
        # if the file cannot be open, the error is severe.
        raise QEOutputParsingError("Failed to open output file: {}.".format(out_file))
    
    # in case of executable failures, check if there is any output at all
    if not out_lines:
        job_successful = False
    
    # check if the job has finished (that doesn't mean without errors)
    finished_run = False
    for line in out_lines[::-1]:
        if 'JOB DONE' in line:
            finished_run = True
            break
    
    if not finished_run:
        warning = 'QE ph run did not reach the end of the execution.'
        parser_info['parser_warnings'].append(warning)        
        job_successful = False
    
    # parse tensors, if present
    tensor_data = {}
    if tensor_file:
        with open(tensor_file,'r') as f:
            tensor_lines = f.read()
        try:
            tensor_data = parse_ph_tensor(tensor_lines)
        except QEOutputParsingError:
            parser_info['parser_warnings'].append('Error while parsing the tensor files')
            pass
    
    # parse ph output
    with open(out_file,'r') as f:
        out_lines = f.readlines()
    out_data,critical_messages = parse_ph_text_output(out_lines)
    
    # if there is a severe error, the calculation is FAILED
    if any([x in out_data['warnings'] for x in critical_messages]):
        job_successful = False
    
    # parse dynamical matrices if present
    dynmat_data = {}
    if dynmat_files:
        # find lattice parameter
        for dynmat_counter,this_dynmat in enumerate(dynmat_files):
            # read it
            with open(this_dynmat,'r') as f:
                lines = f.readlines()
            
            # check if the file contains frequencies (i.e. is useful) or not
            dynmat_to_parse = False
            if not lines:
                continue
            try:
                _ = [ float(i) for i in lines[0].split()]
            except ValueError:
                dynmat_to_parse = True
            if not dynmat_to_parse:
                continue
            
            # parse it
            this_dynmat_data = parse_ph_dynmat(lines) 
            
            # join it with the previous dynmat info
            dynmat_data['dynamical_matrix_%s' % dynmat_counter] = this_dynmat_data
            # TODO: use the bands format?

    # join dictionaries, there should not be any twice repeated key
    for key in out_data.keys():
        if key in tensor_data.keys():
            raise AssertionError('{} found in two dictionaries'.format(key))
    for key in out_data.keys():
        if key in dynmat_data.keys():
            if key=='warnings': # this ke can be found in both, but is not a problem
                out_data['warnings'] += dynmat_data['warnings']
                del dynmat_data['warnings']
            else:
                raise AssertionError('{} found in two dictionaries'.format(key))
    # I don't check the dynmat_data and parser_info keys 
    final_data = dict(dynmat_data.items() + out_data.items() + 
                      tensor_data.items() + parser_info.items())

    return final_data,job_successful


def parse_ph_tensor(data):
    """
    Parse the xml tensor file of QE v5.0.3
    data must be read from the file with the .read() function (avoid readlines)
    """
    
    dom = parseString(data)
    
    parsed_data = {}
    
    parsed_data['xml_warnings'] = []
    
    # card EF_TENSORS
    cardname = 'EF_TENSORS'
    target_tags = read_xml_card(dom,cardname)
    
    tagname='DONE_ELECTRIC_FIELD'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)
    
    if parsed_data[tagname.lower()]:
        try:
            second_tagname = 'DIELECTRIC_CONSTANT'  
            parsed_data[second_tagname.lower()] = parse_xml_matrices(second_tagname,
                                                                     target_tags)
        except:
            raise QEOutputParsingError('Failed to parse Dielectric constant')
    
    tagname='DONE_EFFECTIVE_CHARGE_EU'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)
    
    if parsed_data[tagname.lower()]:
        try:
            second_tagname = 'EFFECTIVE_CHARGES_EU'
            dumb_matrix = parse_xml_matrices(second_tagname,target_tags)
            # separate the elements of the messy matrix, with a matrix 3x3 for each element
            new_matrix = []
            this_at = []
            for i in dumb_matrix:
                this_at.append(i)
                if len(this_at) == 3:
                    new_matrix.append(this_at)
                    this_at = []
                    
            parsed_data[second_tagname.lower()] = new_matrix
        except:
            raise QEOutputParsingError('Failed to parse effective charges eu')

    return parsed_data
    
def parse_xml_matrices(tagname,target_tags):
    """
    Can be used to load the disordered matrices of the QE XML file
    """
    a = target_tags.getElementsByTagName(tagname)[0]
    b = a.childNodes[0]
    flat_array = b.data.split()
    # convert to float, then into a list of tuples, then into a list of lists
    flat_array = [float(i) for i in flat_array]
    list_tuple = zip(*[iter(flat_array)]*3)
    return [list(i) for i in list_tuple]

def parse_ph_text_output(lines):
    """
    Parses the stdout of QE-PH.
    
    :param lines: list of strings, the file as read by readlines()
    
    :return parsed_data: dictionary with parsed values.
    :return critical_messages: a list with critical messages. If any is found in
                               parsed_data['warnings'], the calculation is FAILED!
    """
    from aiida.parsers.plugins.quantumespresso.raw_parser_pw import parse_QE_errors

    parsed_data = {}
    parsed_data['warnings'] = []
    # parse time, starting from the end
    # apparently, the time is written multiple times
    for line in reversed(lines):
        if 'PHONON' in line and 'WALL' in line:
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data['wall_time'] = time
            except Exception:
                parsed_data['warnings'].append('Error while parsing wall time.')
                
            try:
                parsed_data['wall_time_seconds'] = \
                    convert_qe_time_to_sec(parsed_data['wall_time'])
            except ValueError:
                raise QEOutputParsingError("Unable to convert wall_time in seconds.")
            break
        
    # parse number of q-points and number of atoms
    for count,line in enumerate(lines):
        if 'q-points for this run' in line:
            try:
                num_qpoints = int(line.split('/')[1].split('q-points')[0])
                if ( 'number_of_qpoints' in parsed_data.keys() and 
                     num_qpoints != parsed_data['number_of_qpoints']):
                    parsed_data['warnings'].append("Number q-points found "
                                                   "several times with different"
                                                   " values")
                else:
                    parsed_data['number_of_qpoints'] = num_qpoints
            except Exception:
                parsed_data['warnings'].append("Error while parsing number of "
                                               "q points.")
        
        elif 'q-points)' in line:
            # case of a 'only_wfc' calculation
            try:
                num_qpoints = int(line.split('q-points')[0].split('(')[1])
                if ( 'number_of_qpoints' in parsed_data.keys() and 
                     num_qpoints != parsed_data['number_of_qpoints']):
                    parsed_data['warnings'].append("Number q-points found "
                                                   "several times with different"
                                                   " values")
                else:
                    parsed_data['number_of_qpoints'] = num_qpoints
            except Exception:
                parsed_data['warnings'].append("Error while parsing number of "
                                               "q points.")
            
        elif "number of atoms/cell" in line:
            try:
                num_atoms = int(line.split('=')[1])
                parsed_data['number_of_atoms'] = num_atoms
            except Exception:
                parsed_data['warnings'].append("Error while parsing number of "
                                               "atoms.")
        
        elif "irreducible representations" in line:
            if 'number_of_irr_representations_for_each_q' not in parsed_data.keys():
                parsed_data['number_of_irr_representations_for_each_q'] = []
            try:
                num_irr_repr = int(line.split('irreducible')[0].split('are')[1])
                parsed_data['number_of_irr_representations_for_each_q'].append(num_irr_repr)
            except Exception:
                pass
            
        #elif "lattice parameter (alat)" in line:
        #    lattice_parameter = float(line.split('=')[1].split('a.u.')[0])*bohr_to_ang
            
        #elif ('cell' not in parsed_data.keys() and
        #      "crystal axes: (cart. coord. in units of alat)" in line):
        #    cell = [ [float(e)*lattice_parameter for e in li.split("a({}) = (".format(i+1)
        #            )[1].split(")")[0].split()] for i,li in enumerate(lines[count+1:count+4])]
        #    parsed_data['cell'] = cell
            
    # TODO: find a more exhaustive list of the common errors of ph
    
    # critical warnings: if any is found, the calculation status is FAILED
    critical_warnings = {'No convergence has been achieved':
                         'Phonon did not reach end of self consistency',
                         'Maximum CPU time exceeded':'Maximum CPU time exceeded',
                         '%%%%%%%%%%%%%%':None,
                         }
    
    minor_warnings = {'Warning:':None,
                      }
    
    all_warnings = dict(critical_warnings.items() + minor_warnings.items())

    for count,line in enumerate(lines):

        if any( i in line for i in all_warnings):
            messages = [ all_warnings[i] if all_warnings[i] is not None 
                            else line for i in all_warnings.keys() 
                            if i in line]
                                               
            if '%%%%%%%%%%%%%%' in line:
                messages = parse_QE_errors(lines,count,parsed_data['warnings']) 
                        
            # if it found something, add to log
            if len(messages)>0:
                parsed_data['warnings'].extend(messages)
            
    return parsed_data,critical_warnings.values()

def parse_ph_dynmat(data,lattice_parameter=None,also_eigenvectors=False,
                    parse_header=False):
    """
    parses frequencies and eigenvectors of a single dynamical matrix
    :param data: the text read with the function readlines()
    :param lattice_parameter: the lattice_parameter ('alat' in QE jargon). If 
        None, q_point is kept in 2pi/a coordinates as in the dynmat file.
    :param also_eigenvectors: if True, return an additional 'eigenvectors' 
        array in output, containing also the eigenvectors. This will be
        a list of lists, that when converted to a numpy array has 4 indices,
        with shape Neigenstates x Natoms x 3(xyz) x 2 (re,im)
        To convert to a complex numpy array, you can use::

          ev = np.array(parsed_data['eigenvectors'])
          ev = ev[:,:,:,0] + 1j * ev[:,:,:,1]
    :param parse_header: if True, return additional keys in the returned
        parsed_data dictionary, including information from the header

    :return parsed_data: a dictionary with parsed values and units
    
    """
    parsed_data = {}
    parsed_data['warnings'] = []
    
    if 'Dynamical matrix file' not in data[0]:
        raise QEOutputParsingError('Dynamical matrix is not in the expected format') 
        
    frequencies = []
    eigenvectors = []

    starting_line = 1
    if parse_header:
        header_dict = {"warnings": []}
        try:
            pieces = data[2].split()
            if len(pieces) != 9:
                raise QEOutputParsingError("Wrong # of elements on line 3")
            try:
                num_species = int(pieces[0])
                num_atoms = int(pieces[1])
                header_dict['ibrav'] = int(pieces[2])
                header_dict['celldm'] = [float(i) for i in pieces[3:]]
                # In angstrom
                alat = header_dict['celldm'][0] * bohr_to_ang
                if abs(alat) < 1.e-5:
                    raise QEOutputParsingError(
                        "Lattice constant=0! Probably you are using an "
                        "old Quantum ESPRESSO version?")
                header_dict["alat"] = alat
                header_dict["alat_units"] = "angstrom"
            except ValueError:
                raise QEOutputParsingError("Wrong data on line 3")

            starting_line = 3
            if header_dict['ibrav'] == 0:
                if 'Basis vectors' not in data[3]:
                    raise QEOutputParsingError(
                        "Wrong format (no 'Basis vectors' line)")
                try:
                    v1 = [float(_)*alat for _ in data[4].split()]
                    v2 = [float(_)*alat for _ in data[5].split()]
                    v3 = [float(_)*alat for _ in data[6].split()]
                    if len(v1) != 3 or len(v2) != 3 or len(v3) != 3:
                        raise QEOutputParsingError(
                            "Wrong length for basis vectors")
                    header_dict['lattice_vectors'] = [v1,v2,v3]
                    header_dict['lattice_vectors_units'] = "angstrom"
                except ValueError:
                    raise QEOutputParsingError("Wrong data for basis vectors")
                starting_line += 4

            species_info = {}
            species = []
            for idx, sp_line in enumerate(
                data[starting_line:starting_line + num_species],
                start=1):
                pieces = sp_line.split("'")
                if len(pieces) != 3:
                    raise QEOutputParsingError(
                        "Wrong # of elements for one of the species")
                try:
                    if int(pieces[0]) != idx:
                        raise QEOutputParsingError(
                            "Error with the indices of the species")
                    species.append([pieces[1].strip(),
                                    float(pieces[2])/amu_Ry])
                except ValueError:
                    raise QEOutputParsingError("Error parsing the species")
            
            masses = dict(species)
            header_dict['masses'] = masses

            atoms_coords = []
            atoms_labels = []
            starting_line += num_species
            for idx, atom_line in enumerate(
                data[starting_line:starting_line + num_atoms],
                start=1):
                pieces = atom_line.split()
                if len(pieces) != 5:
                    raise QEOutputParsingError(
                        "Wrong # of elements for one of the atoms: {}, "
                        "line {}: {}".format(
                            len(pieces), starting_line+idx, pieces))
                try:
                    if int(pieces[0]) != idx:
                        raise QEOutputParsingError(
                            "Error with the indices of the atoms: "
                            "{} vs {}".format(int(pieces[0]), idx))
                    sp_idx = int(pieces[1])
                    if sp_idx > len(species):
                        raise QEOutputParsingError("Wrong index for the species: "
                                            "{}, but max={}".format(
                                sp_idx, len(species)))
                    atoms_labels.append(species[sp_idx-1][0])
                    atoms_coords.append([float(pieces[2])*alat,
                                         float(pieces[3])*alat,
                                         float(pieces[4])*alat])
                except ValueError:
                    raise QEOutputParsingError("Error parsing the atoms")
                except IndexError:
                    raise QEOutputParsingError(
                        "Error with the indices in the atoms section")
            header_dict['atoms_labels'] = atoms_labels
            header_dict['atoms_coords'] = atoms_coords
            header_dict['atoms_coords_units'] = "angstrom"
            
            starting_line += num_atoms
            
            starting_line += 1 # Got to the next line to check
            if 'Dynamical' not in data[starting_line]:
                raise QEOutputParsingError(
                    "Wrong format (no 'Dynamical  Matrix' line)")            
            
            ## Here I finish the header parsing

        except QEOutputParsingError as e:
            parsed_data['warnings'].append(
                "Problem parsing the header of the matdyn file! (msg: {}). "
                "Storing only the information I managed to retrieve".format(
                    e.message))
            header_dict['warnings'].append(
                "There was some parsing error and this dictionary is "
                "not complete, see the warnings of the top parsed_data dict")

        # I store what I got
        parsed_data['header'] = header_dict
    
    for line_counter,line in enumerate(data[starting_line:],
                                       start=starting_line):
        if 'q = ' in line:
            # q point is written several times, because it can also be rotated.
            # I consider only the first point, which is the one computed
            if 'q_point' not in parsed_data:
                q_point = [ float(i) for i in line.split('(')[1].split(')')[0].split() ]
                if lattice_parameter:
                    parsed_data['q_point'] = [ e*2*numpy.pi/lattice_parameter for e in q_point]
                    parsed_data['q_point_units'] = 'angstrom-1'
                else:
                    parsed_data['q_point'] = q_point
                    parsed_data['q_point_units'] = '2pi/lattice_parameter'
        
        if 'freq' in line or 'omega' in line:
            this_freq = line.split('[cm-1]')[0].split('=')[-1]
            
            # exception for bad fortran coding: *** could be written instead of the number
            if '*' in this_freq:
                frequencies.append(None)
                parsed_data['warnings'].append('Wrong fortran formatting found while parsing frequencies')
            else:
                frequencies.append( float(this_freq) )
            
            this_eigenvectors = []
            for new_line in data[line_counter+1:]:
                if ('freq' in new_line or 'omega' in new_line or
                    '************************************************'
                    in new_line):
                    break
                this_things = new_line.split('(')[1].split(')')[0].split()
                try:
                    this_flatlist = [float(i) for i in this_things]
                except ValueError:
                    parsed_data['warnings'].append('Wrong fortran formatting found while parsing eigenvectors')
                    # then save the three (xyz) complex numbers as [None,None]
                    this_eigenvectors.append([[None,None]]*3)
                    continue
                
                list_tuples = zip(*[iter(this_flatlist)]*2)
                # I save every complex number as a list of two numbers
                this_eigenvectors.append( [ [i[0],i[1]] for i in list_tuples ] )
                
            eigenvectors.append(this_eigenvectors)
            
    parsed_data['frequencies'] = frequencies
    parsed_data['frequencies_units'] = 'cm-1'
    # TODO: the eigenvectors should be written in the database according to a parser_opts.
    # for now, we don't store them, otherwise we get too much stuff
    # We implement anyway the possibility to get it with an optional parameter
    if also_eigenvectors:
        parsed_data['eigenvectors'] = eigenvectors
    
    return parsed_data



