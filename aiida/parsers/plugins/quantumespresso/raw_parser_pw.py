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
A collection of function that are used to parse the output of Quantum Espresso PW.
The function that needs to be called from outside is parse_raw_output().
The functions mostly work without aiida specific functionalities.
The parsing will try to convert whatever it can in some dictionary, which
by operative decision doesn't have much structure encoded, [the values are simple ] 
"""
import xml.dom.minidom
import os
import string
import re
from aiida.parsers.plugins.quantumespresso.constants import ry_to_ev,hartree_to_ev,bohr_to_ang,ry_si,bohr_si
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError

# TODO: it could be possible to use info of the input file to parse output. 
# but atm the output has all the informations needed for the parsing.

# parameter that will be used later for comparisons


lattice_tolerance = 1.e-5

default_energy_units = 'eV'
units_suffix = '_units'
k_points_default_units = '2 pi / Angstrom'
default_length_units = 'Angstrom'
default_dipole_units = 'Debye'
default_magnetization_units = 'Bohrmag / cell'
default_charge_units = 'e'
default_force_units = 'ev / angstrom'
default_stress_units = 'GPascal'
default_polarization_units = 'C / m^2'
       
def parse_raw_output(out_file, input_dict, parser_opts=None, xml_file=None, dir_with_bands=None):
    """
    Parses the output of a calculation
    Receives in input the paths to the output file and the xml file.
    
    :param out_file: path to pw std output
    :param input_dict: dictionary with the input parameters
    :param parser_opts: not used
    :param dir_with_bands: path to directory with all k-points (Kxxxxx) folders
    :param xml_file: path to QE data-file.xml
    
    :return parameter_data: a dictionary with parsed parameters
    :return trajectory_data: a dictionary with arrays (for relax & md calcs.)
    :return structure_data: a dictionary with data for the output structure
    :return bands_data: a dictionary with data for bands (for bands calcs.)
    :return job_successful: a boolean that is False in case of failed calculations
            
    :raises QEOutputParsingError: for errors in the parsing,
    :raises AssertionError: if two keys in the parsed dicts are found to be qual

    3 different keys to check in output: parser_warnings, xml_warnings and warnings.
    On an upper level, these flags MUST be checked.
    The first two are expected to be empty unless QE failures or unfinished jobs.
    """
    import copy
    # TODO: a lot of ifs could be cleaned out
    
    # TODO: input_dict should be used as well
    
    job_successful = True
    
    parser_version = '0.1'
    parser_info = {}
    parser_info['parser_warnings'] = []
    parser_info['parser_info'] = 'AiiDA QE Parser v{}'.format(parser_version)

    # if xml_file is not given in input, skip its parsing
    if xml_file is not None:
        try:
            with open(xml_file,'r') as f:                
                xml_lines = f.read() # Note: read() and not readlines()
        except IOError:
            raise QEOutputParsingError("Failed to open xml file: {}.".format(xml_file))

        xml_data,structure_data,bands_data = parse_pw_xml_output(xml_lines,dir_with_bands)
        # Note the xml file should always be consistent.
    else:
        parser_info['parser_warnings'].append('Skipping the parsing of the xml file.')
        xml_data = {}
        bands_data = {}
        structure_data = {}
    
    # load QE out file
    try:
        with open(out_file,'r') as f:
            out_lines = f.read()
    except IOError: # non existing output file -> job crashed
        raise QEOutputParsingError("Failed to open output file: {}.".format(out_file))

    if not out_lines: # there is an output file, but it's empty -> crash
        job_successful = False
     
    # check if the job has finished (that doesn't mean without errors)
    finished_run = False
    for line in out_lines.split('\n')[::-1]:
        if 'JOB DONE' in line:
            finished_run = True
            break
    if not finished_run: # error if the job has not finished
        warning = 'QE pw run did not reach the end of the execution.'
        parser_info['parser_warnings'].append(warning)        
        job_successful = False

    # parse
    try:
        out_data,trajectory_data,critical_messages = parse_pw_text_output(out_lines,xml_data,structure_data,input_dict)
    except QEOutputParsingError as e:
        if not finished_run: # I try to parse it as much as possible
            parser_info['parser_warnings'].append('Error while parsing the output file')
            out_data = {}
            trajectory_data = {}
            critical_messages = []
        else: # if it was finished and I got error, it's a mistake of the parser
            raise QEOutputParsingError('Error while parsing QE output. Exception message: {}'.format(e.message))
        
    # I add in the out_data all the last elements of trajectory_data values.
    # Safe for some large arrays, that I will likely never query.
    skip_keys = ['forces','atomic_magnetic_moments','atomic_charges',
                 'lattice_vectors_relax','atomic_positions_relax',
                 'atomic_species_name']
    tmp_trajectory_data = copy.copy(trajectory_data)
    for x in tmp_trajectory_data.iteritems():
        if x[0] in skip_keys:
            continue
        out_data[x[0]] = x[1][-1]
        if len(x[1])==1: # delete eventual keys that are not arrays (scf cycles)
            trajectory_data.pop(x[0])
        # note: if an array is empty, there will be KeyError
    for key in ['k_points','k_points_weights']:
        try:
            trajectory_data[key] = xml_data.pop(key)
        except KeyError:
            pass
    # As the k points are an array that is rather large, and again it's not something I'm going to parse likely
    # since it's an info mainly contained in the input file, I move it to the trajectory data

    # if there is a severe error, the calculation is FAILED
    if any([x in out_data['warnings'] for x in critical_messages]):
        job_successful = False

    for key in out_data.keys():
        if key in xml_data.keys():
            if key=='fermi_energy' or key=='fermi_energy_units': # an exception for the (only?) key that may be found on both
                del out_data[key]
            else:
                raise AssertionError('{} found in both dictionaries, '
                                     'values: {} vs. {}'.format(
                                     key, out_data[key], xml_data[key])) # this shouldn't happen!
        # out_data keys take precedence and overwrite xml_data keys,
        # if the same key name is shared by both
        # dictionaries (but this should not happen!)
    parameter_data = dict(xml_data.items() + out_data.items() + parser_info.items())

    # return various data.
    # parameter data will be mapped in ParameterData
    # trajectory_data in ArrayData
    # structure_data in a Structure
    # bands_data should probably be merged in ArrayData    
    return parameter_data,trajectory_data,structure_data,bands_data,job_successful


def cell_volume(a1,a2,a3):
    """
    returns the volume of the primitive cell: ``|a1.(a2xa3)|``
    """
    a_mid_0 = a2[1]*a3[2] - a2[2]*a3[1]
    a_mid_1 = a2[2]*a3[0] - a2[0]*a3[2]
    a_mid_2 = a2[0]*a3[1] - a2[1]*a3[0]
    return abs(float(a1[0]*a_mid_0 + a1[1]*a_mid_1 + a1[2]*a_mid_2))

# In the following, some functions that helps the parsing of
# the xml file of QE v5.0.x (version below not tested)
def read_xml_card(dom,cardname):
    try:
        root_node = [_ for _ in dom.childNodes if 
                    isinstance(_, xml.dom.minidom.Element)
                        and _.nodeName == "Root"][0]
        the_card = [_ for _ in root_node.childNodes if _.nodeName == cardname][0]
        #the_card = dom.getElementsByTagName(cardname)[0]
        return the_card
    except Exception as e:
        print e
        raise QEOutputParsingError('Error parsing tag {}'.format(cardname) )

def parse_xml_child_integer(tagname,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.childNodes[0]
        return int(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}'
                                   .format(tagname,target_tags.tagName) )

def parse_xml_child_float(tagname,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.childNodes[0]
        return float(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}'\
                                   .format(tagname, target_tags.tagName ) )

def parse_xml_child_bool(tagname,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.childNodes[0]
        return str2bool(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}'\
                                   .format(tagname, target_tags.tagName) )

def str2bool(string):
    try:
        false_items=["f","0","false","no"]
        true_items=["t","1","true","yes"]
        string=str(string.lower().strip())
        if string in false_items:
            return False
        if string in true_items:
            return True
        else:
            raise QEOutputParsingError('Error converting string '
                                       '{} to boolean value.'.format(string) )
    except Exception:
        raise QEOutputParsingError('Error converting string to boolean.')

def parse_xml_child_str(tagname,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.childNodes[0]
        return str(b.data).rstrip().replace('\n','')
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}'\
                                   .format(tagname, target_tags.tagName) )

def parse_xml_child_attribute_str(tagname,attributename,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        value=str(a.getAttribute(attributename))
        return value.rstrip().replace('\n','').lower()
    except Exception:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                   .format(attributename,tagname,target_tags.tagName) )

def parse_xml_child_attribute_int(tagname,attributename,target_tags):
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        value=int(a.getAttribute(attributename))
        return value
    except Exception:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                    .format(attributename,tagname,target_tags.tagName) )

def grep_energy_from_line(line):
    try:
        return float(line.split('=')[1].split('Ry')[0])*ry_to_ev
    except Exception:
        raise QEOutputParsingError('Error while parsing energy')
        
def convert_qe_time_to_sec(timestr):
    """
    Given the walltime string of Quantum Espresso, converts it in a number of
    seconds (float).
    """
    rest = timestr.strip()

    if 'd' in rest:
        days, rest = rest.split('d')
    else:
        days = '0'

    if 'h' in rest:
        hours, rest = rest.split('h')
    else:
        hours = '0'

    if 'm' in rest:
        minutes, rest = rest.split('m')
    else:
        minutes = '0'

    if 's' in rest:
        seconds, rest = rest.split('s')
    else:
        seconds = '0.'

    if rest.strip():
        raise ValueError("Something remained at the end of the string '{}': '{}'"
                         .format(timestr, rest))

    num_seconds = (
        float(seconds) + float(minutes) * 60. + 
        float(hours) * 3600. + float(days) * 86400.)

    return num_seconds
 
def convert_list_to_matrix(in_matrix,n_rows,n_columns):
    """
    converts a list into a list of lists (a matrix like) with n_rows and n_columns
    """
    return [ in_matrix[j:j+n_rows] for j in range(0,n_rows*n_columns,n_rows) ]

def xml_card_cell(parsed_data,dom):
    #CARD CELL of QE output
    
    cardname = 'CELL'
    target_tags = read_xml_card(dom,cardname)
    
    for tagname in ['NON-PERIODIC_CELL_CORRECTION','BRAVAIS_LATTICE']:
        parsed_data[tagname.replace('-','_').lower()] = parse_xml_child_str(tagname,target_tags)

    tagname = 'LATTICE_PARAMETER'
    value = parse_xml_child_float(tagname,target_tags)
    parsed_data[tagname.replace('-','_').lower()+'_xml'] = value
    attrname = 'UNITS'
    metric = parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if metric not in ['bohr','angstrom']:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}, units not found'
                                   .format(attrname,tagname,target_tags.tagName) )
    if metric == 'bohr':
        value *= bohr_to_ang
    parsed_data[tagname.replace('-','_').lower()] = value
    
    tagname='CELL_DIMENSIONS'
    try:    
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.childNodes[0]
        c=b.data.replace('\n','').split()
        value=[ float(i) for i in c ]
        parsed_data[tagname.replace('-','_').lower()]=value
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'.format(tagname,target_tags.tagName) )

    tagname = 'DIRECT_LATTICE_VECTORS'
    lattice_vectors = []
    try: 
        second_tagname='UNITS_FOR_DIRECT_LATTICE_VECTORS'
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b=a.getElementsByTagName('UNITS_FOR_DIRECT_LATTICE_VECTORS')[0]
        value=str(b.getAttribute('UNITS')).lower()
        parsed_data[second_tagname.replace('-','_').lower()]=value
        
        metric = value
        if metric not in ['bohr','angstroms']: # REMEMBER TO CHECK THE UNITS AT THE END OF THE FUNCTION
            raise QEOutputParsingError('Error parsing tag {} inside {}: units not supported: {}'
                                       .format(tagname,target_tags.tagName,metric) )

        lattice_vectors = []
        for second_tagname in ['a1','a2','a3']:
            #b = a.getElementsByTagName(second_tagname)[0]
            b=[_ for _ in a.childNodes if _.nodeName == second_tagname][0]
            c = b.childNodes[0]
            d = c.data.replace('\n','').split()
            value = [ float(i) for i in d ]
            if metric=='bohr':
                value = [ bohr_to_ang*float(s) for s in value ]
            lattice_vectors.append(value)
        
        volume = cell_volume(lattice_vectors[0],lattice_vectors[1],lattice_vectors[2])
        
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {} inside {}.'
                                   .format(tagname,target_tags.tagName,cardname) )
    # NOTE: lattice_vectors will be saved later together with card IONS.atom

    tagname = 'RECIPROCAL_LATTICE_VECTORS'
    try:    
        #a = target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        
        second_tagname = 'UNITS_FOR_RECIPROCAL_LATTICE_VECTORS'
        b = a.getElementsByTagName(second_tagname)[0]
        value = str(b.getAttribute('UNITS')).lower()
        parsed_data[second_tagname.replace('-','_').lower()]=value
        
        metric=value
        # NOTE: output is given in 2 pi / a [ang ^ -1]
        if metric not in ['2 pi / a']:
            raise QEOutputParsingError('Error parsing tag {} inside {}: units {} not supported'
                                       .format(tagname,target_tags.tagName,metric) )

        # reciprocal_lattice_vectors
        this_matrix = []
        for second_tagname in ['b1','b2','b3']:
            b = a.getElementsByTagName(second_tagname)[0]
            c = b.childNodes[0]
            d = c.data.replace('\n','').split()
            value = [ float(i) for i in d ]
            if metric == '2 pi / a':
                value=[ float(s)/parsed_data['lattice_parameter'] for s in value ]
            this_matrix.append(value)
        parsed_data['reciprocal_lattice_vectors'] = this_matrix
        
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'
                                   .format(tagname,target_tags.tagName) )
    return parsed_data,lattice_vectors,volume

def xml_card_ions(parsed_data,dom,lattice_vectors,volume):
    cardname='IONS'
    target_tags=read_xml_card(dom,cardname)
    
    for tagname in ['NUMBER_OF_ATOMS','NUMBER_OF_SPECIES']:
        parsed_data[tagname.lower()]=parse_xml_child_integer(tagname,target_tags)
    
    tagname='UNITS_FOR_ATOMIC_MASSES'
    attrname='UNITS'
    parsed_data[tagname.lower()]=parse_xml_child_attribute_str(tagname,attrname,target_tags)

    try:
        parsed_data['species']={}
        parsed_data['species']['index'] =[]
        parsed_data['species']['type']  =[]
        parsed_data['species']['mass']  =[]
        parsed_data['species']['pseudo']=[]
        for i in range(parsed_data['number_of_species']):
            tagname='SPECIE.'+str(i+1)
            parsed_data['species']['index'].append(i+1)

            #a=target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            
            tagname2='ATOM_TYPE'
            parsed_data['species']['type'].append(parse_xml_child_str(tagname2,a))

            tagname2='MASS'
            parsed_data['species']['mass'].append(parse_xml_child_float(tagname2,a))

            tagname2='PSEUDO'
            parsed_data['species']['pseudo'].append(parse_xml_child_str(tagname2,a))

        tagname='UNITS_FOR_ATOMIC_POSITIONS'
        attrname='UNITS'
        parsed_data[tagname.lower()]=parse_xml_child_attribute_str(tagname,attrname,target_tags)
    except:
        raise QEOutputParsingError('Error parsing tag SPECIE.# inside %s.'% (target_tags.tagName ) )
# TODO convert the units
# if parsed_data['units_for_atomic_positions'] not in ['alat','bohr','angstrom']:

    try:
        atomlist=[]
        atoms_index_list=[]
        atoms_if_pos_list=[]
        tagslist=[]
        for i in range(parsed_data['number_of_atoms']):
            tagname='ATOM.'+str(i+1)
            # USELESS AT THE MOMENT, I DON'T SAVE IT
            # parsed_data['atoms']['list_index']=i
            #a=target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            tagname2='INDEX'
            b=int(a.getAttribute(tagname2))
            atoms_index_list.append(b)
            tagname2='SPECIES'

            chem_symbol=str(a.getAttribute(tagname2)).rstrip().replace("\n","")
            # I check if it is a subspecie
            chem_symbol_digits = "".join([i for i in chem_symbol if i in string.digits])
            try:
                tagslist.append(int(chem_symbol_digits))
            except ValueError:
                # If I can't parse the digit, it is probably not there: I add a None to the tagslist
                tagslist.append(None)
            # I remove the symbols
            chem_symbol = chem_symbol.translate(None, string.digits)

            tagname2='tau'
            b = a.getAttribute(tagname2)
            tau = [float(s) for s in b.rstrip().replace("\n","").split()]
            metric = parsed_data['units_for_atomic_positions']
            if metric not in ['alat','bohr','angstrom']: # REMEMBER TO CONVERT AT THE END
                raise QEOutputParsingError('Error parsing tag %s inside %s'% (tagname, target_tags.tagName ) )
            if metric=='alat':
                tau=[ parsed_data['lattice_parameter_xml']*float(s) for s in tau ]
            elif metric=='bohr':
                tau=[ bohr_to_ang*float(s) for s in tau ]
            atomlist.append([chem_symbol,tau])
            tagname2='if_pos'
            b=a.getAttribute(tagname2)
            if_pos=[int(s) for s in b.rstrip().replace("\n","").split()]
            atoms_if_pos_list.append(if_pos)
        parsed_data['atoms']=atomlist
        parsed_data['atoms_index_list']=atoms_index_list
        parsed_data['atoms_if_pos_list']=atoms_if_pos_list
        cell={}
        cell['lattice_vectors']=lattice_vectors
        cell['volume']=volume
        cell['atoms']=atomlist
        cell['tagslist'] = tagslist
        parsed_data['cell']=cell
    except Exception:
        raise QEOutputParsingError('Error parsing tag ATOM.# inside %s.'% (target_tags.tagName ) )
    # saving data together with cell parameters. Did so for better compatibility with ASE.
    
    # correct some units that have been converted in 
    parsed_data['atomic_positions'+units_suffix] = default_length_units
    parsed_data['direct_lattice_vectors'+units_suffix] = default_length_units
        
    return parsed_data

def xml_card_spin(parsed_data,dom):
    cardname='SPIN'
    target_tags=read_xml_card(dom,cardname)

    for tagname in ['LSDA','NON-COLINEAR_CALCULATION',
                    'SPIN-ORBIT_CALCULATION','SPIN-ORBIT_DOMAG']:
        parsed_data[tagname.replace('-','_').lower()
                    ] = parse_xml_child_bool(tagname,target_tags)

    return parsed_data

def xml_card_header(parsed_data,dom):
    cardname='HEADER'
    target_tags=read_xml_card(dom,cardname)
    
    for tagname in ['FORMAT','CREATOR']:
        for attrname in ['NAME','VERSION']:
            parsed_data[(tagname+'_'+attrname).lower()
                        ] = parse_xml_child_attribute_str(tagname,attrname,target_tags)

    return parsed_data

def xml_card_planewaves(parsed_data,dom,calctype):
    if calctype not in ['pw','cp']:
        raise ValueError("Input flag not accepted, must be 'cp' or 'pw'")
    
    cardname='PLANE_WAVES'
    target_tags=read_xml_card(dom,cardname)

    tagname = 'UNITS_FOR_CUTOFF'
    attrname = 'UNITS'
    units = parse_xml_child_attribute_str(tagname,attrname,target_tags).lower()
    if 'hartree' not in units:
        if 'rydberg' not in units:
            raise QEOutputParsingError("Units {} are not supported by parser".format(units))
    else:
        if 'hartree' in units:
            conv_fac = hartree_to_ev
        else:
            conv_fac = ry_to_ev

        tagname='WFC_CUTOFF' 
        parsed_data[tagname.lower()] = parse_xml_child_float(tagname,target_tags)*conv_fac
        parsed_data[tagname.lower()+units_suffix] = default_energy_units
        
        tagname='RHO_CUTOFF' 
        parsed_data[tagname.lower()] = parse_xml_child_float(tagname,target_tags)*conv_fac
        parsed_data[tagname.lower()+units_suffix] = default_energy_units
        
    for tagname in [ 'FFT_GRID','SMOOTH_FFT_GRID' ]:
        grid = []
        for attrname in ['nr1','nr2','nr3']:
            if 'SMOOTH' in tagname:
                attrname += 's'
            grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
        parsed_data[tagname.lower()] = grid

    if calctype == 'cp':

        for tagname in ['MAX_NUMBER_OF_GK-VECTORS','GVECT_NUMBER','SMOOTH_GVECT_NUMBER' ]:
            parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)

        tagname='GAMMA_ONLY' 
        parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)

        tagname='SMALLBOX_FFT_GRID'
        fft_grid = []
        for attrname in ['nr1b','nr2b','nr3b']:
            fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
        parsed_data[tagname.lower()] = fft_grid
        
    return parsed_data

def xml_card_symmetries(parsed_data,dom):
    cardname='SYMMETRIES'
    target_tags=read_xml_card(dom,cardname)

    for tagname in ['NUMBER_OF_SYMMETRIES','NUMBER_OF_BRAVAIS_SYMMETRIES']:
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_integer(tagname,target_tags)
                
    for tagname in ['INVERSION_SYMMETRY','DO_NOT_USE_TIME_REVERSAL',
                    'TIME_REVERSAL_FLAG','NO_TIME_REV_OPERATIONS']:
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='UNITS_FOR_SYMMETRIES'
    attrname='UNITS'
    metric=parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if metric not in ['crystal']:
        raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                                   ' tag {} inside '.format(tagname) + \
                                   '{}, units unknown'.format(target_tags.tagName ) )
    parsed_data['symmetries'+units_suffix] = metric

    # parse the symmetry matrices
    parsed_data['symmetries']=[]
    find_sym=True
    i=0
    while find_sym:
        try:
            i+=1
            current_sym={}
            tagname='SYMM.'+str(i)
            #a=target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            tagname2='INFO'
            b=a.getElementsByTagName(tagname2)[0]
            attrname='NAME'
            value=str(b.getAttribute(attrname)).rstrip().replace('\n','')
            current_sym['name']=value

            try:
                attrname='T_REV'
                value=str(b.getAttribute(attrname)).rstrip().replace('\n','')
                current_sym[attrname.lower()]=value
            except Exception:
                pass

            tagname2='ROTATION'
            b=a.getElementsByTagName(tagname2)[0]
            c=[ int(s) for s in b.childNodes[0].data.split() ]
            current_sym[tagname2.lower()] = convert_list_to_matrix(c,3,3)
                
            for tagname2 in ['FRACTIONAL_TRANSLATION','EQUIVALENT_IONS']: # not always present
                try:
                    b = a.getElementsByTagName(tagname2)[0]
                    if tagname2 == 'FRACTIONAL_TRANSLATION':
                        value = [ float(s) for s in b.childNodes[0].data.split() ]
                    else:
                        value = [ int(s) for s in b.childNodes[0].data.split() ]
                    current_sym[tagname2.lower()] = value
                except Exception:
                    raise

            parsed_data['symmetries'].append(current_sym)
        except IndexError: # SYMM.i out of index
            find_sym=False
                
    return parsed_data

def xml_card_exchangecorrelation(parsed_data,dom):
    cardname='EXCHANGE_CORRELATION'
    target_tags=read_xml_card(dom,cardname)

    tagname='DFT'
    parsed_data[(tagname+'_exchange_correlation').lower()] = \
        parse_xml_child_str(tagname,target_tags)

    tagname='LDA_PLUS_U_CALCULATION'
    try:
        parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)
    except Exception:
        parsed_data[tagname.lower()] = False
    
    if parsed_data[tagname.lower()]: # if it is a plus U calculation, I expect more infos
        tagname = 'HUBBARD_L'
        try:
            #a = target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            b = a.childNodes[0]
            c = b.data.replace('\n','').split()
            value = [int(i) for i in c]
            parsed_data[tagname.lower()] = value
        except Exception:
            raise QEOutputParsingError('Error parsing tag '+\
                                       '{} inside {}.'.format(tagname, target_tags.tagName) )
        
        for tagname in ['HUBBARD_U','HUBBARD_ALPHA','HUBBARD_BETA','HUBBARD_J0']:
            try:
                #a = target_tags.getElementsByTagName(tagname)[0]
                a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
                b = a.childNodes[0]
                c = b.data.replace('\n',' ').split() # note the need of a white space!
                value = [float(i)*ry_to_ev for i in c]
                parsed_data[tagname.lower()] = value
            except Exception:
                raise QEOutputParsingError('Error parsing tag '+\
                                           '{} inside {}.'.format(tagname, target_tags.tagName))
        
        tagname = 'LDA_PLUS_U_KIND'
        try:
            parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)
        except Exception:
            pass

        tagname = 'U_PROJECTION_TYPE'
        try:
            parsed_data[tagname.lower()] = parse_xml_child_str(tagname,target_tags)
        except Exception:
            pass

        tagname = 'HUBBARD_J'
        try:
            #a=target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            b=a.childNodes[0]
            c=b.data.replace('\n','').split()
            parsed_data[tagname.lower()] = convert_list_to_matrix(c,3,3)
        except Exception:
            pass
    
    try:
        tagname='NON_LOCAL_DF'
        parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)
    except Exception:
        pass

    try:
        tagname='VDW_KERNEL_NAME'
        parsed_data[tagname.lower()] = parse_xml_child_str(tagname,target_tags)
    except Exception:
        pass

    return parsed_data

def parse_pw_xml_output(data,dir_with_bands=None):
    """
    Parse the xml data of QE v5.0.x
    Input data must be a single string, as returned by file.read()
    Returns a dictionary with parsed values
    """
    import copy
    from xml.parsers.expat import ExpatError
    # NOTE : I often assume that if the xml file has been written, it has no
    # internal errors.
    try:
        dom = xml.dom.minidom.parseString(data)
    except ExpatError:
        return {'xml_warnings':"Error in XML parseString: bad format"},{},{}
    
    parsed_data = {}
    
    parsed_data['xml_warnings'] = []
    
    structure_dict = {}
    # CARD CELL
    structure_dict,lattice_vectors,volume = copy.deepcopy(xml_card_cell(structure_dict,dom))

    # CARD IONS
    structure_dict = copy.deepcopy(xml_card_ions(structure_dict,dom,lattice_vectors,volume))
    
    #CARD HEADER
    parsed_data = copy.deepcopy(xml_card_header(parsed_data,dom))
    
    # CARD CONTROL
    cardname='CONTROL'
    target_tags=read_xml_card(dom,cardname)
    for tagname in ['PP_CHECK_FLAG','LKPOINT_DIR',
                    'Q_REAL_SPACE','BETA_REAL_SPACE']:
        parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)

    # TODO: why this one isn't working? What is it actually?
#    # CARD MOVING_CELL
#
#    try:
#        target_tags = dom.getElementsByTagName('MOVING_CELL')[0]
#    except:
#        raise IOError
#
#    tagname='CELL_FACTOR'
#    parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)
    
    # CARD ELECTRIC_FIELD
    cardname='ELECTRIC_FIELD'
    target_tags=read_xml_card(dom,cardname)
    for tagname in ['HAS_ELECTRIC_FIELD','HAS_DIPOLE_CORRECTION']:
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)
        
    if parsed_data['has_electric_field'] or parsed_data['has_dipole_correction']:
        tagname='FIELD_DIRECTION'
        parsed_data[tagname.lower()]=parse_xml_child_integer(tagname,target_tags)
        
        for tagname in ['MAXIMUM_POSITION','INVERSE_REGION','FIELD_AMPLITUDE']:
            parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)

    # CARD PLANE_WAVES
    parsed_data = copy.deepcopy(xml_card_planewaves(parsed_data,dom,'pw'))
    
    # CARD SPIN
    parsed_data = copy.deepcopy(xml_card_spin(parsed_data,dom))

    # CARD BRILLOUIN ZONE
    cardname='BRILLOUIN_ZONE'
    target_tags=read_xml_card(dom,cardname)

    tagname='NUMBER_OF_K-POINTS'
    parsed_data[tagname.replace('-','_').lower()] = parse_xml_child_integer(tagname,target_tags)

    tagname = 'UNITS_FOR_K-POINTS'
    attrname = 'UNITS'
    metric = parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if metric not in ['2 pi / a']:
        raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                ' tag {} inside {}, units unknown'.format(tagname, target_tags.tagName) )
    k_points_units = metric

    for tagname, param in [ ['MONKHORST_PACK_GRID','nk'],['MONKHORST_PACK_OFFSET','k'] ]:
        try:
            #a = target_tags.getElementsByTagName(tagname)[0]
            a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            value = [int(a.getAttribute(param+str(i+1))) for i in range(3)]
            parsed_data[tagname.replace('-','_').lower()] = value
        except Exception: # I might not use the monkhorst pack grid
            pass

    
    kpoints = []
    kpoints_weights = []
    
    tagname_prefix = 'K-POINT.'
    a_dict={_.nodeName: _ for _ in target_tags.childNodes
            if _.nodeName.startswith(tagname_prefix)}
    
    try:
        import numpy
        for i in range(parsed_data['number_of_k_points']):
            tagname = "{}{}".format(tagname_prefix,i+1)
            #a = target_tags.getElementsByTagName(tagname)[0]
            a=a_dict[tagname]
            b = a.getAttribute('XYZ').replace('\n','').rsplit()
            value = [ float(s) for s in b ]
            
            metric = k_points_units
            if metric=='2 pi / a':
                value = [ 2.*numpy.pi*float(s)/structure_dict['lattice_parameter'] for s in value ]
                weight = float(a.getAttribute('WEIGHT'))                
                kpoints.append(value)
                kpoints_weights.append(weight)
        parsed_data['k_points']=kpoints
        parsed_data['k_points'+units_suffix] = k_points_default_units
        parsed_data['k_points_weights'] = kpoints_weights
    except Exception:
        raise QEOutputParsingError('Error parsing tag K-POINT.{} '
                                   'inside {}.'.format(i+1,target_tags.tagName) )


    # I skip this card until someone will have a need for this. 
#     try:
#         tagname='STARTING_K-POINTS'
#         num_starting_k_points=parse_xml_child_integer(tagname,target_tags)
#         # raise exception if there is no such a key
#         parsed_data[tagname.replace('-','_').lower()]=num_starting_k_points
# 
#         if parsed_data.get('starting_k_points'):
#             try:
#                 kpoints=[]
#                 for i in range(parsed_data['starting_k_points']):
#                     tagname='K-POINT_START.'+str(i+1)
#                     a=target_tags.getElementsByTagName(tagname)[0]
#                     b=a.getAttribute('XYZ').replace('\n','').rsplit()
#                     value=[ float(s) for s in b ]
#                     metric=parsed_data['k_points_units']
#                     if metric=='2 pi / a':
#                         value=[ float(s)/parsed_data['lattice_parameter'] for s in value ]
# 
#                         weight=float(a.getAttribute('WEIGHT'))
# 
#                         kpoints.append([value,weight])
# 
#                 parsed_data['k_point_start']=kpoints
#             except Exception:
#                 raise QEOutputParsingError('Error parsing tag {}'.format(tagname)+\
#                                            ' inside {}.'.format(target_tags.tagName ) )
#     except Exception:
#         if not parsed_data.get('starting_k_points'):
#             pass
#         else:
#             parsed_data['xml_warnings'].append("Warning: could not parse {}".format(tagname))

    # tagname='NORM-OF-Q'
    # TODO: decide if save this parameter
    # parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_float(tagname,target_tags)
    
    # CARD BAND STRUCTURE INFO
    cardname = 'BAND_STRUCTURE_INFO'
    target_tags = read_xml_card(dom,cardname)

    for tagname in ['NUMBER_OF_SPIN_COMPONENTS','NUMBER_OF_ATOMIC_WFC','NUMBER_OF_BANDS']:
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_integer(tagname,target_tags)
    
    tagname='NON-COLINEAR_CALCULATION'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_bool(tagname,target_tags)

    tagname='NUMBER_OF_ELECTRONS'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_float(tagname,target_tags)

    tagname = 'UNITS_FOR_ENERGIES'
    attrname = 'UNITS'
    units = parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if units not in ['hartree']:
        raise QEOutputParsingError('Expected energy units in Hartree.' + \
                                   'Got instead {}'.format(parsed_data['energy_units']) )
    
    try:
        tagname='TWO_FERMI_ENERGIES'
        parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)
    except Exception:
        pass

    if parsed_data.get('two_fermi_energies',False):
        tagname = 'FERMI_ENERGY_UP'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_float(tagname,target_tags) * hartree_to_ev
        parsed_data[tagname.lower()+units_suffix] = default_energy_units
        tagname = 'FERMI_ENERGY_DOWN'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_float(tagname,target_tags) * hartree_to_ev
        parsed_data[tagname.lower()+units_suffix] = default_energy_units        
    else:
        tagname = 'FERMI_ENERGY'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_float(tagname,target_tags) * hartree_to_ev
        parsed_data[tagname.lower()+units_suffix] = default_energy_units
        
    #CARD MAGNETIZATION_INIT
    cardname = 'MAGNETIZATION_INIT'
    target_tags = read_xml_card(dom,cardname)

    # 0 if false
    tagname='CONSTRAINT_MAG'
    parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)
    
    vec1 = []
    vec2 = []
    vec3 = []
    for i in range(structure_dict['number_of_species']):
        tagname='SPECIE.'+str(i+1)
        #a=target_tags.getElementsByTagName(tagname)[0]
        a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        tagname2='STARTING_MAGNETIZATION'
        vec1.append(parse_xml_child_float(tagname2,a))
        tagname2='ANGLE1'
        vec2.append(parse_xml_child_float(tagname2,a))
        tagname2='ANGLE2'
        vec3.append(parse_xml_child_float(tagname2,a))
    parsed_data['starting_magnetization'] = vec1
    parsed_data['magnetization_angle1'] = vec2
    parsed_data['magnetization_angle2'] = vec3
    
    #CARD OCCUPATIONS
    cardname = 'OCCUPATIONS'
    target_tags = read_xml_card(dom,cardname)
    for tagname in ['SMEARING_METHOD','TETRAHEDRON_METHOD','FIXED_OCCUPATIONS']:
        parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)
    
    #CARD CHARGE-DENSITY
    cardname='CHARGE-DENSITY'
    target_tags=read_xml_card(dom,cardname)
    try:
        attrname='iotk_link'
        value=str(target_tags.getAttribute(attrname)).rstrip().replace('\n','').lower()
        parsed_data[cardname.lower().rstrip().replace('-','_')]=value
    except Exception:
        raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                                   ' card {}.'.format(cardname))
    
    #CARD EIGENVALUES
    # Note: if this card is parsed, the dimension of the database grows very much!
    cardname='EIGENVALUES'
    target_tags=read_xml_card(dom,cardname)
    bands_dict = {}
    if dir_with_bands:
        try:
            occupations1 = []
            occupations2 = []
            bands1 = []
            bands2 = []
            for i in range(parsed_data['number_of_k_points']):
                tagname='K-POINT.'+str(i+1)
                #a=target_tags.getElementsByTagName(tagname)[0]
                a=[_ for _ in target_tags.childNodes if _.nodeName == tagname][0]

                def read_bands_and_occupations(eigenval_n):
                    # load the eigenval.xml file
                    with open(eigenval_n,'r') as eigenval_f:
                        f = eigenval_f.read()
                        
                    eig_dom = xml.dom.minidom.parseString(f)
                    
                    tagname = 'UNITS_FOR_ENERGIES'
                    a = eig_dom.getElementsByTagName(tagname)[0]
                    attrname = 'UNITS'
                    metric = str(a.getAttribute(attrname))
                    if metric not in ['Hartree']:
                        raise QEOutputParsingError('Error parsing eigenvalues xml file, ' + \
                                                   'units {} not implemented.'.format(metric))
                    
                    tagname='EIGENVALUES'
                    a=eig_dom.getElementsByTagName(tagname)[0]
                    b=a.childNodes[0]
                    value_e = [ float(s)*hartree_to_ev for s in b.data.split() ]
                    
                    tagname='OCCUPATIONS'
                    a = eig_dom.getElementsByTagName(tagname)[0]
                    b = a.childNodes[0]
                    value_o = [ float(s) for s in b.data.split() ]
                    return value_e,value_o
            
                # two cases: in cases of magnetic calculations, I have both spins    
                try:
                    tagname2 = 'DATAFILE'
                    b = a.getElementsByTagName(tagname2)[0]
                    attrname = 'iotk_link'
                    value = str(b.getAttribute(attrname)).rstrip().replace('\n','')
                    eigenval_n =  os.path.join(dir_with_bands,value)

                    value_e,value_o = read_bands_and_occupations(eigenval_n)
                    bands1.append(value_e)
                    occupations1.append(value_o)
                    
                except IndexError:
                    tagname2='DATAFILE.1'
                    b1 = a.getElementsByTagName(tagname2)[0]
                    tagname2='DATAFILE.2'
                    b2 = a.getElementsByTagName(tagname2)[0]
                    attrname = 'iotk_link'
                    value1 = str(b1.getAttribute(attrname)).rstrip().replace('\n','')
                    value2 = str(b2.getAttribute(attrname)).rstrip().replace('\n','')
                    
                    eigenval_n =  os.path.join(dir_with_bands,value1)
                    value_e,value_o = read_bands_and_occupations(eigenval_n)
                    bands1.append(value_e)
                    occupations1.append(value_o)

                    eigenval_n =  os.path.join(dir_with_bands,value2)
                    value_e,value_o = read_bands_and_occupations(eigenval_n)
                    bands2.append(value_e)
                    occupations2.append(value_o)

            occupations = [occupations1]
            bands = [bands1]
            if occupations2:
                occupations.append(occupations2)
            if bands2:
                bands.append(bands2)
            
            bands_dict['occupations'] = occupations
            bands_dict['bands'] = bands
            bands_dict['bands'+units_suffix] = default_energy_units
        except Exception:
            raise QEOutputParsingError('Error parsing card {}'.format(tagname))

#     if dir_with_bands:
#         # if there is at least an empty band:
#         if parsed_data['smearing_method'] or  \
#            parsed_data['number_of_electrons']/2. < parsed_data['number_of_bands']:
#             
#             #TODO: currently I do it only for non magnetic systems
#             if len(bands_dict['occupations'])==1:
#             # initialize lumo
#                 lumo = parsed_data['homo']+10000.0
#                 for list_bands in bands_dict['bands']:
#                     for value in list_bands:
#                         if (value > parsed_data['fermi_energy']) and (value<lumo):
#                             lumo=value
#                 if (lumo==parsed_data['homo']+10000.0) or lumo<=parsed_data['fermi_energy']:
#                     #might be an error for bandgap larger than 10000 eV...
#                     raise QEOutputParsingError('Error while searching for LUMO.')
#                 parsed_data['lumo']=lumo
#                 parsed_data['lumo'+units_suffix] = default_energy_units
    
    # CARD symmetries
    parsed_data = copy.deepcopy(xml_card_symmetries(parsed_data,dom))
    
    # CARD EXCHANGE_CORRELATION
    parsed_data = copy.deepcopy(xml_card_exchangecorrelation(parsed_data,dom))
    
    return parsed_data,structure_dict,bands_dict

def parse_pw_text_output(data, xml_data={}, structure_data={}, input_dict={}):
    """
    Parses the text output of QE-PWscf.
    
    :param data: a string, the file as read by read()
    :param xml_data: the dictionary with the keys read from xml.
    :param structure_data: dictionary, coming from the xml, with info on the structure
    :param input_dict: dictionary with the input parameters
    
    :return parsed_data: dictionary with key values, referring to quantities 
                         at the last scf step.
    :return trajectory_data: key,values referring to intermediate scf steps, 
                             as in the case of vc-relax. Empty dictionary if no
                             value is present.
    :return critical_messages: a list with critical messages. If any is found in
                               parsed_data['warnings'], the calculation is FAILED!
    """
    # Separate the input string into separate lines
    data_lines = data.split('\n')
    
    parsed_data = {}
    parsed_data['warnings'] = []
    vdw_correction = False
    trajectory_data = {}
    
    # critical warnings: if any is found, the calculation status is FAILED
    critical_warnings = {'The maximum number of steps has been reached.':"The maximum step of the ionic/electronic relaxation has been reached.",
                         'convergence NOT achieved after':"The scf cycle did not reach convergence.",
                         #'eigenvalues not converged':None, # special treatment
                         'iterations completed, stopping':'Maximum number of iterations reached in Wentzcovitch Damped Dynamics.',
                         'Maximum CPU time exceeded':'Maximum CPU time exceeded',
                         '%%%%%%%%%%%%%%':None,
                         }
    
    minor_warnings = {'Warning:':None,
                      'DEPRECATED:':None,
                      'incommensurate with FFT grid':'The FFT is incommensurate: some symmetries may be lost.',
                      'SCF correction compared to forces is too large, reduce conv_thr':"Forces are inaccurate (SCF correction is large): reduce conv_thr.",
                      }
    
    all_warnings = dict(critical_warnings.items() + minor_warnings.items())

    # Find some useful quantities.
    if not xml_data.get('number_of_bands',None) and not structure_data:
        try:
            for line in data.split('\n'):
                if 'lattice parameter (alat)' in line:
                    alat = float(line.split('=')[1].split('a.u')[0])
                elif 'number of atoms/cell' in line:
                    nat = int(line.split('=')[1])
                elif 'number of atomic types' in line:
                    ntyp = int(line.split('=')[1])
                elif 'unit-cell volume' in line:
                    volume = float(line.split('=')[1].split('(a.u.)^3')[0])
                elif 'number of Kohn-Sham states' in line:
                    nbnd = int(line.split('=')[1])
                elif "number of k points" in line:
                    nk = int(line.split('=')[1].split()[0])
                    if input_dict.get('SYSTEM',{}).get('nspin',1) > 1:
                        # QE counts twice each k-point in spin-polarized calculations
                        nk /= 2
                elif "Dense  grid" in line:
                    FFT_grid = [int(g) for g in 
                                line.split('(')[1].split(')')[0].split(',')]
                elif "Smooth grid" in line:
                    smooth_FFT_grid = [int(g) for g in 
                                       line.split('(')[1].split(')')[0].split(',')]
                    break
            alat *= bohr_to_ang
            volume *= bohr_to_ang**3
            parsed_data['lattice_parameter_initial'] = alat
            parsed_data['warnings'].append('Xml data not found: parsing only the text output')
            parsed_data['number_of_bands'] = nbnd
            try:
                parsed_data['number_of_k_points'] = nk
                parsed_data['fft_grid'] = FFT_grid
                parsed_data['smooth_fft_grid'] = smooth_FFT_grid
            except NameError:
                # these are not crucial, so parsing does not fail if they are not found
                pass
        except NameError: # nat or other variables where not found, and thus not initialized
            # try to get some error message
            for count,line in enumerate(data.split('\n')):
                if any( i in line for i in all_warnings):
                    messages = [ all_warnings[i] if all_warnings[i] is not None 
                                    else line for i in all_warnings.keys() 
                                    if i in line]
                                                       
                    if '%%%%%%%%%%%%%%' in line:
                        messages = parse_QE_errors(data.split('\n'),count,
                                                   parsed_data['warnings']) 
                                
                    # if it found something, add to log
                    if len(messages)>0:
                        parsed_data['warnings'].extend(messages)

            if len(parsed_data['warnings'])>0:
                return parsed_data, trajectory_data, critical_warnings.values()
            else:
                # did not find any error message -> raise an Error and do not 
                # return anything
                raise QEOutputParsingError("Parser can't load basic info.")
    else:
        nat = structure_data['number_of_atoms']
        ntyp = structure_data['number_of_species']
        nbnd = xml_data['number_of_bands']
        alat = structure_data['lattice_parameter_xml']
        volume = structure_data['cell']['volume']
    # NOTE: lattice_parameter_xml is the lattice parameter of the xml file
    # in the units used by the code. lattice_parameter instead in angstroms.
    
    # Save these two quantities in the parsed_data, because they will be 
    # useful for queries (maybe), and structure_data will not be stored as a ParameterData
    parsed_data['number_of_atoms'] = nat
    parsed_data['number_of_species'] = ntyp
    times_strings = ['h_psi','s_psi','cdiaghg']
    times_strings += ['fft','fft_scatter', 'init_run']
    times_strings += ['wfcinit','c_bands']

    parsed_data['volume'] = volume
    
    c_bands_error = False
    
    # now grep quantities that can be considered isolated informations.
    for count,line in enumerate(data_lines):
        
        bool_time = [any(re.findall('\\b{}\\b'.format(i), line)) for i in times_strings]
        # to be used for later
        if 'Carrying out vdW-DF run using the following parameters:' in line:
            vdw_correction=True
            
#        # single information only. To check that is not an info of the input already.
#        elif 'EXX-fraction' in line:
#            parsed_data['exx_fraction'] = float( line.split()[-1] )

        elif 'Cartesian axes' in line:
            # this is the part when initial positions and chemical
            # symbols are printed (they do not change during a run)
            i = count+1
            while i<count+10 and not('site n.' in data_lines[i] and 
                                      'atom' in data_lines[i]):
                i += 1
            if 'site n.' in data_lines[i] and 'atom' in data_lines[i]:
                trajectory_data['atomic_species_name'] = \
                    [data_lines[i+1+j].split()[1] for j in range(nat)]
            
        # parse the initialization time (take only first occurence)
        elif ('init_wall_time_seconds' not in parsed_data
              and "total cpu time spent up to now is" in line):
            init_time = float(line.split("total cpu time spent up to now is"
                                         )[1].split('secs')[0])
            parsed_data['init_wall_time_seconds'] = init_time

        # parse the global file, for informations that are written only once
        elif 'PWSCF' in line and 'WALL' in line:
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data['wall_time'] = time
            except Exception:
                parsed_data['warnings'].append('Error while parsing wall time.')                
            try:
                parsed_data['wall_time_seconds'] = convert_qe_time_to_sec(time)
            except ValueError:
                raise QEOutputParsingError("Unable to convert wall_time in seconds.")

        elif any(bool_time) and 'WALL' in line:
            bindex = bool_time.index(True)
            bstring = times_strings[bindex] + '_time'
            bstring_seconds= times_strings[bindex] + '_time_seconds'
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data[bstring] = time
            except Exception:
                error_string = 'Error while parsing ' + times_strings[bindex]
                parsed_data['warnings'].append(error_string)                
            try:
                parsed_data[bstring_seconds] = convert_qe_time_to_sec(time)
            except ValueError:
                error_string = 'Unable to convert ' + times_strings[bindex] + ' seconds'
                parsed_data['warnings'].append(error_string)                
 

        
        elif 'SUMMARY OF PHASES' in line:
            try:
                j = 0
                while True:
                    j+=1
                    if 'Ionic Phase' in data_lines[count+j]:                        
                        value = float(data_lines[count+j].split(':')[1].split('(')[0])
                        mod = int(data_lines[count+j].split('(mod')[1].split(')')[0])
                        if mod != 2:
                            raise QEOutputParsingError("Units for polarization phase not supported")
                        parsed_data['ionic_phase'] = value
                        parsed_data['ionic_phase'+units_suffix] = '2pi'

                    if 'Electronic Phase' in data_lines[count+j]:
                        value = float(data_lines[count+j].split(':')[1].split('(')[0])
                        mod = int(data_lines[count+j].split('(mod')[1].split(')')[0])
                        if mod != 2:
                            raise QEOutputParsingError("Units for polarization phase not supported")
                        parsed_data['electronic_phase'] = value
                        parsed_data['electronic_phase'+units_suffix] = '2pi'
                        
                    if 'Total Phase' in data_lines[count+j]:
                        value = float(data_lines[count+j].split(':')[1].split('(')[0])
                        mod = int(data_lines[count+j].split('(mod')[1].split(')')[0])
                        if mod != 2:
                            raise QEOutputParsingError("Units for polarization phase not supported")
                        parsed_data['total_phase'] = value
                        parsed_data['total_phase'+units_suffix] = '2pi'

                    # TODO: decide a standard unit for e charge
                    if "C/m^2" in data_lines[count+j]:
                        value = float(data_lines[count+j].split('=')[1].split('(')[0])
                        mod = float(data_lines[count+j].split('mod')[1].split(')')[0])
                        units = data_lines[count+j].split(')')[1].strip() 
                        parsed_data['polarization'] = value
                        parsed_data['polarization_module'] = mod
                        parsed_data['polarization'+units_suffix] = default_polarization_units
                        if 'C / m^2' not in default_polarization_units:
                            raise  QEOutputParsingError("Units for polarization phase not supported")

                    if 'polarization direction' in data_lines[count+j]: 
                        vec = [ float(s) for s in \
                                data_lines[count+j].split('(')[1].split(')')[0].split(',') ]
                        parsed_data['polarization_direction'] = vec
                        
            except Exception:
                warning = 'Error while parsing polarization.'
                parsed_data['warnings'].append(warning)     

        # for later control on relaxation-dynamics convergence
        elif 'nstep' in line and '=' in line:
            max_dynamic_iterations = int(line.split()[2])
            
        elif 'point group' in line:
            if 'k-point group' not in line:
                try:
                    # Split line in components delimited by either space(s) or
                    # parenthesis and filter out empty strings
                    line_elems = filter(None, re.split(' +|\(|\)', line))

                    pg_international = line_elems[-1]
                    pg_schoenflies = line_elems[-2]

                    parsed_data['pointgroup_international'] = pg_international
                    parsed_data['pointgroup_schoenflies'] = pg_schoenflies

                except Exception:
                    warning = "Problem parsing point group, I found: {}".format(line.strip())
                    parsed_data['warnings'].append(warning)
        
        # special parsing of c_bands error        
        elif 'c_bands' in line and 'eigenvalues not converged' in line:
            c_bands_error = True

        elif "iteration #" in line:
            if ( ("Calculation restarted" not in line) and 
                 ("Calculation stopped" not in line) ):
                try:
                    parsed_data['total_number_of_scf_iterations'] += 1
                except KeyError:
                    parsed_data['total_number_of_scf_iterations'] = 1

            if c_bands_error:
                # if there is another iteration, c_bands is not necessarily a problem
                # I put a warning only if c_bands error appears in the last iteration
                c_bands_error = False
        
        # Parsing of errors
        elif any( i in line for i in all_warnings):
            message = [ all_warnings[i] for i in all_warnings.keys() if i in line][0]
            if message is None:
                message = line
                
            # if the run is a molecular dynamics, I ignore that I reached the 
            # last iteration step.
            if ('The maximum number of steps has been reached.' in line and 
                'md' in input_dict.get('CONTROL',{}).get('calculation','')):
                message = None
                
            if 'iterations completed, stopping' in line:
                value = message
                message = None
                if 'Wentzcovitch Damped Dynamics:' in line:
                    dynamic_iterations = int(line.split()[3])
                    if max_dynamic_iterations == dynamic_iterations:
                        message = value
                        
#             if 'c_bands' and 'eigenvalues not converged' in line:
#                 # even if some bands are not converged, this is a problem only
#                 # if it happens at the last scf step
#                 # start a loop to find the end of scf step
#                 # if another iteration is found, no warning is needed
#                 doloop = True  
#                 j = 0
#                 while doloop:
#                     line2 = data.split('\n')[count+j]
#                     if "iteration #" in line2:
#                         doloop = False
#                         message = None
#                     if "End of self-consistent calculation" in line2:
#                         doloop = False # to prevent going until the end of file
#                     j += 1
#                     print count+j
                    
            if '%%%%%%%%%%%%%%' in line:
                message  = None
                messages = parse_QE_errors(data_lines,count,parsed_data['warnings']) 
                        
            # if it found something, add to log
            try:
                parsed_data['warnings'].extend(messages)
            except UnboundLocalError:
                pass
            if message is not None:
                parsed_data['warnings'].append(message)

    if c_bands_error:
        parsed_data['warnings'].append("c_bands: at least 1 eigenvalues not converged")


    # I split the output text in the atomic SCF calculations.
    # the initial part should be things already contained in the xml.
    # (cell, initial positions, kpoints, ...) and I skip them.
    # In case, parse for them before this point.
    # Put everything in a trajectory_data dictionary
    relax_steps = data.split('Self-consistent Calculation')[1:]
    relax_steps = [ i.split('\n') for i in relax_steps]
    
    
    # now I create a bunch of arrays for every step.    
    for data_step in relax_steps:
        for count,line in enumerate(data_step):
            
            if 'CELL_PARAMETERS' in line:
                try:
                    a1 = [float(s) for s in data_step[count+1].split()]
                    a2 = [float(s) for s in data_step[count+2].split()]
                    a3 = [float(s) for s in data_step[count+3].split()]
                    # try except indexerror for not enough lines
                    lattice = line.split('(')[1].split(')')[0].split('=')
                    if lattice[0].lower() not in ['alat','bohr','angstrom']:
                        raise QEOutputParsingError('Error while parsing cell_parameters: '+\
                                                   'unsupported units {}'.format(lattice[0]) )

                    if 'alat' in lattice[0].lower():
                        a1 = [ alat*bohr_to_ang*float(s) for s in a1 ]
                        a2 = [ alat*bohr_to_ang*float(s) for s in a2 ]
                        a3 = [ alat*bohr_to_ang*float(s) for s in a3 ]
                        lattice_parameter_b = float(lattice[1])
                        if abs(lattice_parameter_b - alat) > lattice_tolerance:
                            raise QEOutputParsingError("Lattice parameters mismatch! " + \
                                                       "{} vs {}".format(lattice_parameter_b, alat))
                    elif 'bohr' in lattice[0].lower():
                        lattice_parameter_b*=bohr_to_ang
                        a1 = [ bohr_to_ang*float(s) for s in a1 ]
                        a2 = [ bohr_to_ang*float(s) for s in a2 ]
                        a3 = [ bohr_to_ang*float(s) for s in a3 ]
                    try:
                        trajectory_data['lattice_vectors_relax'].append([a1,a2,a3])
                    except KeyError:
                        trajectory_data['lattice_vectors_relax'] = [[a1,a2,a3]]
                        
                except Exception:
                    parsed_data['warnings'].append('Error while parsing relaxation cell parameters.')

            elif 'ATOMIC_POSITIONS' in line:
                try:
                    this_key = 'atomic_positions_relax'
                    #this_key_2 = 'atomic_species_name'
                    # the inizialization of tau prevent parsed_data to be associated
                    # to the pointer of the previous iteration
                    metric = line.split('(')[1].split(')')[0]
                    if metric not in ['alat','bohr','angstrom']:
                        raise QEOutputParsingError('Error while parsing atomic_positions:'
                                                   ' units not supported.')
                    # TODO: check how to map the atoms in the original scheme
                    positions = []
                    #chem_symbols = []
                    for i in range(nat):
                        line2 = data_step[count+1+i].split()
                        tau = [float(s) for s in line2[1:4]]
                        #chem_symbol = str(line2[0]).rstrip()
                        if metric == 'alat':
                            tau = [ alat*float(s) for s in tau ]
                        elif metric == 'bohr':
                            tau = [ bohr_to_ang*float(s) for s in tau ]
                        positions.append(tau)
                        #chem_symbols.append(chem_symbol)
                    try:
                        trajectory_data[this_key].append(positions)
                    except KeyError:
                        trajectory_data[this_key] = [positions]
                    #trajectory_data[this_key_2] = chem_symbols # the symbols do not change during a run
                except Exception:
                    parsed_data['warnings'].append('Error while parsing relaxation atomic positions.')

            # NOTE: in the above, the chemical symbols are not those of AiiDA
            # since the AiiDA structure is different. So, I assume now that the
            # order of atoms is the same of the input atomic structure. 
            
            # Computed dipole correction in slab geometries.
            # save dipole in debye units, only at last iteration of scf cycle
            elif 'Computed dipole along edir' in line:
                j = count+3
                line2 = data_step[j]
                try:
                    units = line2.split()[-1]
                    if default_dipole_units.lower() not in units.lower(): # only debye
                       raise QEOutputParsingError("Error parsing the dipole correction."
                                                      " Units {} are not supported.".format(units))
                    value = float(line2.split()[-2])
                except IndexError: # on units
                    pass   
                # save only the last dipole correction    
                while 'Computed dipole along edir' not in line2:
                    j += 1
                    try: 
                        line2 = data_step[j]
                    except IndexError: # The dipole is also written at the beginning of a new bfgs iteration
                        break
                    if 'End of self-consistent calculation' in line2:
                        try:
                            trajectory_data['dipole'].append( value )
                        except KeyError:
                            trajectory_data['dipole'] = [value]
                        parsed_data['dipole'+units_suffix] = default_dipole_units
                        break

            elif ('convergence has been achieved in' in line
                  or 'convergence NOT achieved after' in line):
                try:
                    scf_iterations = int(line.split("iterations")[0].split()[-1])
                    try:
                        trajectory_data['scf_iterations'].append(scf_iterations)
                    except KeyError:
                        trajectory_data['scf_iterations'] = [scf_iterations]
                except Exception:
                    parsed_data['warnings'].append('Error while parsing scf iterations.')
            
            elif 'End of self-consistent calculation' in line:
                # parse energy threshold for diagonalization algorithm
                try:
                    j = 0
                    while True:
                        j -= 1
                        line2 = data_step[count+j]
                        if 'ethr' in line2:
                            value = float(line2.split('=')[1].split(',')[0])
                            break
                    try:
                        trajectory_data['energy_threshold'].append(value)
                    except KeyError:
                        trajectory_data['energy_threshold'] = [value]
                except Exception:
                    parsed_data['warnings'].append('Error while parsing ethr.')
                
                # parse final magnetic moments, if present
                try:
                    j = 0
                    while True:
                        j -= 1
                        line2 = data_step[count+j]
                        if 'Magnetic moment per site' in line2:
                            break
                        if 'iteration' in line2:
                            raise QEOutputParsingError
                    mag_moments = []
                    charges = []
                    while True:
                        j += 1
                        line2 = data_step[count+j]
                        if 'atom:' in line2:
                            mag_moments.append(float(line2.split('magn:')[1].split()[0]))
                            charges.append(float(line2.split('charge:')[1].split()[0]))
                        if len(mag_moments)==nat:
                            break
                    try:
                        trajectory_data['atomic_magnetic_moments'].append(mag_moments)
                        trajectory_data['atomic_charges'].append(charges)
                    except KeyError:
                        trajectory_data['atomic_magnetic_moments'] = [mag_moments]
                        trajectory_data['atomic_charges'] = [charges]
                    parsed_data['atomic_magnetic_moments'+units_suffix] = default_magnetization_units
                    parsed_data['atomic_charges'+units_suffix] = default_charge_units
                except QEOutputParsingError:
                    pass
            
            # grep energy and possibly, magnetization
            elif '!' in line:
                try:
                    for key in ['energy','energy_accuracy']:
                        if key not in trajectory_data:
                            trajectory_data[key] = []
                    
                    En = float(line.split('=')[1].split('Ry')[0])*ry_to_ev
                    E_acc = float(data_step[count+2].split('<')[1].split('Ry')[0])*ry_to_ev
                    
                    for key,value in [['energy',En],['energy_accuracy',E_acc]]:
                        trajectory_data[key].append(value)
                        parsed_data[key+units_suffix] = default_energy_units
                    # TODO: decide units for magnetization. now bohr mag/cell
                    j = 0
                    while True:
                        j+=1
                        line2 = data_step[count+j]
                        
                        for string,key in [
                            ['one-electron contribution','energy_one_electron'],
                            ['hartree contribution','energy_hartree'],
                            ['xc contribution','energy_xc'],
                            ['ewald contribution','energy_ewald'],
                            ['smearing contrib.','energy_smearing'],
                            ['one-center paw contrib.','energy_one_center_paw'],
                            ['est. exchange err','energy_est_exchange'],
                            ['Fock energy','energy_fock'],
                            # Add also ENVIRON specific contribution to the total energy
                            ['solvation energy','energy_solvation'],
                            ['cavitation energy','energy_cavitation'],
                            ['PV energy', 'energy_pv'],
                            ['periodic energy correct.','energy_pbc_correction'],
                            ['ionic charge energy','energy_ionic_charge'],
                            ['external charges energy','energy_external_charges']
                            ]:
                            if string in line2:
                                value = grep_energy_from_line(line2)
                                try:
                                    trajectory_data[key].append(value)
                                except KeyError:
                                    trajectory_data[key] = [value]
                                parsed_data[key+units_suffix] = default_energy_units
                        # magnetizations
                        if 'total magnetization' in line2:
                            this_m = line2.split('=')[1].split('Bohr')[0]
                            try: # magnetization might be a scalar
                                value = float(this_m)
                            except ValueError: # but can also be a three vector component in non-collinear calcs
                                value = [ float(i) for i in this_m.split() ]
                            try:
                                trajectory_data['total_magnetization'].append(value)
                            except KeyError:
                                trajectory_data['total_magnetization'] = [value]
                            parsed_data['total_magnetization'+units_suffix] = default_magnetization_units
                        elif 'absolute magnetization' in line2:
                            value=float(line2.split('=')[1].split('Bohr')[0])
                            try:
                                trajectory_data['absolute_magnetization'].append(value)
                            except KeyError:
                                trajectory_data['absolute_magnetization'] = [value]
                            parsed_data['absolute_magnetization'+units_suffix] = default_magnetization_units
                        # exit loop
                        elif 'convergence' in line2:
                            break
                            
                    if vdw_correction:
                        j=0
                        while True:
                            j+=-1
                            line2 = data_step[count+j]
                            if 'Non-local correlation energy' in line2:
                                value = grep_energy_from_line(line2)
                                try:
                                    trajectory_data['energy_vdw'].append(value)
                                except KeyError:
                                    trajectory_data['energy_vdw'] = [value]
                                break
                        parsed_data['energy_vdw'+units_suffix] = default_energy_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing for energy terms.')

            elif 'the Fermi energy is' in line:
                try:
                    value = float(line.split('is')[1].split('ev')[0])
                    try:
                        trajectory_data['fermi_energy'].append(value)
                    except KeyError:
                        trajectory_data['fermi_energy'] = [value]
                    parsed_data['fermi_energy'+units_suffix] = default_energy_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing Fermi energy from the output file.')


            elif 'Forces acting on atoms (Ry/au):' in line:
                try:
                    forces = []
                    j = 0
                    while True:
                        j+=1
                        line2 = data_step[count+j]
                        if 'atom ' in line2:
                            line2 = line2.split('=')[1].split()
                            # CONVERT FORCES IN eV/Ang
                            vec = [ float(s)*ry_to_ev / \
                                   bohr_to_ang for s in line2 ]
                            forces.append(vec)
                        if len(forces)==nat:
                            break
                    try:
                        trajectory_data['forces'].append(forces)
                    except KeyError:
                        trajectory_data['forces'] = [forces]
                    parsed_data['forces'+units_suffix] = default_force_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing forces.')
                
            # TODO: adding the parsing support for the decomposition of the forces
            
            elif 'Total force =' in line:
                try: # note that I can't check the units: not written in output!
                    value = float(line.split('=')[1].split('Total')[0])*ry_to_ev/bohr_to_ang
                    try:
                        trajectory_data['total_force'].append(value)
                    except KeyError:
                        trajectory_data['total_force'] = [value]
                    parsed_data['total_force'+units_suffix] = default_force_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing total force.')
        
            elif 'entering subroutine stress ...' in line:
                try:
                    stress = []
                    for k in range (10+5*vdw_correction):
                        if "P=" in data_step[count+k+1]:
                            count2 = count+k+1
                    if '(Ry/bohr**3)' not in data_step[count2]:
                        raise QEOutputParsingError('Error while parsing stress: unexpected units.')
                    for k in range(3):
                        line2 = data_step[count2+k+1].split()
                        vec = [ float(s)*10**(-9)*ry_si/(bohr_si)**3 for s in line2[0:3] ]
                        stress.append(vec)
                    try:
                        trajectory_data['stress'].append(stress)
                    except KeyError:
                        trajectory_data['stress'] = [stress]
                    parsed_data['stress'+units_suffix] = default_stress_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing stress tensor.')

    return parsed_data, trajectory_data, critical_warnings.values()

def parse_QE_errors(lines,count,warnings):
    """
    Parse QE errors messages (those appearing between some lines with
    ``%%%%%%%%``)
    :param lines: list of strings, the output text file as read by readlines()
    or as obtained by data.split('\\n') when data is the text file read by read()
    :param count: the line at which we identified some ``%%%%%%%%``
    :param warnings: the warnings already parsed in the file
    :return messages: a list of QE error messages
    """
    
#    PREVIOUS VERSION
#    TODO: suppress it when we are sure the new one is working in all cases
#    # find the indices of the lines with problems
#    found_endpoint = False
#    init_problem = count
#    for count2,line2 in enumerate(lines[count+1:]):
#        end_problem = count + count2 + 1
#        if "%%%%%%%%%%%%" in line2:
#            found_endpoint = True
#            break
#    if not found_endpoint:
#        message = None
#    else:
#        # build a dictionary with the lines
#        prob_list = lines[init_problem:end_problem+1]
#        irred_list = list(set(prob_list))
#        message = ""
#        for v in prob_list:
#            if v in irred_list:
#                #irred_list.pop(v)
#                message += irred_list.pop(irred_list.index(v)) + '\n'  
#    return [message]

    # find the indices of the lines with problems
    found_endpoint = False
    init_problem = count
    for count2,line2 in enumerate(lines[count+1:]):
        end_problem = count + count2 + 1
        if "%%%%%%%%%%%%" in line2:
            found_endpoint = True
            break
    messages = []
    if found_endpoint:
        # build a dictionary with the lines
        prob_list = lines[init_problem:end_problem+1]
        irred_list = list(set(prob_list))
        for v in prob_list:
            if ( len(v)>0 and (v in irred_list and v not in warnings) ):
                messages.append(irred_list.pop(irred_list.index(v)))  

    return messages
