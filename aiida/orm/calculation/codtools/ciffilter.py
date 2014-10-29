# -*- coding: utf-8 -*-
"""
Plugin to create input for cif_filter from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os
import shutil

from aiida.orm import Calculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import CalcInfo
from aiida.common.utils import classproperty

class CiffilterCalculation(Calculation):

    def _init_internal_params(self):
        super(CiffilterCalculation, self)._init_internal_params()

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

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
        if 'values' in parameters.get_dict():
            for k in parameters.get_dict()['values'].keys():
                v = parameters.get_dict()['values'][k]
                if not isinstance(v, list):
                    v = [ v ]
                if len( k ) == 1:
                    k = "-{}".format( k )
                else:
                    k = "--{}".format( k )
                for val in v:
                    commandline_params.append( "{} {}".format( k, val ) )

        if 'flags' in parameters.get_dict():
            for f in parameters.get_dict()['flags']:
                if len( f ) == 1:
                    f = "-{}".format( f )
                else:
                    f = "--{}".format( f )
                commandline_params.append( f )

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        # The command line parameters should be generated from 'parameters'
        calcinfo.cmdline_params = commandline_params
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.stdin_name  = self._DEFAULT_INPUT_FILE
        calcinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE]
        calcinfo.retrieve_singlefile_list = []

        return calcinfo
