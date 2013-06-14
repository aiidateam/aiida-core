"""
A collection of function that are used to parse the output of Quantum Espresso PW.
The function that needs to be called from outside is parse_raw_output().
Ideally, the functions should work even without aiida and will return a dictionary with parsed keys.
"""
from xml.dom.minidom import parseString
import os, sys
import string
from distutils.version import StrictVersion
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.parsers.quantumespresso.constants import *
from aiida.parsers.exceptions import OutputParsingError, FailedJobError

# TODO : need to check the units of energy 
# TODO : use some input info to support better parsing

lattice_tolerance = 1.e-5

class QEOutputParsingError(OutputParsingError):
    pass
    # def __init__(self,message):
    #     wrappedmessage = "Error parsing Quantum Espresso PW output: " + message
    #     super(QEOutputParsingError,self).__init__(wrappedmessage)
    #     self.message = wrappedmessage
    #     self.module = "qe-pw"

def cell_volume(a1,a2,a3):
    """
    returns the volume of the primitive cell: |a1.(a2xa3)|
    """
    a_mid_0 = a2[1]*a3[2] - a2[2]*a3[1]
    a_mid_1 = a2[2]*a3[0] - a2[0]*a3[2]
    a_mid_2 = a2[0]*a3[1] - a2[1]*a3[0]
    return abs(float(a1[0]*a_mid_0 + a1[1]*a_mid_1 + a1[2]*a_mid_2))

# In the following, some functions that helps the parsing of
# the xml file of QE v5.0.x (version below not tested)
def read_xml_card(dom,cardname):
    try:
        return dom.getElementsByTagName(cardname)[0]
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {}'.format(cardname) )

def parse_xml_child_integer(tagname,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.childNodes[0]
        return int(b.data)
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {}'
                                   .format(tagname,target_tags.tagName) )

def parse_xml_child_float(tagname,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.childNodes[0]
        return float(b.data)
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {}'\
                                   .format(tagname, target_tags.tagName ) )

def parse_xml_child_bool(tagname,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.childNodes[0]
        return str2bool(b.data)
    except Exception as e:
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
    except Exception as e:
        raise QEOutputParsingError('Error converting string to boolean.')

def parse_xml_child_str(tagname,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.childNodes[0]
        return str(b.data).rstrip().replace('\n','')
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {}'\
                                   .format(tagname, target_tags.tagName) )

def parse_xml_child_attribute_str(tagname,attributename,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        value=str(a.getAttribute(attributename))
        return value.rstrip().replace('\n','').lower()
    except Exception as e:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                   .format(attributename,tagname,target_tags.tagName) )

def parse_xml_child_attribute_int(tagname,attributename,target_tags):
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        value=int(a.getAttribute(attributename))
        return value
    except Exception as e:
        raise QEOutputParsingError('Error parsing attribute {}, tag {} inside {}'
                                    .format(attributename,tagname,target_tags.tagName) )

def grep_energy_from_line(line):
    try:
        return float(line.split('=')[1].split('Ry')[0])*ry_to_ev
    except Exception as e:
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

def parse_pw_xml_output(data,dir_with_bands=None):
    """
    Parse the xml data of QE v5.0.x
    Input data must be a single string, as returned by file.read()
    Returns a dictionary with parsed values
    """
    # NOTE : I often assume that if the xml file has been written, it has no
    # internal errors.
    
    dom = parseString(data)
    
    parsed_data = {}
    
    parsed_data['xml_warnings'] = []
    
    #CARD CELL
    
    cardname = 'CELL'
    target_tags = read_xml_card(dom,cardname)
    
    tagname = 'NON-PERIODIC_CELL_CORRECTION'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_str(tagname,target_tags)

    tagname='BRAVAIS_LATTICE'
    parsed_data[tagname.lower()] = parse_xml_child_str(tagname,target_tags)

    tagname = 'LATTICE_PARAMETER'
    value = parse_xml_child_float(tagname,target_tags)
    parsed_data[tagname.replace('-','_').lower()+'_xml'] = \
        parse_xml_child_float(tagname,target_tags)
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
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.childNodes[0]
        c=b.data.replace('\n','').split()
        value=[]
        for i in range(6):
            value.append(float(c[i]))            
        parsed_data[tagname.replace('-','_').lower()]=value
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'.format(tagname,target_tags.tagName) )

    tagname = 'DIRECT_LATTICE_VECTORS'
    lattice_vectors = []
    try: 
        second_tagname='UNITS_FOR_DIRECT_LATTICE_VECTORS'
        a=target_tags.getElementsByTagName(tagname)[0]
        b=a.getElementsByTagName('UNITS_FOR_DIRECT_LATTICE_VECTORS')[0]
        value=str(b.getAttribute('UNITS')).lower()
        parsed_data[second_tagname.replace('-','_').lower()]=value
        
        metric = value
        if metric not in ['bohr','angstroms']:
            raise QEOutputParsingError('Error parsing tag {} inside {}: units not supported: {}'
                                       .format(tagname,target_tags.tagName,metric) )

        lattice_vectors = []
        for second_tagname in ['a1','a2','a3']:
            b = a.getElementsByTagName(second_tagname)[0]
            c = b.childNodes[0]
            d = c.data.replace('\n','').split()
            value = []
            for i in range(3):
                value.append(float(d[i]))
            if metric=='bohr':
                value = [ bohr_to_ang*float(s) for s in value ]
            lattice_vectors.append(value)
        
        volume = cell_volume(lattice_vectors[0],lattice_vectors[1],lattice_vectors[2])
        
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {} inside {}.'
                                   .format(tagname,target_tags.tagName,cardname) )
    # NOTE: lattice_vectors will be saved later together with card IONS.atom

    tagname = 'RECIPROCAL_LATTICE_VECTORS'
    try:    
        a = target_tags.getElementsByTagName(tagname)[0]
        
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
            value = []
            for i in range(3):
                value.append(float(d[i]))
            if metric == '2 pi / a':
                value=[ float(s)/parsed_data['lattice_parameter'] for s in value ]
            this_matrix.append(value)
        parsed_data['reciprocal_lattice_vectors'] = this_matrix
        
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} inside {}.'
                                   .format(tagname,target_tags.tagName) )
                
    #CARD HEADER

    cardname='HEADER'
    target_tags=read_xml_card(dom,cardname)
    
    tagname='FORMAT'
    attrname='NAME'
    parsed_data[(tagname+'_'+attrname).lower()] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)

    attrname='VERSION'
    parsed_data[(tagname+'_'+attrname).lower()] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)

    tagname='CREATOR'
    attrname='NAME'
    parsed_data[(tagname+'_'+attrname).lower()] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)
        
    attrname='VERSION'
    parsed_data[(tagname+'_'+attrname).lower()] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)

    # CARD CONTROL

    cardname='CONTROL'
    target_tags=read_xml_card(dom,cardname)

    tagname='PP_CHECK_FLAG'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='LKPOINT_DIR'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='Q_REAL_SPACE'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='BETA_REAL_SPACE'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    # TODO : why this one isn't working? What is it actually?
