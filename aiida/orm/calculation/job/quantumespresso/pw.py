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
"""
# TODO: COPY OUTDIR FROM PREVIOUS CALCULATION! Should be an input node of type
# RemoteData (or maybe subclass it?).
# TODO: tests!
# TODO: DOC + implementation of SETTINGS
# TODO: preexec, postexec
# TODO: Check that no further parameters are passed in SETTINGS
# TODO: many cards missing: check and implement
#       e.g.: ['CONSTRAINTS', 'OCCUPATIONS']
# TODO: implement pre... and post... hooks to add arbitrary strings before
#       and after a namelist, and a 'final_string' (all optional); useful
#       for development when new cards are needed
# TODO: all a lot of logger.debug stuff
import os

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.job.quantumespresso import BasePwCpInputGenerator
from aiida.common.utils import classproperty
from aiida.orm.data.array.kpoints import KpointsData



class PwCalculation(BasePwCpInputGenerator, JobCalculation):
    """
    Main DFT code (PWscf, pw.x) of the Quantum ESPRESSO distribution.
    For more information, refer to http://www.quantum-espresso.org/
    """
    # false due to PWscf bug, could be set to true on versions >= 5.1.0
    _default_symlink_usage = False

    def _init_internal_params(self):
        super(PwCalculation, self)._init_internal_params()

        self._DATAFILE_XML = os.path.join(
            BasePwCpInputGenerator._OUTPUT_SUBFOLDER,
            '{}.save'.format(BasePwCpInputGenerator._PREFIX),
            BasePwCpInputGenerator._DATAFILE_XML_BASENAME)

        # Default PW output parser provided by AiiDA
        self._default_parser = 'quantumespresso.pw'

        self._automatic_namelists = {
            'scf': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
            'nscf': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
            'bands': ['CONTROL', 'SYSTEM', 'ELECTRONS'],
            'relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
            'md': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS'],
            'vc-md': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
            'vc-relax': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'],
        }

        # Keywords that cannot be set
        self._blocked_keywords = [('CONTROL', 'pseudo_dir'),  # set later
                                  ('CONTROL', 'outdir'),  # set later
                                  ('CONTROL', 'prefix'),  # set later
                                  ('SYSTEM', 'ibrav'),  # set later
                                  ('SYSTEM', 'celldm'),
                                  ('SYSTEM', 'nat'),  # set later
                                  ('SYSTEM', 'ntyp'),  # set later
                                  ('SYSTEM', 'a'), ('SYSTEM', 'b'),
                                  ('SYSTEM', 'c'),
                                  ('SYSTEM', 'cosab'), ('SYSTEM', 'cosac'),
                                  ('SYSTEM', 'cosbc'),
                                  ]

        self._use_kpoints = True

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        retdict = JobCalculation._use_methods
        retdict.update(BasePwCpInputGenerator._baseclass_use_methods)

        retdict['kpoints'] = {
            'valid_types': KpointsData,
            'additional_parameter': None,
            'linkname': 'kpoints',
            'docstring': "Use the node defining the kpoint sampling to use",
        }

        return retdict
   
    @classmethod
    def input_helper(cls, *args, **kwargs):
        """
        Validate if the keywords are valid Quantum ESPRESSO pw.x keywords, and
        also helps in preparing the input parameter dictionary in a 
        'standardized' form (e.g., converts ints to floats when required,
        or if the flag flat_mode is specified, puts the keywords in the right
        namelists).
        
        This function calls 
        :py:func:`aiida.orm.calculation.job.quantumespresso.helpers.pw_input_helper`,
        see its docstring for further information.
        """
        from . import helpers
        return helpers.pw_input_helper(*args, **kwargs)
    
    
