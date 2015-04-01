# -*- coding: utf-8 -*-
import os
import shutil

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.common.datastructures import CalcInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Andrius Merkys"

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
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Parameters describing NWChem input",
               },
            })
        return retdict

    def _prepare_for_submission(self,tempfolder,inputdict):
        from pymatgen.io.nwchemio import NwTask,NwInput
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("no parameters are specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename,'w') as f:
            f.write(str(NwInput.from_dict(parameters.get_dict())))
            f.flush()

        commandline_params = self._default_commandline_params

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = commandline_params
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        calcinfo.stderr_name = self._DEFAULT_ERROR_FILE
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE,
                                  self._DEFAULT_ERROR_FILE]
        calcinfo.retrieve_singlefile_list = []

        return calcinfo