#    # CARD MOVING_CELL
#
#    try:
#        target_tags = dom.getElementsByTagName('MOVING_CELL')[0]
#    except:
#        raise IOError
#
#    tagname='CELL_FACTOR'
#    parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)

    # CARD IONS

    cardname='IONS'
    target_tags=read_xml_card(dom,cardname)

    tagname='NUMBER_OF_ATOMS'
    parsed_data[tagname.lower()]=parse_xml_child_integer(tagname,target_tags)

    tagname='NUMBER_OF_SPECIES'
    parsed_data[tagname.lower()]=parse_xml_child_integer(tagname,target_tags)

    tagname='UNITS_FOR_ATOMIC_MASSES'
    attrname='UNITS'
    parsed_data['atomic_masses_units'] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)

    try:
        parsed_data['species'] = {}
        parsed_data['species']['index'] = []
        parsed_data['species']['type'] = []
        parsed_data['species']['mass'] = []
        parsed_data['species']['pseudo'] = []
        for i in range(parsed_data['number_of_species']):
            tagname = 'SPECIE.'+str(i+1)
            parsed_data['species']['index'].append(i+1)

            a = target_tags.getElementsByTagName(tagname)[0]
            
            tagname2 = 'ATOM_TYPE'
            parsed_data['species']['type'].append(parse_xml_child_str(tagname2,a))

            tagname2 = 'MASS'
            parsed_data['species']['mass'].append(parse_xml_child_float(tagname2,a))

            tagname2 = 'PSEUDO'
            parsed_data['species']['pseudo'].append(parse_xml_child_str(tagname2,a))

        tagname = 'UNITS_FOR_ATOMIC_POSITIONS'
        attrname = 'UNITS'
        parsed_data['atomic_positions_units'] = \
            parse_xml_child_attribute_str(tagname,attrname,target_tags)
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag SPECIE.# inside {}.'.format(tagname))
    # TODO : For calculations launched with AiiDA, angstrom is the unit used.
    # but for other imports, we don't know.
    if parsed_data['atomic_positions_units'] not in ['angstrom','bohr']:
        parsed_data['xml_warnings'].append('Angstrom Units for atomic ' + \
                    'positions were expected.' + \
                    'Found instead {}'.format(parsed_data['atomic_positions_units']) )

    try:
        atomlist = []
        atoms_index_list = []
        atoms_if_pos_list = []
        tagslist = []
        for i in range(parsed_data['number_of_atoms']):
            tagname='ATOM.'+str(i+1)
            a=target_tags.getElementsByTagName(tagname)[0]
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
                # If I can't parse the digit, it is probably not there:
                # I add a None to the tagslist
                tagslist.append(None)
            # I remove the symbols
            chem_symbol = chem_symbol.translate(None, string.digits)
            tagname2 = 'tau'
            b=a.getAttribute(tagname2)
            tau=[float(s) for s in b.rstrip().replace("\n","").split()]
            metric=parsed_data['atomic_positions_units']
            if metric not in ['alat','bohr','angstrom']:
                raise QEOutputParsingError('Error parsing tag {}'.format(tagname) + \
                                           ' inside {}'.format(target_tags.tagName) )
            if metric=='alat':
                tau = [ parsed_data['lattice_parameter_xml']*float(s) for s in tau ]
            elif metric=='bohr':
                tau = [ bohr_to_ang*float(s) for s in tau ]
            atomlist.append([chem_symbol,tau])
            tagname2='if_pos'
            b=a.getAttribute(tagname2)
            if_pos=[int(s) for s in b.rstrip().replace("\n","").split()]
            atoms_if_pos_list.append(if_pos)
            
        parsed_data['atoms']=atomlist
        parsed_data['atoms_index_list'] = atoms_index_list
        parsed_data['atoms_if_pos_list'] = atoms_if_pos_list
        # NOTE: saving a bunch of data together to have an object analogous
        # to the AiiDA cell object
        cell = {}
        cell['lattice_vectors'] = lattice_vectors
        cell['volume'] = volume
        cell['atoms'] = atomlist
        cell['tagslist'] = tagslist
        parsed_data['cell'] = cell
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise QEOutputParsingError('Error parsing tag ATOM.# inside' + \
                                   ' {}.'.format(target_tags.tagName) )
    
    # CARD ELECTRIC_FIELD

    cardname='ELECTRIC_FIELD'
    target_tags=read_xml_card(dom,cardname)

    tagname='HAS_ELECTRIC_FIELD'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='HAS_DIPOLE_CORRECTION'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    if parsed_data['has_electric_field'] or parsed_data['has_dipole_correction']:
        tagname='FIELD_DIRECTION'
        parsed_data[tagname.lower()]=parse_xml_child_integer(tagname,target_tags)
        
        tagname='MAXIMUM_POSITION'
        parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)
        
        tagname='INVERSE_REGION'
        parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)
        
        tagname='FIELD_AMPLITUDE'
        parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)

    # CARD PLANE_WAVES

    cardname='PLANE_WAVES'
    target_tags=read_xml_card(dom,cardname)

    tagname='UNITS_FOR_CUTOFF'
    attrname='UNITS'
    parsed_data['cutoff_units']=parse_xml_child_attribute_str(tagname,attrname,target_tags)

    tagname='WFC_CUTOFF'
    parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)

    tagname='RHO_CUTOFF'
    parsed_data[tagname.lower()]=parse_xml_child_float(tagname,target_tags)

