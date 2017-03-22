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
from aiida.parsers.plugins.quantumespresso.constants import ry_to_ev, hartree_to_ev, bohr_to_ang, ry_si, bohr_si
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
default_force_units = 'ev / angstrom'
default_stress_units = 'GPascal'
default_polarization_units = 'C / m^2'


def parse_raw_output(out_file, input_dict, parser_opts=None, xml_file=None, dir_with_bands=None):
    """
    Parses the output of a calculation
    Receives in input the paths to the output file and the xml file.
    
    :param out_file: path to pw std output
    :param input_dict: not used
    :param parser_opts: not used
    :param dir_with_bands: path to directory with all k-points (Kxxxxx) folders
    :param xml_file: path to QE data-file.xml
    
    :returns out_dict: a dictionary with parsed data
    :return successful: a boolean that is False in case of failed calculations
            
    :raises aiida.parsers.plugins.quantumespresso.QEOutputParsingError: for errors in the parsing,
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
    parser_info['parser_info'] = 'AiiDA QE Basic Parser v{}'.format(parser_version)

    # if xml_file is not given in input, skip its parsing
    if xml_file is not None:
        try:
            with open(xml_file, 'r') as f:
                xml_lines = f.read()  # Note: read() and not readlines()
        except IOError:
            raise QEOutputParsingError("Failed to open xml file: {}.".format(xml_file))

        xml_data, structure_data = parse_pw_xml_output(xml_lines, dir_with_bands)
        # Note the xml file should always be consistent.
    else:
        parser_info['parser_warnings'].append('Skipping the parsing of the xml file.')
        xml_data = {}
        bands_data = {}
        structure_data = {}

    # load QE out file
    try:
        with open(out_file, 'r') as f:
            out_lines = f.read()
    except IOError:  # non existing output file -> job crashed
        raise QEOutputParsingError("Failed to open output file: {}.".format(out_file))

    if not out_lines:  # there is an output file, but it's empty -> crash
        job_successful = False

    # check if the job has finished (that doesn't mean without errors)
    finished_run = False
    for line in out_lines.split('\n')[::-1]:
        if 'JOB DONE' in line:
            finished_run = True
            break
    if not finished_run:  # error if the job has not finished
        warning = 'QE pw run did not reach the end of the execution.'
        parser_info['parser_warnings'].append(warning)
        job_successful = False

    # parse
    try:
        out_data, trajectory_data, critical_messages = parse_pw_text_output(out_lines, xml_data, structure_data,
                                                                            input_dict)
    except QEOutputParsingError:
        if not finished_run:  # I try to parse it as much as possible
            parser_info['parser_warnings'].append('Error while parsing the output file')
            out_data = {}
            trajectory_data = {}
            critical_messages = []
        else:  # if it was finished and I got error, it's a mistake of the parser
            raise QEOutputParsingError('Error while parsing QE output')

    # I add in the out_data all the last elements of trajectory_data values.
    # Safe for some large arrays, that I will likely never query.
    skip_keys = ['forces', 'lattice_vectors_relax',
                 'atomic_positions_relax', 'atomic_species_name']
    tmp_trajectory_data = copy.copy(trajectory_data)
    for x in tmp_trajectory_data.iteritems():
        if x[0] in skip_keys:
            continue
        out_data[x[0]] = x[1][-1]
        if len(x[1]) == 1:  # delete eventual keys that are not arrays (scf cycles)
            trajectory_data.pop(x[0])
            # note: if an array is empty, there will be KeyError
    for key in ['k_points', 'k_points_weights']:
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
            if key == 'fermi_energy' or key == 'fermi_energy_units':  # an exception for the (only?) key that may be found on both
                del out_data[key]
            else:
                raise AssertionError('{} found in both dictionaries, '
                                     'values: {} vs. {}'.format(
                    key, out_data[key], xml_data[key]))  # this shouldn't happen!
                # out_data keys take precedence and overwrite xml_data keys,
                # if the same key name is shared by both
                # dictionaries (but this should not happen!)
    parameter_data = dict(xml_data.items() + out_data.items() + parser_info.items())

    # return various data.
    # parameter data will be mapped in ParameterData
    # trajectory_data in ArrayData
    # structure_data in a Structure
    # bands_data should probably be merged in ArrayData    
    return parameter_data, trajectory_data, structure_data, job_successful


def cell_volume(a1, a2, a3):
    """
    returns the volume of the primitive cell: \|a1.(a2xa3)\|
    """
    a_mid_0 = a2[1] * a3[2] - a2[2] * a3[1]
    a_mid_1 = a2[2] * a3[0] - a2[0] * a3[2]
    a_mid_2 = a2[0] * a3[1] - a2[1] * a3[0]
    return abs(float(a1[0] * a_mid_0 + a1[1] * a_mid_1 + a1[2] * a_mid_2))


# In the following, some functions that helps the parsing of
# the xml file of QE v5.0.x (version below not tested)
def read_xml_card(dom, cardname):
    try:
        root_node = [_ for _ in dom.childNodes if
                     isinstance(_, xml.dom.minidom.Element)
                     and _.nodeName == "Root"][0]
        the_card = [_ for _ in root_node.childNodes if _.nodeName == cardname][0]
        # the_card = dom.getElementsByTagName(cardname)[0]
        return the_card
    except Exception as e:
        print e
        raise QEOutputParsingError('Error parsing tag {}'.format(cardname))


def parse_xml_child_integer(tagname, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.childNodes[0]
        return int(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}'
                                   .format(tagname, target_tags.tagName))


def parse_xml_child_float(tagname, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.childNodes[0]
        return float(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}' \
                                   .format(tagname, target_tags.tagName))


def parse_xml_child_bool(tagname, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.childNodes[0]
        return str2bool(b.data)
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}' \
                                   .format(tagname, target_tags.tagName))


def str2bool(string):
    try:
        false_items = ["f", "0", "false", "no"]
        true_items = ["t", "1", "true", "yes"]
        string = str(string.lower().strip())
        if string in false_items:
            return False
        if string in true_items:
            return True
        else:
            raise QEOutputParsingError('Error converting string '
                                       '{} to boolean value.'.format(string))
    except Exception:
        raise QEOutputParsingError('Error converting string to boolean.')


def parse_xml_child_str(tagname, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.childNodes[0]
        return str(b.data).rstrip().replace('\n', '')
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}' \
                                   .format(tagname, target_tags.tagName))


def parse_xml_child_attribute_str(tagname, attributename, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        value = str(a.getAttribute(attributename))
        return value.rstrip().replace('\n', '').lower()
    except Exception:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                   .format(attributename, tagname, target_tags.tagName))


def parse_xml_child_attribute_int(tagname, attributename, target_tags):
    try:
        # a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        value = int(a.getAttribute(attributename))
        return value
    except Exception:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                   .format(attributename, tagname, target_tags.tagName))


def grep_energy_from_line(line):
    try:
        return float(line.split('=')[1].split('Ry')[0]) * ry_to_ev
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


def convert_list_to_matrix(in_matrix, n_rows, n_columns):
    """
    converts a list into a list of lists (a matrix like) with n_rows and n_columns
    """
    return [in_matrix[j:j + n_rows] for j in range(0, n_rows * n_columns, n_rows)]


def xml_card_cell(parsed_data, dom):
    # CARD CELL of QE output

    cardname = 'CELL'
    target_tags = read_xml_card(dom, cardname)

    for tagname in ['NON-PERIODIC_CELL_CORRECTION', 'BRAVAIS_LATTICE']:
        parsed_data[tagname.replace('-', '_').lower()] = parse_xml_child_str(tagname, target_tags)

    tagname = 'LATTICE_PARAMETER'
    value = parse_xml_child_float(tagname, target_tags)
    parsed_data[tagname.replace('-', '_').lower() + '_xml'] = value
    attrname = 'UNITS'
    metric = parse_xml_child_attribute_str(tagname, attrname, target_tags)
    if metric not in ['bohr', 'angstrom']:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}, units not found'
                                   .format(attrname, tagname, target_tags.tagName))
    if metric == 'bohr':
        value *= bohr_to_ang
    parsed_data[tagname.replace('-', '_').lower()] = value

    tagname = 'CELL_DIMENSIONS'
    try:
        #a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.childNodes[0]
        c = b.data.replace('\n', '').split()
        value = [float(i) for i in c]
        parsed_data[tagname.replace('-', '_').lower()] = value
    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'.format(tagname, target_tags.tagName))

    tagname = 'DIRECT_LATTICE_VECTORS'
    lattice_vectors = []
    try:
        second_tagname = 'UNITS_FOR_DIRECT_LATTICE_VECTORS'
        #a=target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
        b = a.getElementsByTagName('UNITS_FOR_DIRECT_LATTICE_VECTORS')[0]
        value = str(b.getAttribute('UNITS')).lower()
        parsed_data[second_tagname.replace('-', '_').lower()] = value

        metric = value
        if metric not in ['bohr', 'angstroms']:  # REMEMBER TO CHECK THE UNITS AT THE END OF THE FUNCTION
            raise QEOutputParsingError('Error parsing tag {} inside {}: units not supported: {}'
                                       .format(tagname, target_tags.tagName, metric))

        lattice_vectors = []
        for second_tagname in ['a1', 'a2', 'a3']:
            #b = a.getElementsByTagName(second_tagname)[0]
            b = [_ for _ in a.childNodes if _.nodeName == second_tagname][0]
            c = b.childNodes[0]
            d = c.data.replace('\n', '').split()
            value = [float(i) for i in d]
            if metric == 'bohr':
                value = [bohr_to_ang * float(s) for s in value]
            lattice_vectors.append(value)

        volume = cell_volume(lattice_vectors[0], lattice_vectors[1], lattice_vectors[2])

    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {} inside {}.'
                                   .format(tagname, target_tags.tagName, cardname))
    # NOTE: lattice_vectors will be saved later together with card IONS.atom

    tagname = 'RECIPROCAL_LATTICE_VECTORS'
    try:
        #a = target_tags.getElementsByTagName(tagname)[0]
        a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]

        second_tagname = 'UNITS_FOR_RECIPROCAL_LATTICE_VECTORS'
        b = a.getElementsByTagName(second_tagname)[0]
        value = str(b.getAttribute('UNITS')).lower()
        parsed_data[second_tagname.replace('-', '_').lower()] = value

        metric = value
        # NOTE: output is given in 2 pi / a [ang ^ -1]
        if metric not in ['2 pi / a']:
            raise QEOutputParsingError('Error parsing tag {} inside {}: units {} not supported'
                                       .format(tagname, target_tags.tagName, metric))

        # reciprocal_lattice_vectors
        this_matrix = []
        for second_tagname in ['b1', 'b2', 'b3']:
            b = a.getElementsByTagName(second_tagname)[0]
            c = b.childNodes[0]
            d = c.data.replace('\n', '').split()
            value = [float(i) for i in d]
            if metric == '2 pi / a':
                value = [float(s) / parsed_data['lattice_parameter'] for s in value]
            this_matrix.append(value)
        parsed_data['reciprocal_lattice_vectors'] = this_matrix

    except Exception:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'
                                   .format(tagname, target_tags.tagName))
    return parsed_data, lattice_vectors, volume


def xml_card_ions(parsed_data, dom, lattice_vectors, volume):
    cardname = 'IONS'
    target_tags = read_xml_card(dom, cardname)

    for tagname in ['NUMBER_OF_ATOMS', 'NUMBER_OF_SPECIES']:
        parsed_data[tagname.lower()] = parse_xml_child_integer(tagname, target_tags)

    tagname = 'UNITS_FOR_ATOMIC_MASSES'
    attrname = 'UNITS'
    parsed_data[tagname.lower()] = parse_xml_child_attribute_str(tagname, attrname, target_tags)

    try:
        parsed_data['species'] = {}
        parsed_data['species']['index'] = []
        parsed_data['species']['type'] = []
        parsed_data['species']['mass'] = []
        parsed_data['species']['pseudo'] = []
        for i in range(parsed_data['number_of_species']):
            tagname = 'SPECIE.' + str(i + 1)
            parsed_data['species']['index'].append(i + 1)

            # a=target_tags.getElementsByTagName(tagname)[0]
            a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]

            tagname2 = 'ATOM_TYPE'
            parsed_data['species']['type'].append(parse_xml_child_str(tagname2, a))

            tagname2 = 'MASS'
            parsed_data['species']['mass'].append(parse_xml_child_float(tagname2, a))

            tagname2 = 'PSEUDO'
            parsed_data['species']['pseudo'].append(parse_xml_child_str(tagname2, a))

        tagname = 'UNITS_FOR_ATOMIC_POSITIONS'
        attrname = 'UNITS'
        parsed_data[tagname.lower()] = parse_xml_child_attribute_str(tagname, attrname, target_tags)
    except:
        raise QEOutputParsingError('Error parsing tag SPECIE.# inside %s.' % (target_tags.tagName ))
    # TODO convert the units
    # if parsed_data['units_for_atomic_positions'] not in ['alat','bohr','angstrom']:

    try:
        atomlist = []
        atoms_index_list = []
        atoms_if_pos_list = []
        tagslist = []
        for i in range(parsed_data['number_of_atoms']):
            tagname = 'ATOM.' + str(i + 1)
            # USELESS AT THE MOMENT, I DON'T SAVE IT
            # parsed_data['atoms']['list_index']=i
            # a=target_tags.getElementsByTagName(tagname)[0]
            a = [_ for _ in target_tags.childNodes if _.nodeName == tagname][0]
            tagname2 = 'INDEX'
            b = int(a.getAttribute(tagname2))
            atoms_index_list.append(b)
            tagname2 = 'SPECIES'

            chem_symbol = str(a.getAttribute(tagname2)).rstrip().replace("\n", "")
            # I check if it is a subspecie
            chem_symbol_digits = "".join([i for i in chem_symbol if i in string.digits])
            try:
                tagslist.append(int(chem_symbol_digits))
            except ValueError:
                # If I can't parse the digit, it is probably not there: I add a None to the tagslist
                tagslist.append(None)
            # I remove the symbols
            chem_symbol = chem_symbol.translate(None, string.digits)

            tagname2 = 'tau'
            b = a.getAttribute(tagname2)
            tau = [float(s) for s in b.rstrip().replace("\n", "").split()]
            metric = parsed_data['units_for_atomic_positions']
            if metric not in ['alat', 'bohr', 'angstrom']:  # REMEMBER TO CONVERT AT THE END
                raise QEOutputParsingError('Error parsing tag %s inside %s' % (tagname, target_tags.tagName ))
            if metric == 'alat':
                tau = [parsed_data['lattice_parameter_xml'] * float(s) for s in tau]
            elif metric == 'bohr':
                tau = [bohr_to_ang * float(s) for s in tau]
            atomlist.append([chem_symbol, tau])
            tagname2 = 'if_pos'
            b = a.getAttribute(tagname2)
            if_pos = [int(s) for s in b.rstrip().replace("\n", "").split()]
            atoms_if_pos_list.append(if_pos)
        parsed_data['atoms'] = atomlist
        parsed_data['atoms_index_list'] = atoms_index_list
        parsed_data['atoms_if_pos_list'] = atoms_if_pos_list
        cell = {}
        cell['lattice_vectors'] = lattice_vectors
        cell['volume'] = volume
        cell['atoms'] = atomlist
        cell['tagslist'] = tagslist
        parsed_data['cell'] = cell
    except Exception:
        raise QEOutputParsingError('Error parsing tag ATOM.# inside %s.' % (target_tags.tagName ))
    # saving data together with cell parameters. Did so for better compatibility with ASE.

    # correct some units that have been converted in 
    parsed_data['atomic_positions' + units_suffix] = default_length_units
    parsed_data['direct_lattice_vectors' + units_suffix] = default_length_units

    return parsed_data


def parse_pw_xml_output(data, dir_with_bands=None):
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
        return {'xml_warnings': "Error in XML parseString: bad format"}, {}, {}

    parsed_data = {}

    parsed_data['xml_warnings'] = []

    structure_dict = {}
    # CARD CELL
    structure_dict, lattice_vectors, volume = copy.deepcopy(xml_card_cell(structure_dict, dom))

    # CARD IONS
    structure_dict = copy.deepcopy(xml_card_ions(structure_dict, dom, lattice_vectors, volume))

    # fermi energy

    cardname = 'BAND_STRUCTURE_INFO'
    target_tags = read_xml_card(dom, cardname)

    tagname = 'FERMI_ENERGY'
    parsed_data[tagname.replace('-', '_').lower()] = \
        parse_xml_child_float(tagname, target_tags) * hartree_to_ev
    parsed_data[tagname.lower() + units_suffix] = default_energy_units

    return parsed_data, structure_dict


def parse_pw_text_output(data, xml_data=None, structure_data=None, input_dict=None):
    """
    Parses the text output of QE-PWscf.
    
    :param data: a string, the file as read by read()
    :param xml_data: the dictionary with the keys read from xml.
    :param structure_data: dictionary, coming from the xml, with info on the structure
    
    :return parsed_data: dictionary with key values, referring to quantities 
                         at the last scf step.
    :return trajectory_data: key,values referring to intermediate scf steps, 
                             as in the case of vc-relax. Empty dictionary if no
                             value is present.
    :return critical_messages: a list with critical messages. If any is found in
                               parsed_data['warnings'], the calculation is FAILED!
    """

    parsed_data = {}
    parsed_data['warnings'] = []
    vdw_correction = False
    trajectory_data = {}

    # critical warnings: if any is found, the calculation status is FAILED
    critical_warnings = {
    'The maximum number of steps has been reached.': "The maximum step of the ionic/electronic relaxation has been reached.",
    'convergence NOT achieved after': "The scf cycle did not reach convergence.",
    # 'eigenvalues not converged':None, # special treatment
    'iterations completed, stopping': 'Maximum number of iterations reached in Wentzcovitch Damped Dynamics.',
    'Maximum CPU time exceeded': 'Maximum CPU time exceeded',
    '%%%%%%%%%%%%%%': None,
    }

    minor_warnings = {'Warning:': None,
                      'DEPRECATED:': None,
                      'incommensurate with FFT grid': 'The FFT is incommensurate: some symmetries may be lost.',
                      'SCF correction compared to forces is too large, reduce conv_thr': "Forces are inaccurate (SCF correction is large): reduce conv_thr.",
    }

    all_warnings = dict(critical_warnings.items() + minor_warnings.items())

    # Find some useful quantities.
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
                break
        alat *= bohr_to_ang
        volume *= bohr_to_ang ** 3
        parsed_data['number_of_bands'] = nbnd
    except NameError:  # nat or other variables where not found, and thus not initialized
        # try to get some error message
        for count, line in enumerate(data.split('\n')):
            if any(i in line for i in all_warnings):
                messages = [all_warnings[i] if all_warnings[i] is not None
                            else line for i in all_warnings.keys()
                            if i in line]

                if '%%%%%%%%%%%%%%' in line:
                    messages = parse_QE_errors(data.split('\n'), count,
                                               parsed_data['warnings'])

                    # if it found something, add to log
                if len(messages) > 0:
                    parsed_data['warnings'].extend(messages)

        if len(parsed_data['warnings']) > 0:
            return parsed_data, trajectory_data, critical_warnings.values()
        else:
            # did not find any error message -> raise an Error and do not 
            # return anything
            raise QEOutputParsingError("Parser can't load basic info.")

    # Save these two quantities in the parsed_data, because they will be 
    # useful for queries (maybe), and structure_data will not be stored as a ParameterData
    parsed_data['number_of_atoms'] = nat
    parsed_data['number_of_species'] = ntyp
    parsed_data['volume'] = volume

    c_bands_error = False

    # now grep quantities that can be considered isolated informations.
    for count, line in enumerate(data.split('\n')):

        # special parsing of c_bands error
        if 'c_bands' in line and 'eigenvalues not converged' in line:
            c_bands_error = True
        elif "iteration #" in line and c_bands_error:
            # if there is another iteration, c_bands is not necessarily a problem
            # I put a warning only if c_bands error appears in the last iteration
            c_bands_error = False

        # Parsing of errors
        elif any(i in line for i in all_warnings):
            message = [all_warnings[i] for i in all_warnings.keys() if i in line][0]
            if message is None:
                message = line

            # if the run is a molecular dynamics, I ignore that I reached the 
            # last iteration step.
            if ('The maximum number of steps has been reached.' in line and
                        'md' in input_dict['CONTROL']['calculation']):
                message = None

            if 'iterations completed, stopping' in line:
                value = message
                message = None
                if 'Wentzcovitch Damped Dynamics:' in line:
                    dynamic_iterations = int(line.split()[3])
                    if max_dynamic_iterations == dynamic_iterations:
                        message = value

            if '%%%%%%%%%%%%%%' in line:
                message = None
                messages = parse_QE_errors(data.split('\n'), count, parsed_data['warnings'])

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
    relax_steps = [i.split('\n') for i in relax_steps]


    # now I create a bunch of arrays for every step.    
    for data_step in relax_steps:
        for count, line in enumerate(data_step):

            # NOTE: in the above, the chemical symbols are not those of AiiDA
            # since the AiiDA structure is different. So, I assume now that the
            # order of atoms is the same of the input atomic structure. 

            # Computed dipole correction in slab geometries.
            # save dipole in debye units, only at last iteration of scf cycle

            # grep energy and eventually, magnetization
            if '!' in line:                
                if 'makov-payne' in line.lower():
                    try:
                        for key in ['total','envir']:
                            if key in line.lower():                                
                                En = float(line.split('=')[1].split('Ry')[0]) * ry_to_ev
                                try:
                                    trajectory_data[key+'_makov-payne'].append(En)
                                except KeyError:
                                    trajectory_data[key+'_makov-payne'] = [En]
                                    parsed_data[key +'_makov-payne'+ units_suffix] = default_energy_units
                    except Exception:
                        parsed_data['warnings'].append('Error while parsing the energy')
                else:    
                    try:
                        for key in ['energy', 'energy_accuracy']:
                            if key not in trajectory_data:
                                trajectory_data[key] = []

                        En = float(line.split('=')[1].split('Ry')[0]) * ry_to_ev
                        E_acc = float(data_step[count + 2].split('<')[1].split('Ry')[0]) * ry_to_ev

                        for key, value in [['energy', En], ['energy_accuracy', E_acc]]:
                            trajectory_data[key].append(value)
                            parsed_data[key + units_suffix] = default_energy_units
                    except Exception:
                        parsed_data['warnings'].append('Error while parsing the energy')

            elif 'the Fermi energy is' in line:
                try:
                    value = line.split('is')[1].split('ev')[0]
                    try:
                        trajectory_data['fermi_energy'].append(value)
                    except KeyError:
                        trajectory_data['fermi_energy'] = [value]
                    parsed_data['fermi_energy' + units_suffix] = default_energy_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing Fermi energy from the output file.')

            elif 'Forces acting on atoms (Ry/au):' in line:
                try:
                    forces = []
                    j = 0
                    while True:
                        j += 1
                        line2 = data_step[count + j]
                        if 'atom ' in line2:
                            line2 = line2.split('=')[1].split()
                            # CONVERT FORCES IN eV/Ang
                            vec = [float(s) * ry_to_ev / \
                                   bohr_to_ang for s in line2]
                            forces.append(vec)
                        if len(forces) == nat:
                            break
                    try:
                        trajectory_data['forces'].append(forces)
                    except KeyError:
                        trajectory_data['forces'] = [forces]
                    parsed_data['forces' + units_suffix] = default_force_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing forces.')

            # TODO: adding the parsing support for the decomposition of the forces

            elif 'Total force =' in line:
                try:  # note that I can't check the units: not written in output!
                    value = float(line.split('=')[1].split('Total')[0]) * ry_to_ev / bohr_to_ang
                    try:
                        trajectory_data['total_force'].append(value)
                    except KeyError:
                        trajectory_data['total_force'] = [value]
                    parsed_data['total_force' + units_suffix] = default_force_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing total force.')

            elif 'entering subroutine stress ...' in line:
                try:
                    stress = []
                    for k in range(10):
                        if "P=" in data_step[count + k + 1]:
                            count2 = count + k + 1
                    if '(Ry/bohr**3)' not in data_step[count2]:
                        raise QEOutputParsingError('Error while parsing stress: unexpected units.')
                    for k in range(3):
                        line2 = data_step[count2 + k + 1].split()
                        vec = [float(s) * 10 ** (-9) * ry_si / (bohr_si) ** 3 for s in line2[0:3]]
                        stress.append(vec)
                    try:
                        trajectory_data['stress'].append(stress)
                    except KeyError:
                        trajectory_data['stress'] = [stress]
                    parsed_data['stress' + units_suffix] = default_stress_units
                except Exception:
                    parsed_data['warnings'].append('Error while parsing stress tensor.')

    return parsed_data, trajectory_data, critical_warnings.values()


def parse_QE_errors(lines, count, warnings):
    """
    Parse QE errors messages (those appearing between some lines with
    ``'%%%%%%%%'``)

    :param lines: list of strings, the output text file as read by readlines()
        or as obtained by data.split('\\n') when data is the text file read by read()
    :param count: the line at which we identified some ``'%%%%%%%%'``
    :param warnings: the warnings already parsed in the file
    :return messages: a list of QE error messages
    """

    # find the indices of the lines with problems
    found_endpoint = False
    init_problem = count
    for count2, line2 in enumerate(lines[count + 1:]):
        end_problem = count + count2 + 1
        if "%%%%%%%%%%%%" in line2:
            found_endpoint = True
            break
    messages = []
    if found_endpoint:
        # build a dictionary with the lines
        prob_list = lines[init_problem:end_problem + 1]
        irred_list = list(set(prob_list))
        for v in prob_list:
            if ( len(v) > 0 and (v in irred_list and v not in warnings) ):
                messages.append(irred_list.pop(irred_list.index(v)))

    return messages

