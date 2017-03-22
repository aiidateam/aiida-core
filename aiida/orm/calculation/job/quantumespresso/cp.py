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

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.job.quantumespresso import BasePwCpInputGenerator
from aiida.common.utils import classproperty



class CpCalculation(BasePwCpInputGenerator, JobCalculation):
    """
    Car-Parrinello molecular dynamics code (cp.x) of the
    Quantum ESPRESSO distribution.
    For more information, refer to http://www.quantum-espresso.org/
    """

    def _init_internal_params(self):
        super(CpCalculation, self)._init_internal_params()

        _cp_read_unit_number = 50
        _cp_write_unit_number = 51

        self._DATAFILE_XML = os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}_{}.save'.format(BasePwCpInputGenerator._PREFIX,
                                _cp_write_unit_number),
            BasePwCpInputGenerator._DATAFILE_XML_BASENAME)

        self._FILE_XML_PRINT_COUNTER = os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}_{}.save'.format(BasePwCpInputGenerator._PREFIX,
                                _cp_write_unit_number),
            self._FILE_XML_PRINT_COUNTER_BASENAME)

        # Default output parser provided by AiiDA
        self._default_parser = 'quantumespresso.cp'

        self._automatic_namelists = {
            'scf': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
            'nscf': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
            'relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
            'cp': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
            'vc-cp': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
            'vc-relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
            'vc-wf': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'WANNIER'],
        }

        # Keywords that cannot be set
        self._blocked_keywords = [('CONTROL', 'pseudo_dir'),  # set later
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

        self._use_kpoints = False

        # in restarts, it will copy from the parent the following 
        self._restart_copy_from = os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}_{}.save'.format(BasePwCpInputGenerator._PREFIX,
                                _cp_write_unit_number))
        # in restarts, it will copy the previous folder in the following one 
        self._restart_copy_to = os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}_{}.save'.format(BasePwCpInputGenerator._PREFIX,
                                _cp_read_unit_number))

        _cp_ext_list = ['cel', 'con', 'eig', 'evp', 'for', 'nos', 'pol',
                        'pos', 'spr', 'str', 'the', 'vel', 'wfc']

        # I retrieve them all, even if I don't parse all of them
        self._internal_retrieve_list = [os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}.{}'.format(BasePwCpInputGenerator._PREFIX,
                           ext)) for ext in _cp_ext_list]
        self._internal_retrieve_list += [self._FILE_XML_PRINT_COUNTER]

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

    @classproperty
    def _FILE_XML_PRINT_COUNTER_BASENAME(cls):
        return 'print_counter.xml'

    @classproperty
    def _default_verbosity(cls):
        return 'low'


    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        retdict = JobCalculation._use_methods
        retdict.update(BasePwCpInputGenerator._baseclass_use_methods)

        return retdict
    
    