#    tagname='MAX_NUMBER_OF_GK-VECTORS'
#    parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_integer(tagname,target_tags)

    tagname='FFT_GRID'
    fft_grid=[]
    attrname='nr1'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    attrname='nr2'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    attrname='nr3'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    parsed_data[tagname.lower()]=fft_grid

    tagname='SMOOTH_FFT_GRID'
    fft_grid=[]
    attrname='nr1s'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    attrname='nr2s'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    attrname='nr3s'
    fft_grid.append(parse_xml_child_attribute_int(tagname,attrname,target_tags))
    parsed_data[tagname.lower()]=fft_grid

    # CARD SPIN

    cardname='SPIN'
    target_tags=read_xml_card(dom,cardname)

    tagname='LSDA'
    parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='NON-COLINEAR_CALCULATION'
    parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='SPIN-ORBIT_CALCULATION'
    parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_bool(tagname,target_tags)

    tagname='SPIN-ORBIT_DOMAG'
    parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_bool(tagname,target_tags)

    # CARD BRILLOUIN ZONE
    
    cardname='BRILLOUIN_ZONE'
    target_tags=read_xml_card(dom,cardname)

    tagname='NUMBER_OF_K-POINTS'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_integer(tagname,target_tags)

    tagname = 'UNITS_FOR_K-POINTS'
    attrname = 'UNITS'
    metric = parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if metric not in ['2 pi / a']:
        raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                ' tag {} inside {}, units unknown'.format(tagname, target_tags.tagName) )
    parsed_data['k_points_units'] = metric

    # TODO: check what happens if one does not use the monkhorst pack in the code
    tagname='MONKHORST_PACK_GRID'
    try:
        a = target_tags.getElementsByTagName(tagname)[0]
        value = [int(a.getAttribute('nk'+str(i+1))) for i in range(3)]
        parsed_data[tagname.replace('-','_').lower()] = value
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {}'.format(tagname) + \
                                   ' inside {}.'.format(target_tags.tagName ) )

    tagname='MONKHORST_PACK_OFFSET'
    try:
        a=target_tags.getElementsByTagName(tagname)[0]
        value=[int(a.getAttribute('k'+str(i+1))) for i in range(3)]
        parsed_data[tagname.replace('-','_').lower()]=value
    except Exception as e:
        raise QEOutputParsingError('Error parsing tag {} '.format(tagname) + \
                                   'inside {}.'.format(target_tags.tagName) )

    try:
        kpoints = []
        for i in range(parsed_data['number_of_k_points']):
            tagname = 'K-POINT.'+str(i+1)
            a = target_tags.getElementsByTagName(tagname)[0]
            b = a.getAttribute('XYZ').replace('\n','').rsplit()
            value = [ float(s) for s in b ]
            
            metric = parsed_data['k_points_units']
            if metric=='2 pi / a':
                value = [ float(s)/parsed_data['lattice_parameter'] for s in value ]
                weight = float(a.getAttribute('WEIGHT'))                
                kpoints.append([value,weight])
                
        parsed_data['k_point']=kpoints
    except Exception as e:
        raise QEOutputParsingError( 'Error parsing tag K-POINT.# ' + \
                                    'inside {}.'.format(target_tags.tagName) )
    
    try:
        tagname='STARTING_K-POINTS'
        num_starting_k_points=parse_xml_child_integer(tagname,target_tags)
        # raise exception if there is no such a key
        parsed_data[tagname.replace('-','_').lower()]=num_starting_k_points

        if parsed_data.get('starting_k_points'):
            try:
                kpoints=[]
                for i in range(parsed_data['starting_k_points']):
                    tagname='K-POINT_START.'+str(i+1)
                    a=target_tags.getElementsByTagName(tagname)[0]
                    b=a.getAttribute('XYZ').replace('\n','').rsplit()
                    value=[ float(s) for s in b ]
                    metric=parsed_data['k_points_units']
                    if metric=='2 pi / a':
                        value=[ float(s)/parsed_data['lattice_parameter'] for s in value ]

                        weight=float(a.getAttribute('WEIGHT'))

                        kpoints.append([value,weight])

                parsed_data['k_point_start']=kpoints
            except Exception as e:
                print e
                raise QEOutputParsingError('Error parsing tag {}'.format(tagname)+\
                                           ' inside {}.'.format(target_tags.tagName ) )
    except Exception as ev:
        if not parsed_data.get('starting_k_points'):
            pass
        else:
            parsed_data['xml_warnings'].append("Warning: could not parse {}".format(tagname))

    # tagname='NORM-OF-Q'
    # TODO decide if save this parameter
    # parsed_data[tagname.replace('-','_').lower()]=parse_xml_child_float(tagname,target_tags)
    
    # CARD BAND STRUCTURE INFO

    cardname = 'BAND_STRUCTURE_INFO'
    target_tags = read_xml_card(dom,cardname)

    tagname='NUMBER_OF_SPIN_COMPONENTS'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_integer(tagname,target_tags)

    tagname='NON-COLINEAR_CALCULATION'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_bool(tagname,target_tags)

    tagname='NUMBER_OF_ATOMIC_WFC'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_integer(tagname,target_tags)

    tagname='NUMBER_OF_BANDS'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_integer(tagname,target_tags)

    tagname='NUMBER_OF_ELECTRONS'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_float(tagname,target_tags)

    tagname = 'UNITS_FOR_ENERGIES'
    attrname = 'UNITS'
    parsed_data['energy_units'] = \
        parse_xml_child_attribute_str(tagname,attrname,target_tags)
    if parsed_data['energy_units'] not in ['hartree']:
        raise QEOutputParsingError('Expected energy units in Hartree.' + \
                                   'Got instead {}'.format(parsed_data['energy_units']) )

    try:
        tagname='TWO_FERMI_ENERGIES'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_bool(tagname,target_tags) * hartree_to_ev
    except Exception as e:
        pass

    # TODO what happens if spin polarizeda and there are two fermi energies?
    tagname = 'FERMI_ENERGY'
    parsed_data[tagname.replace('-','_').lower()] = \
        parse_xml_child_float(tagname,target_tags) * hartree_to_ev

    #CARD MAGNETIZATION_INIT
    cardname = 'MAGNETIZATION_INIT'
    target_tags = read_xml_card(dom,cardname)

    # 0 if false
    tagname='CONSTRAINT_MAG'
    parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)

    # already done
    #tagname='NUMBER_OF_SPECIES'
    
    vec1 = []
    vec2 = []
    vec3 = []
    for i in range(parsed_data['number_of_species']):
        tagname='SPECIE.'+str(i+1)
        a=target_tags.getElementsByTagName(tagname)[0]
        tagname2='STARTING_MAGNETIZATION'
        vec1.append(parse_xml_child_float(tagname2,a))
        tagname2='ANGLE1'
        vec2.append(parse_xml_child_float(tagname2,a))
        tagname2='ANGLE2'
        vec3.append(parse_xml_child_float(tagname2,a))
    parsed_data['species']['starting_magnetization'] = vec1
    parsed_data['species']['angle1'] = vec2
    parsed_data['species']['angle2'] = vec3

    #CARD OCCUPATIONS

    cardname = 'OCCUPATIONS'
    target_tags = read_xml_card(dom,cardname)

    tagname = 'SMEARING_METHOD'
    parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)

    tagname = 'TETRAHEDRON_METHOD'
    parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)

    tagname='FIXED_OCCUPATIONS'
    parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)

    #CARD CHARGE-DENSITY

    cardname='CHARGE-DENSITY'
    target_tags=read_xml_card(dom,cardname)

    try:
        attrname='iotk_link'
        value=str(target_tags.getAttribute(attrname)).rstrip().replace('\n','').lower()
        parsed_data[cardname.lower().rstrip().replace('-','_')]=value
    except Exception as e:
        raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                                   ' card {}.'.format(cardname))

    #CARD EIGENVALUES

    cardname='EIGENVALUES'
    target_tags=read_xml_card(dom,cardname)
    if dir_with_bands:
        try:
            occupations = []
            bands=[]
            for i in range(parsed_data['number_of_k_points']):
                tagname='K-POINT.'+str(i+1)
                a=target_tags.getElementsByTagName(tagname)[0]
                tagname2='DATAFILE'
                b=a.getElementsByTagName(tagname2)[0]
                attrname='iotk_link'
                value=str(b.getAttribute(attrname)).rstrip().replace('\n','')

                eigenval_n = os.path.join(dir_with_bands,value)

                # load the eigenval.xml file
                with open(eigenval_n,'r') as eigenval_f:
                    f = eigenval_f.read()
                    
                eig_dom = parseString(f)

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
                value=[ float(s)*hartree_to_ev for s in b.data.split() ]
                bands.append(value)

                tagname='OCCUPATIONS'
                a = eig_dom.getElementsByTagName(tagname)[0]
                b = a.childNodes[0]
                value=[ float(s) for s in b.data.split() ]
                occupations.append(value)
            parsed_data['occupations'] = occupations
            parsed_data['bands'] = bands        
        except Exception as e:
            raise QEOutputParsingError('Error parsing card {}'.format(tagname))

    # in QE, the homo coincide with the fermi energy, both for metals and insulators
    parsed_data['homo'] = parsed_data['fermi_energy']

    # TODO : the search for the lumo is ridiculous
    try:
        # if there is at least an empty band:
        if parsed_data['smearing_method'] or parsed_data['number_of_electrons'] \
                /2.0 < parsed_data['number_of_bands']:
            # initialize lumo
            lumo = parsed_data['homo']+10000.0
            for list_bands in parsed_data['bands']:
                for value in list_bands:
                    if (value > parsed_data['fermi_energy']) and (value<lumo):
                        lumo=value
            if (lumo==parsed_data['homo']+10000.0) or lumo<=parsed_data['fermy_energy']:
                #might be an error for bandgap larger than 10000 eV
                raise QEOutputParsingError('Error while searching for LUMO.')
            parsed_data['lumo']=lumo
    except Exception as e:
        pass
    
    # Card symmetries

    try:    
        cardname='SYMMETRIES'
        target_tags=read_xml_card(dom,cardname)

        tagname='NUMBER_OF_SYMMETRIES'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_integer(tagname,target_tags)

        tagname='NUMBER_OF_BRAVAIS_SYMMETRIES'
        parsed_data[tagname.replace('-','_').lower()] = \
            parse_xml_child_integer(tagname,target_tags)

        tagname='INVERSION_SYMMETRY'
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

        tagname='DO_NOT_USE_TIME_REVERSAL'
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

        tagname='TIME_REVERSAL_FLAG'
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

        tagname='NO_TIME_REV_OPERATIONS'
        parsed_data[tagname.lower()]=parse_xml_child_bool(tagname,target_tags)

        tagname='UNITS_FOR_SYMMETRIES'
        attrname='UNITS'
        metric=parse_xml_child_attribute_str(tagname,attrname,target_tags)
        if metric not in ['crystal']:
            raise QEOutputParsingError('Error parsing attribute {},'.format(attrname) + \
                                       ' tag {} inside '.format(tagname) + \
                                       '{}, units unknown'.format(target_tags.tagName ) )
        parsed_data['symmetries_units'] = metric

        # parse the symmetry matrices
        parsed_data['symmetries']=[]
        find_sym=True
        i=0
        while find_sym:
            try:
                i+=1
                current_sym={}
                tagname='SYMM.'+str(i)
                a=target_tags.getElementsByTagName(tagname)[0]
                tagname2='INFO'
                b=a.getElementsByTagName(tagname2)[0]
                attrname='NAME'
                value=str(b.getAttribute(attrname)).rstrip().replace('\n','')
                current_sym['name']=value

                try:
                    attrname='T_REV'
                    value=str(b.getAttribute(attrname)).rstrip().replace('\n','')
                    current_sym[attrname.lower()]=value
                except Exception as e:
                    pass

                tagname2='ROTATION'
                b=a.getElementsByTagName(tagname2)[0]
                c=[ int(s) for s in b.childNodes[0].data.split() ]
                # convert list to matrix
                line=[]
                value=[]
                for j in range(9):
                    line.append(float(c[j]))
                    if (j+1)%3==0:
                        value.append(line)
                        line=[]
                current_sym[tagname2.lower()]=value

                try:
                    tagname2='FRACTIONAL_TRANSLATION'
                    b=a.getElementsByTagName(tagname2)[0]
                    value=[ float(s) for s in b.childNodes[0].data.split() ]
                    current_sym[tagname2.lower()]=value
                except Exception as e:
                    pass

                try:
                    tagname2='EQUIVALENT_IONS'
                    b=a.getElementsByTagName(tagname2)[0]
                    value=[ int(s) for s in b.childNodes[0].data.split() ]
                    current_sym[tagname2.lower()]=value
                except Exception as e:
                    pass

                parsed_data['symmetries'].append(current_sym)
            except Exception as e:
                find_sym=False
        
    except Exception as e:
        raise QEOutputParsingError('Error parsing card {}.'.format(tagname)) 
    
    # CARD EXCHANGE_CORRELATION
    
    cardname='EXCHANGE_CORRELATION'
    target_tags=read_xml_card(dom,cardname)

    tagname='DFT'
    parsed_data[(tagname+'_exchange_correlation').lower()] = \
        parse_xml_child_str(tagname,target_tags)

    tagname='LDA_PLUS_U_CALCULATION'
    parsed_data[tagname.lower()] = parse_xml_child_bool(tagname,target_tags)
    
    if parsed_data[tagname.lower()]: # if it is a plus U calculation, I expect more infos
        tagname = 'HUBBARD_L'
        try:
             a = target_tags.getElementsByTagName(tagname)[0]
             b = a.childNodes[0]
             c = b.data.replace('\n','').split()
             value = [int(i) for i in c]
             parsed_data[tagname.replace('-','_').lower()]=value
        except Exception as e:
            raise QEOutputParsingError('Error parsing tag '+\
                                       '{} inside {}.'.format(tagname, target_tags.tagName) )
        
        for tagname in ['HUBBARD_U','HUBBARD_ALPHA','HUBBARD_BETA','HUBBARD_J0']:
            try:
                a = target_tags.getElementsByTagName(tagname)[0]
                b = a.childNodes[0]
                c = b.data.replace('\n',' ').split() # note the need of a white space!
                value = [float(i)*ry_to_ev for i in c]
                parsed_data[tagname.replace('-','_').lower()]=value
            except Exception as e:
                raise QEOutputParsingError('Error parsing tag '+\
                                           '{} inside {}.'.format(tagname, target_tags.tagName))
        
        tagname = 'LDA_PLUS_U_KIND'
        try:
            parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)
        except Exception as e:
            pass

        tagname = 'U_PROJECTION_TYPE'
        try:
            parsed_data[tagname.lower()] = \
                parse_xml_child_attribute_str(tagname,attrname,target_tags)
        except Exception as e:
            pass

        tagname = 'HUBBARD_J'
        try:
            a=target_tags.getElementsByTagName(tagname)[0]
            b=a.childNodes[0]
            c=b.data.replace('\n','').split()
            value=[]
            list_of_3 = []
            for i in range(len(c)):
                list_of_3.append(float(c[i]))
                if (i+1)%3 == 0:
                    value.append(list_of_3)
                    list_of_3=[]

            parsed_data[tagname.replace('-','_').lower()]=value
        except Exception as e:
            pass
    
    try:
        tagname='NON_LOCAL_DF'
        parsed_data[tagname.lower()] = parse_xml_child_integer(tagname,target_tags)
    except Exception as e:
        pass
        # print >> sys.stderr, 'Skipping non-local df...'

    return parsed_data
 




