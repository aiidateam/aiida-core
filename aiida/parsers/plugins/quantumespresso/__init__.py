# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.parsers.exceptions import OutputParsingError



class QEOutputParsingError(OutputParsingError):
    """
    Exception raised by a parser error in a QE code
    """
    pass
    # def __init__(self,message):
    # wrappedmessage = "Error parsing Quantum Espresso PW output: " + message
    #     super(QEOutputParsingError,self).__init__(wrappedmessage)
    #     self.message = wrappedmessage
    #     self.module = "qe-pw"


def convert_qe2aiida_structure(output_dict, input_structure=None):
    """
    Receives the dictionary cell parsed from quantum espresso
    Convert it into an AiiDA structure object
    """
    from aiida.orm import DataFactory

    StructureData = DataFactory('structure')

    cell_dict = output_dict['cell']

    # If I don't have any help, I will set up the cell as it is in QE
    if not input_structure:

        s = StructureData(cell=cell_dict['lattice_vectors'])
        for atom in cell_dict['atoms']:
            s.append_atom(position=tuple(atom[1]), symbols=[atom[0]])

    else:

        s = input_structure.copy()
        s.reset_cell(cell_dict['lattice_vectors'])
        new_pos = [i[1] for i in cell_dict['atoms']]
        s.reset_sites_positions(new_pos)

    return s

def parse_raw_out_basic(out_file, calc_name):
    """
    A very simple parser for the standard out, usually aiida.out. Currently
    only parses basic warnings and the walltime.
    :param out_file: the standard out to be parsed
    :param calc_name: the name of the calculation, e.g. PROJWFC
    :return: parsed_data
    """

    # read file
    parsed_data = {}
    parsed_data['warnings'] = []
    # critical warnings: if any is found, the calculation status is FAILED
    critical_warnings = {'Maximum CPU time exceeded':'Maximum CPU time exceeded',
                         '%%%%%%%%%%%%%%':None,
                         }

    minor_warnings = {'Warning:':None,
                      'DEPRECATED:':None,
                      }
    all_warnings = dict(critical_warnings.items() + minor_warnings.items())
    for count in range (len(out_file)):
        line = out_file[count]
        # parse the global file, for informations that are written only once
        if calc_name in line and 'WALL' in line:
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data['wall_time'] = time
            except ValueError:
                parsed_data['warnings'].append('Error while parsing wall time.')
            try:
                parsed_data['wall_time_seconds'] = convert_qe_time_to_sec(time)
            except ValueError:
                raise QEOutputParsingError("Unable to convert wall_time in seconds.")
            # Parsing of errors
        elif any( i in line for i in all_warnings):
            message = [ all_warnings[i] for i in all_warnings.keys() if i in line][0]
            if message is None:
                message = line
            if '%%%%%%%%%%%%%%' in line:
                message  = None
                messages = parse_QE_errors(out_file,count,parsed_data['warnings'])

            # if it found something, add to log
            try:
                parsed_data['warnings'].extend(messages)
            except UnboundLocalError:
                pass
            if message is not None:
                parsed_data['warnings'].append(message)

    return parsed_data

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

def ldlparse_QE_errors(lines,count,warnings):
    """
    Parse QE errors messages, i.e., those appearing between some lines
    with ``%%%%%%%%``

    :param lines: list of strings, the output text file as read by readlines()
      or as obtained by ``data.split('\\n')`` when data is the text file read by
      read()
    :param count: the line at which we identified some ``%%%%%%%%``
    :param warnings: the warnings already parsed in the file
    :return messages: a list of QE error messages
    """

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


def parse_QE_errors(lines,count,warnings):
    """
    Parse QE errors messages, i.e., those appearing between some lines 
    with ``%%%%%%%%``

    :param lines: list of strings, the output text file as read by readlines()
      or as obtained by ``data.split('\\n')`` when data is the text file read by read()
    :param count: the line at which we identified some ``%%%%%%%%``
    :param warnings: the warnings already parsed in the file
    :return messages: a list of QE error messages
    """

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
