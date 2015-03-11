# -*- coding: utf-8 -*-
"""
Plugin to create input for scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os
import shutil

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import CalcInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifcoddepositCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_deposit from cod-tools package.
    """
    def _init_internal_params(self):
        super(CifcoddepositCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcoddeposit'
        self._CONFIG_FILE = 'config.conf'
        default_url = \
            'http://test.crystallography.net/cgi-bin/cif-deposit.pl'
        self._default_commandline_params = [ '--use-rm',
                                             '--read-stdin',
                                             '--output-mode', 'stdout',
                                             '--no-print-timestamps',
                                             '--url', default_url,
                                             '--config', self._CONFIG_FILE ]

        self._config_keys = [ 'username', 'password', 'journal',
                              'user_email', 'author_name', 'author_email',
                              'hold_period' ]

    @classproperty
    def _use_methods(cls):
        retdict = JobCalculation._use_methods
        retdict.update({
            "cif": {
               'valid_types': CifData,
               'additional_parameter': None,
               'linkname': 'cif',
               'docstring': "A CIF file to be deposited",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Deposition parameters",
               },
            })
        return retdict

    def _prepare_for_submission(self,tempfolder,inputdict):
        from aiida.orm.calculation.job.codtools import commandline_params_from_dict
        try:
            cif = inputdict.pop(self.get_linkname('cif'))
        except KeyError:
            raise InputValidationError("no CIF file is specified for deposition")
        if not isinstance(cif, CifData):
            raise InputValidationError("cif is not of type CifData")

        parameters = inputdict.pop(self.get_linkname('parameters'), None)
        if parameters is None:
            parameters = ParameterData(dict={})
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")

        parameters_dict = parameters.get_dict()

        deposit_file_rel = "deposit.cif"
        deposit_file_abs = tempfolder.get_abs_path(deposit_file_rel)
        shutil.copy( cif.get_file_abs_path(), deposit_file_abs)

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename,'w') as f:
            f.write("{}\n".format(deposit_file_rel))
            f.flush()

        config_file_abs = tempfolder.get_abs_path(self._CONFIG_FILE)
        with open(config_file_abs,'w') as f:
            for k in self._config_keys:
                if k in parameters_dict.keys():
                    f.write("{}={}\n".format(k,parameters_dict.pop(k)))
            f.flush()

        commandline_params = self._default_commandline_params
        commandline_params.extend(
            commandline_params_from_dict( parameters_dict ) )

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