def parse_pw_text_output(data, xml_data):
    """
    Parses the stdout of QE-PW.
    Input data must be a list of strings, one for each lines, as returned by
    readlines(). xml_data is the dictionary returned by the xml_parse
    function.
    
    Returns a dictionary with parsed values, without the values of the
    xml dictionary. 
    """
    
    parsed_data = {}
    parsed_data['warnings'] = []
    vdw_correction = False
    
    # use quantities from the xml file if possible
    if not xml_data:
        try:
            for line in data:
                if 'lattice parameter (alat)' in line:
                    alat = float(line.split('=')[1].split('a.u')[0])
                if 'number of atoms/cell' in line:
                    nat = int(line.split('=')[1])
                if 'number of atomic types' in line:
                    ntyp = int(line.split('=')[1])
                if 'number of Kohn-Sham states' in line:
                    nbnd = int(line.split('=')[1])
                    break
            parsed_data['warnings'].append('Xml data not found: parsing only the text output')
            parsed_data['number_of_atoms'] = nat
            parsed_data['number_of_species'] = ntyp
            parsed_data['number_of_bands'] = nbnd
            parsed_data['lattice_parameter_initial'] = alat
        except Exception as e:
            raise QEOutputParsingError("Parser can't load basic info.")
        
    else:
        nat = xml_data['number_of_atoms']
        ntyp = xml_data['number_of_species']
        nbnd = xml_data['number_of_bands']
        alat = xml_data['lattice_parameter_xml']
    # NOTE: lattice_parameter_xml is the lattice parameter of the xml file
    # in the units used by the code. lattice_parameter instead in angstroms.

    for count,line in enumerate(data):

        if 'Carrying out vdW-DF run using the following parameters:' in line:
            vdw_correction=True
        elif 'CELL_PARAMETERS' in line:
            try:
                if 'lattice_vectors_relax' not in parsed_data:
                    parsed_data['lattice_vectors_relax'] = []
                a1 = [float(s) for s in data[count+1].split()]
                a2 = [float(s) for s in data[count+2].split()]
                a3 = [float(s) for s in data[count+3].split()]
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
                parsed_data['lattice_vectors_relax'].append([a1,a2,a3])
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing cell_parameters.')

        elif 'EXX-fraction' in line:
            parsed_data['exx_fraction'] = float( line.split()[-1] )

        elif 'ATOMIC_POSITIONS' in line:
            try:
                this_key = 'atoms_relax'
                if this_key not in parsed_data:
                    parsed_data[this_key] = []
                # the inizialization of tau prevent parsed_data to be associated
                # to the pointer of the previous iteration
                metric = line.split('(')[1].split(')')[0]
                if metric not in ['alat','bohr','angstrom']:
                    raise QEOutputParsingError('Error while parsing atomic_positions:' + \
                                               ' units not supported.')
                # TODO : check how to map the atoms in the original scheme
                atoms = []
                for i in range(nat):
                    line2 = data[count+1+i].split()
                    tau = [float(s) for s in line2[1:4]]
                    chem_symbol = str(line2[0]).rstrip()
