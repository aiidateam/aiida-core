# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import shutil

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty


def _prepare_pymatgen_dict(parameters,struct=None):
    from pymatgen.io.nwchem import NwInput
    import copy

    par = copy.deepcopy(parameters)
    add_cell = par.pop('add_cell',False)
    if struct:
        if add_cell:
            par['geometry_options'].append(
                '\n  system crystal\n'
                '    lat_a {}\n    lat_b {}\n    lat_c {}\n'
                '    alpha {}\n    beta  {}\n    gamma {}\n'
                '  end'.format(*(struct.cell_lengths+struct.cell_angles)))

        if 'mol' not in par:
            par['mol'] = {}
        if 'sites' not in par['mol']:
            par['mol']['sites'] = []

        atoms = struct.get_ase()
        for i,atom_type in enumerate(atoms.get_chemical_symbols()):
            xyz = []
            if add_cell:
                xyz = atoms.get_scaled_positions()[i]
            else:
                xyz = atoms.get_positions()[i]
            par['mol']['sites'].append({
                'species': [ { 'element': atom_type, 'occu': 1 } ],
                'xyz': xyz
            })

    return str(NwInput.from_dict(par))

class NwcpymatgenCalculation(JobCalculation):
    """
    Generic input plugin for NWChem, using pymatgen.
    """
    def _init_internal_params(self):
        super(NwcpymatgenCalculation, self)._init_internal_params()

        # Name of the default parser
        self._default_parser = 'nwchem.nwcpymatgen'

        # Default input and output files
        self._DEFAULT_INPUT_FILE  = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'
        self._DEFAULT_ERROR_FILE  = 'aiida.err'

        # Default command line parameters
        self._default_commandline_params = [ self._DEFAULT_INPUT_FILE ]

    @classproperty
    def _use_methods(cls):
        retdict = JobCalculation._use_methods
        retdict.update({
            "structure": {
               'valid_types': StructureData,
               'additional_parameter': None,
               'linkname': 'structure',
               'docstring': "A structure to be processed",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Parameters describing NWChem input",
               },
            })
        return retdict

    def _prepare_for_submission(self,tempfolder,inputdict):
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("no parameters are specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")

        if 'structure' in inputdict:
            struct = inputdict.pop(self.get_linkname('structure'))
            if not isinstance(struct, StructureData):
                raise InputValidationError("structure is not of type StructureData")

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("no code is specified for this calculation")

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename,'w') as f:
            f.write(_prepare_pymatgen_dict(parameters.get_dict(),struct))
            f.flush()

        commandline_params = self._default_commandline_params

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE,
                                  self._DEFAULT_ERROR_FILE]
        calcinfo.retrieve_singlefile_list = []

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = commandline_params
        codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        codeinfo.stderr_name = self._DEFAULT_ERROR_FILE
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo
