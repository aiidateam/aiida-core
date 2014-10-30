# -*- coding: utf-8 -*-
"""
Plugin to create input for scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os
import shutil

from aiida.orm import Calculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import CalcInfo
from aiida.common.utils import classproperty

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CodtoolsCalculation(Calculation):
    """
    Generic input plugin for scripts from cod-tools package.
    """

    def _init_internal_params(self):
        super(CodtoolsCalculation, self)._init_internal_params()

        # Default input and output files
        self._DEFAULT_INPUT_FILE  = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'
        self._DEFAULT_ERROR_FILE  = 'aiida.err'

    @classproperty
    def _use_methods(cls):
        retdict = Calculation._use_methods
        retdict.update({
            "cif": {
               'valid_types': CifData,
               'additional_parameter': None,
               'linkname': 'cif',
               'docstring': "A CIF file to be processed",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Parameters used in command line",
               },
            })
        return retdict

    def _prepare_for_submission(self,tempfolder,inputdict):
        try:
            cif = inputdict.pop(self.get_linkname('cif'))
        except KeyError:
            raise InputValidationError("no CIF file is specified for this calculation")
        if not isinstance(cif, CifData):
            raise InputValidationError("cif is not of type CifData")

        parameters = inputdict.pop(self.get_linkname('parameters'), None)
        if parameters is None:
            parameters = ParameterData(dict={})
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        shutil.copy( cif.get_file_abs_path(), input_filename )

        commandline_params = []
        for k in parameters.get_dict().keys():
            v = parameters.get_dict()[k]
            if v is None:
                continue
            if not isinstance(v, list):
                v = [ v ]
            key = None
            if len( k ) == 1:
                key = "-{}".format( k )
            else:
                key = "--{}".format( k )
            for val in v:
                if isinstance(val, bool) and val == False:
                    continue
                if isinstance(val, bool):
                    commandline_params.append( key )
                else:
                    commandline_params.append( "{} {}".format( key, val ) )


        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        # The command line parameters should be generated from 'parameters'
        calcinfo.cmdline_params = commandline_params
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.stdin_name  = self._DEFAULT_INPUT_FILE
        calcinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        calcinfo.stderr_name = self._DEFAULT_ERROR_FILE
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE,
                                  self._DEFAULT_ERROR_FILE]
        calcinfo.retrieve_singlefile_list = []

        return calcinfo