#                    # I remove digits from the symbol: Co1 becomes Co
#                    chem_symbol = chem_symbol.translate(None, string.digits)
                    if metric == 'alat':
                        for j in range(len(tau)):
                            tau = [ alat*float(s) for s in tau ]
                    elif metric == 'bohr':
                        for j in range(len(tau)):
                            tau = [ bohr_to_ang*float(s) for s in tau ]
                    atoms.append([chem_symbol,tau])
                parsed_data[this_key].append(atoms)
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing ATOMIC_POSITIONS.')

                # TODO : I want to save Co1

        # save dipole in debye units, only at last iteration of scf cycle
        elif 'Computed dipole along edir' in line:
            try:
                if 'dipole' not in parsed_data:
                    parsed_data['dipole'] = []
                # endless loop:
                doloop = True
                j = 0
                while doloop:
                    j += 1
                    if 'End of self-consistent calculation' in data[count+j]:
                        line2 = data[count+1]
                        value = float(line2.split('au,')[1].split('Debye')[0])
                        parsed_data['dipole'].append(value)
                        doloop = False
                        break
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing dipole values.')   

        elif 'convergence has been achieved in' in line:
            try:
                if 'scf_iterations' not in parsed_data:
                    parsed_data['scf_iterations']=[]
                parsed_data['scf_iterations'].append(int(line.split("in"\
                                                        )[1].split( "iterations")[0]))
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing scf iterations.')

        elif 'End of self-consistent calculation' in line:
            try:
                if 'ethr' not in parsed_data:
                    parsed_data['ethr'] = []
                doloop=True
                j=0
                while doloop:
                    j+=-1
                    line2=data[count+j]
                    if 'ethr' in line2:
                        parsed_data['ethr'].append(float(line2.split('=')[1].split(',')[0]))
                        doloop=False
                        break
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing ethr.')
        # grep energy and eventually, magnetization
        elif '!' in line:
            try:
                if 'energy' not in parsed_data:
                    parsed_data['energy'] = []
                if 'energy_accuracy' not in parsed_data:
                    parsed_data['energy_accuracy'] = []
                if 'energy_contribution' not in parsed_data:
                    parsed_data['energy_contribution'] = []
                if 'total_magnetization' not in parsed_data:
                    parsed_data['total_magnetization'] = []
                if 'absolute_magnetization' not in parsed_data:
                    parsed_data['absolute_magnetization'] = []

                En = float(line.split('=')[1].split('Ry')[0])*ry_to_ev
                E_acc = float(data[count+2].split('<')[1].split('Ry')[0])*ry_to_ev
                parsed_data['energy'].append(En)
                parsed_data['energy_accuracy'].append(E_acc)
                
                try:
                    # TODO decide units for magnetization. now bohr mag/cell
                    en_terms = {}
                    j = 0
                    while True:
                        j+=1
                        line2 = data[count+j]
                        if 'one-electron contribution' in line2:
                            en_terms['one-electron'] = grep_energy_from_line(line2)
                        elif 'hartree contribution' in line2:
                            en_terms['hartree'] = grep_energy_from_line(line2)
                        elif 'xc contribution' in line2:
                            en_terms['xc'] = grep_energy_from_line(line2)
                        elif 'ewald contribution' in line2:
                            en_terms['ewald'] = grep_energy_from_line(line2)
                        elif 'ewald contribution' in line2:
                            en_terms['ewald'] = grep_energy_from_line(line2)
                        elif 'smearing contrib.' in line2:
                            en_terms['smearing'] = grep_energy_from_line(line2)
                        elif 'one-center paw contrib.' in line2:
                            en_terms['one_center_paw'] = grep_energy_from_line(line2)
                        elif 'est. exchange err' in line:
                            en_terms['exchange_error'] = grep_energy_from_line(line2)
                        elif 'Fock energy' in line:
                            en_terms['fock'] = grep_energy_from_line(line2)
                        elif 'total magnetization' in line2:
                            if 'total_magnetization' not in parsed_data:
                                parsed_data['total_magnetization'] = []
                            value=float(line2.split('=')[1].split('Bohr')[0])
                            parsed_data['total_magnetization'].append(value)
                        elif 'absolute magnetization' in line2:
                            if 'absolute_magnetization' not in parsed_data:
                                parsed_data['absolute_magnetization'] = []
                            value=float(line2.split('=')[1].split('Bohr')[0])
                            parsed_data['absolute_magnetization'].append(value)
                        # last term present
                        elif 'convergence' in line2:
                            break
                            
                    if vdw_correction:
                        j=0
                        while True:
                            j+=-1
                            if 'Non-local correlation energy' in data[count+j]:
                                en_terms['vdw'] = grep_energy_from_line(line2)
                                break
                            
                    parsed_data['energy_contribution'].append(en_terms)
                except Exception as e:
                    parsed_data['warnings'].append('Error while parsing for energy terms.')
                    
            except Exception as e:
                ## Note : NO total energy in NSCF
                nscf = False
                for this_line in line:
                    if 'Band Structure Calculation' in this_line:
                        nscf = True
                        break
                if nscf:
                    pass
                else:
                    parsed_data['warnings'].append('Error while parsing for energy.')

        elif 'the Fermi energy is' in line:
            try:
                parsed_data['fermi_energy_outfile'] = line.split('is')[1].split('ev')[0]
            except Exception as e:
                parsed_data['warnings'] = 'Error while parsing Fermi energy.'

        elif 'PWSCF' in line and 'WALL' in line:
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data['wall_time'] = time
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing wall time.')
                
            try:
                parsed_data['wall_time_seconds'] = \
                    convert_qe_time_to_sec(parsed_data['wall_time'])
            except ValueError:
                raise QEOutputParsingError("Unable to convert wall_time in seconds.")

        elif 'Forces acting on atoms (Ry/au):' in line:
            try:
                if 'forces' not in parsed_data:
                    parsed_data['forces'] = []
                forces = []
                found_counter = 0
                for j in range(nat*8):  # 8*nat is a sufficiently high number of lines
                    line2 = data[count+j]
                    if 'atom ' in line2:
                        found_counter += 1
                        if str(found_counter)+' type' in line2:
                            line2 = line2.split('=')[1].split()
                            # CONVERT FORCES IN eV/Ang
                            vec = [ float(s)*ry_to_ev / \
                                 bohr_to_ang for s in line2 ]
                            forces.append(vec)
                            
                        else:
                            warning='Error while parsing forces.'
                            parsed_data['warnings'].append(warning)
                            
                        if found_counter==nat:
                            break
                if forces!=[]:
                    parsed_data['forces'].append(forces)
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing forces.')
                
    # TODO : adding the parsing support for the decomposition of the forces
                
        elif 'Total force =' in line:
            try:
                if 'total_force' not in parsed_data:
                    parsed_data['total_force'] = []
                value = float(line.split('=')[1].split('Total')[0])
                parsed_data['total_force'].append(value*ry_to_ev/bohr_to_ang)
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing total force.')
        
        elif 'entering subroutine stress ...' in line:
            try:
                if 'stress' not in parsed_data:
                    parsed_data['stress'] = []
                stress = []

                j = 0
                while True:
                    j += 1
                    if 'total' in data[count+j] and 'stress' in data[count+j]:
                        break

                line2=data[count+j]
                if '(Ry/bohr**3)' not in line2:
                    raise QEOutputParsingError('Error while parsing stress: unexpected units.')
                for k in range(3):
                    line2 = data[count+j+k+1].split()
                    vec = [ float(s)*ry_to_ev/(bohr_to_ang)**3 \
                            for s in line2[0:3] ]
                    stress.append(vec)
                parsed_data['stress'].append(stress)
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing stress tensor.')

            
        elif 'SUMMARY OF PHASES' in line:
            try:
                j = 0
                while True:
                    j+=1
                    if 'Ionic Phase' in data[count+j]:                        
                        value = float(data[count+j].split(':')[1].split('(')[0])
                        mod = float(data[count+j].split('(mod')[1].split(')')[0])
                        parsed_data['ionic_phase'] = {'value' : value, 'mod'  : mod}

                        j+=1
                        value = float(data[count+j].split(':')[1].split('(')[0])
                        mod = float(data[count+j].split('(mod')[1].split(')')[0])
                        parsed_data['electronic_phase'] = {'value' : value, 'mod'  : mod}
                        
                        j+=1
                        value = float(data[count+j].split(':')[1].split('(')[0])
                        mod = float(data[count+j].split('(mod')[1].split(')')[0])
                        parsed_data['total_phase'] = {'value' : value, 'mod'  : mod}

                    # TODO : decide a standard unit for e charge
                    if "e/bohr^2" in data[count+j]:
                        value = float(data[count+j].split('=')[1].split('(')[0])
                        mod = float(data[count+j].split('mod')[1].split(')')[0])
                        units = data[count+j].split(')')[1].strip() 
                        parsed_data['polarization'] = {'value':value,'mod':mod,'units':units}

                    if 'polarization direction' in data[count+j]: 
                       vec = [ float(s) for s in \
                              data[count+j].split('(')[1].split(')')[0].split(',') ]
                       parsed_data['polarization_direction'] = vec
                        
            except Exception as e:
                warning = 'Error while parsing polarization.'
                parsed_data['warnings'].append(warning)     
        
        
        # controls on relaxation-dynamics convergence
        # TODO put all the different relaxations
        elif 'nstep' in line and '=' in line:
            max_dynamic_iterations = int(line.split()[2])
        elif 'Wentzcovitch Damped Dynamics:' in line and 'iterations completed, stopping' in line:
            dynamic_iterations = int(line.split()[3])
            if max_dynamic_iterations == dynamic_iterations:
                warning = 'Maximum number of iterations reached in Wentzcovitch Damped Dynamics.'
                parsed_data['warnings'].append(warning)

        elif 'point group' in line:
            try:
                point_group_data = line.split()
                pg_international = point_group_data[-1].split('(')[1].split(')')[0]
                pg_schoenflies = point_group_data[-2]
                parsed_data['pointgroup_international'] = pg_international
                parsed_data['pointgroup_schoenflies'] = pg_schoenflies
            except Exception:
                warning = "Problem parsing point group, I found: {}".format(point_group_data)
                parsed_data['warnings'].append(warning)


        # Test of some errors
        # bands not converging
        elif 'eigenvalues not converged' in line and 'c_bands:' in line:
            try:
                problem = False
                num_not_conv=int(line.split()[1])
                doloop=True
                j=0
                while doloop:
                    j+=1
                    line2=data[count+j]
                    if 'iteration #' in line2:
                        break
                    elif 'End of self-consistent calculation' in line2 or \
                        'End of band structure calculation' in line2:
                        problem=True
                        break
                    if count+j==len(data)-2:   #-2 for the safety of not reaching the end of file
                        raise QEOutputParsingError('Error while parsing. While trying to understand'
                                                   ' the position of c_bands non convergence error,'
                                                   'reached the end of the file.')
                    if problem:
                        warning='{} bands did not reach convergence.'.format(num_not_conv)
                        parsed_data['warnings'].append(warning)
            except Exception as e:
                parsed_data['warnings'].append('Error while parsing c_bands errors.')

        # BFGS not at convergence
        elif 'The maximum number of steps has been reached.' in line:
            warning='The maximum number of ionic+electronic has been reached.'
            parsed_data['warnings'].append(warning)
        # scf not at convergence
        elif 'convergence NOT achieved after' in line and 'iterations: stopping':
            warning = 'Scf calculation did not reacher convergence after '+\
                '{} iterations'.format(int(line.split()[4]))
            parsed_data['warnings'].append(warning)

        elif 'SCF correction compared to forces is too large, reduce conv_thr' in line:
            warning='SCF correction compared to forces is too large, reduce conv_thr'
            parsed_data['warnings'].append(warning)
            
        elif 'Warning:' in line:
            parsed_data['warnings'].append(str(line))
    
        elif 'DEPRECATED:' in line:
            parsed_data['warnings'].append(str(line))

    return parsed_data


