# -*- coding: utf-8 -*-
"""
A collection of function that are used to parse the output of Quantum Espresso PHonon.
The function that needs to be called from outside is parse_raw_ph_output().
Ideally, the functions should work even without aiida and will return a dictionary with parsed keys.
"""
from xml.dom.minidom import parseString
from aiida.parsers.plugins.quantumespresso.constants import *
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.parsers.plugins.quantumespresso.raw_parser_pw import parse_xml_child_bool,read_xml_card,convert_qe_time_to_sec


__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def parse_raw_ph_output(out_file, tensor_file=None, dynmat_files=[]):
    """
    Parses the output of a calculation
    Receives in input the paths to the output file and the xml file.
    
    Args: 
        out_file 
            path to pw std output
    
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
    out_data = parse_ph_text_output(out_lines)
    
    # TODO: I should have a list of critical warnings rather than hard coded strings!
    if 'Phonon did not reach end of self consistency' in out_data['warnings']:
        job_successful = False
    
    # parse dynamical matrices if present
    dynmat_data = {}
    if dynmat_files:
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
    
    Returns a dictionary with parsed values.
    """
    
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
    
    # TODO: find a list of the common errors of ph
    for line in lines:
        if 'No convergence has been achieved' in line:
            parsed_data['warnings'].append('Phonon did not reach end of self consistency')
    
    return parsed_data

def parse_ph_dynmat(data):
    """
    parses frequencies and eigenvectors of a single dynamical matrix
    data is the text read with the function readlines()
    """
    parsed_data = {}
    parsed_data['warnings'] = []
    
    if 'Dynamical matrix file' not in data[0]:
        raise QEOutputParsingError('Dynamical matrix is not in the expected format') 
        
    frequencies = []
    eigenvectors = []
    
    for line_counter,line in enumerate(data):
        if 'q = ' in line:
            # q point is written several times, because it can also be rotated.
            # I consider only the first point, which is the one computed
            if 'q_point' not in parsed_data:
                parsed_data['q_point'] = [ float(i) for i in line.split('(')[1].split(')')[0].split() ]
        
        if 'freq' in line:
            this_freq = line.split('[cm-1]')[0].split('=')[-1]
            
            # exception for bad fortran coding: *** could be written instead of the number
            if '*' in this_freq:
                frequencies.append(None)
                parsed_data['warnings'].append('Wrong fortran formatting found while parsing frequencies')
            else:
                frequencies.append( float(this_freq) )
            
            this_eigenvectors = []
            for new_line in data[line_counter+1:]:
                if 'freq' in new_line or '************************************************' in new_line:
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
    # TODO: the eigenvectors should be written in the database according to a parser_opts.
    # for now, I don't store them, otherwise I get too much stuff
    #parsed_data['eigenvectors'] = eigenvectors
    
    return parsed_data



