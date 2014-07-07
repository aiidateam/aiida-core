# -*- coding: utf-8 -*-
"""
Plugin to create a Quantum Espresso pw.x file.

TODO: COPY OUTDIR FROM PREVIOUS CALCULATION! Should be an input node of type
     RemoteData (or maybe subclass it?).
TODO: tests!
TODO: DOC + implementation of SETTINGS
TODO: preexec, postexec
TODO: Check that no further parameters are passed in SETTINGS
TODO: many cards missing: check and implement
      e.g.: ['CONSTRAINTS', 'OCCUPATIONS']
TODO: implement pre_... and post_... hooks to add arbitrary strings before
      and after a namelist, and a 'final_string' (all optional); useful 
      for development when new cards are needed
TODO: all a lot of logger.debug stuff
"""
import os

from aiida.orm import Calculation, DataFactory
from aiida.orm.calculation.quantumespresso import BasePwCpInputGenerator
from aiida.common.utils import classproperty

from aiida.orm.data.parameter import ParameterData
  
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class CpCalculation(BasePwCpInputGenerator, Calculation):   
    """
    Car-Parrinello molecular dynamics code (cp.x) of the
    Quantum ESPRESSO distribution.
    For more information, refer to http://www.quantum-espresso.org/
    """
    _cp_read_unit_number = 50
    _cp_write_unit_number = 51

    DATAFILE_XML = os.path.join(BasePwCpInputGenerator.OUTPUT_SUBFOLDER, 
                               '{}_{}.save'.format(BasePwCpInputGenerator.PREFIX,
                                                   _cp_write_unit_number), 
                               BasePwCpInputGenerator.DATAFILE_XML_BASENAME)

    FILE_XML_PRINT_COUNTER_BASENAME = 'print_counter.xml'
    FILE_XML_PRINT_COUNTER = os.path.join(BasePwCpInputGenerator.OUTPUT_SUBFOLDER, 
                               '{}_{}.save'.format(BasePwCpInputGenerator.PREFIX,
                                                   _cp_write_unit_number), 
                                          FILE_XML_PRINT_COUNTER_BASENAME)

    # Default PW output parser provided by AiiDA
    _default_parser = 'quantumespresso.cp'
    
    _automatic_namelists = {
        'scf':   ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        'nscf':  ['CONTROL', 'SYSTEM', 'ELECTRONS'],
        'relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
        'cp':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
        'vc-cp':    ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
        'vc-relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
        'vc-wf': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'WANNIER'],
        }

    # Keywords that cannot be set
    _blocked_keywords = [('CONTROL', 'pseudo_dir'), # set later
         ('CONTROL', 'outdir'),  # set later
         ('CONTROL', 'prefix'),  # set later
         ('SYSTEM', 'ibrav'),  # set later
         ('SYSTEM', 'celldm'),
         ('SYSTEM', 'nat'),  # set later
         ('SYSTEM', 'ntyp'),  # set later
         ('SYSTEM', 'a'), ('SYSTEM', 'b'), ('SYSTEM', 'c'),
         ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'), ('SYSTEM', 'cosbc'),
         ('CONTROL', 'ndr', _cp_read_unit_number),
         ('CONTROL', 'ndw', _cp_write_unit_number),
    ]
    
    _use_kpoints = False
    
    # in restarts, it will copy from the parent the following 
    _restart_copy_from = os.path.join(
                         BasePwCpInputGenerator.OUTPUT_SUBFOLDER,
                         '{}_{}.save'.format(BasePwCpInputGenerator.PREFIX,_cp_write_unit_number))
    # in restarts, it will copy the previous folder in the following one 
    _restart_copy_to = os.path.join(
                         BasePwCpInputGenerator.OUTPUT_SUBFOLDER,
                         '{}_{}.save'.format(BasePwCpInputGenerator.PREFIX,_cp_read_unit_number))

    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        retdict = Calculation._use_methods
        retdict.update(BasePwCpInputGenerator._baseclass_use_methods)
        
        return retdict
    
    
    _cp_ext_list = ['cel', 'con', 'eig', 'evp', 'for', 'nos', 'pol', 
                    'pos', 'spr', 'str', 'the', 'vel', 'wfc']
    
    # I retrieve them all, even if I don't parse all of them
    _internal_retrieve_list = [os.path.join(
                                 BasePwCpInputGenerator.OUTPUT_SUBFOLDER, 
                                 '{}.{}'.format(BasePwCpInputGenerator.PREFIX,
                                 ext)) for ext in _cp_ext_list]
    _internal_retrieve_list += [FILE_XML_PRINT_COUNTER]