def parse_raw_output(out_file, input_dict, xml_file=None, dir_with_bands=None):
    """
    Parses the output of a calculation
    Receives in input the paths to the output file and the xml file.
    
    Args: 
        (str) out_file: 
            path to pw std output
        (str) xml_file: 
            path to QE data-file.xml
    
    Returns a dictionary with parsed data

    Raises QEOutputParsingError for errors in the parsing,
           AssertionError if two keys in the parsed dicts are found to be qual

    3 different keys to check in output: parser_warnings, xml_warnings and warnings.
    On an upper level, these flags MUST be checked.
    The first two are expected to be empty unless QE failures or unfinished jobs.
    """
    # TODO : a lot of ifs could be cleaned out
    
    # TODO : input_dict should be used as well
    
    parser_version = '0.1'
    parser_info = {}
    parser_info['parser_warnings'] = []
    parser_info['parser_info'] = 'AiiDA QE Parser v{}'.format(parser_version)

    # if xml_file is not given in input, skip its parsing
    if xml_file is not None:
        try:
            with open(xml_file,'r') as f:
                xml_lines = f.read() # read() instead of readlines() is needed
        except IOError:
            raise QEOutputParsingError("Failed to open xml file: {}.".format(xml_file))

        # parse the xml data, if present
        #        try:
        xml_data = parse_pw_xml_output(xml_lines,dir_with_bands)
            #        except QEOutputParsingError:
            #            raise QEOutputParsingError('Error while parsing XML data-file.')            
        # Assuming that if the file xml is written, it is consistent
        # and complete. Even in case of QE failure, it should always be so
    else:
        parser_info['parser_warnings'].append('Skipping the parsing of the xml file.')
        xml_data = {}

    
    # load QE out file
    try:
        with open(out_file,'r') as f:
            out_lines = f.readlines()
    except IOError:
        # if the file cannot be open, the error is severe.
        raise QEOutputParsingError("Failed to open output file: {}.".format(out_file))
    
    # check if the job has finished (that doesn't mean without errors)
    finished_run = False
    for line in out_lines[::-1]:
        if 'JOB DONE' in line:
            finished_run = True
            break
    
    if not finished_run:
        warning = 'QE pw run did not reach the end of the execution.'
        parser_info['parser_warnings'].append(warning)        

    try:
        out_data = parse_pw_text_output(out_lines,xml_data)
    except QEOutputParsingError as e:
        if not finished_run:
            parser_info['parser_warnings'].append('Error while parsing the output file')
            pass
        else:
            raise QEOutputParsingError('Error while parsing QE output')

    for key in out_data.keys():
        if key in xml_data.keys():
            raise AssertionError('{} found in both dictionaries'.format(key))
        # out_data keys take precedence and overwrite xml_data keys,
        # if the same key name is shared by both
        # dictionaries (but this should not happen!)
    final_data = dict(xml_data.items() + out_data.items() + parser_info.items())
    
    return final_data



if __name__ == '__main__':
    import unittest

    class TestQESampleOutputs(unittest.TestCase):
        """
        Tests the examples of Quantum Espresso #01 and #02.
        Simple scf runs
        """
        def test_scf_aluminum_cg(self):
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['1a','1b']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_scf_silicon(self):
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['2']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_scf_copper(self):
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['3']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_copper_bands(self):
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['4']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_relax_aluminum(self):
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['5']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_relax_aluminum_second(self):
            """
            Test an scf calculation in aluminum.
            """            
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['6']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

        def test_relax_co_molecule(self):
            """
            Test an scf calculation in aluminum.
            """            
            import os
            test_folder = './qe_pw_test'
            test_subfolder = ['7']
            for this_test_folder in test_subfolder:
                output_file = os.path.join(test_folder,this_test_folder,'aiida.out')
                xml_file = os.path.join(test_folder,this_test_folder,'data-file.xml')
            
                parsed_data = parse_raw_output(output_file,xml_file)
            
                # test if string is empty
                self.assertFalse( parsed_data['parser_warnings'] )
                self.assertFalse( parsed_data['xml_warnings'] )
                self.assertFalse( parsed_data['warnings'] )

    unittest.main()
