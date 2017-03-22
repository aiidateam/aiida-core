# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError



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
        self._default_commandline_params = ['--use-rm',
                                            '--read-stdin',
                                            '--output-mode', 'stdout',
                                            '--no-print-timestamps',
                                            '--url', default_url,
                                            '--config', self._CONFIG_FILE]

        self._config_keys = ['username', 'password', 'journal',
                             'user_email', 'author_name', 'author_email',
                             'hold_period']

    def _prepare_for_submission(self, tempfolder, inputdict):
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.calculation.job.codtools import commandline_params_from_dict
        import shutil

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

        code = inputdict.pop(self.get_linkname('code'), None)
        if code is None:
            raise InputValidationError("No code found in input")

        parameters_dict = parameters.get_dict()

        deposit_file_rel = "deposit.cif"
        deposit_file_abs = tempfolder.get_abs_path(deposit_file_rel)
        shutil.copy(cif.get_file_abs_path(), deposit_file_abs)

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename, 'w') as f:
            f.write("{}\n".format(deposit_file_rel))
            f.flush()

        config_file_abs = tempfolder.get_abs_path(self._CONFIG_FILE)
        with open(config_file_abs, 'w') as f:
            for k in self._config_keys:
                if k in parameters_dict.keys():
                    f.write("{}={}\n".format(k, parameters_dict.pop(k)))
            f.flush()

        commandline_params = self._default_commandline_params
        commandline_params.extend(
            commandline_params_from_dict(parameters_dict))

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        # The command line parameters should be generated from 'parameters'
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE,
                                  self._DEFAULT_ERROR_FILE]
        calcinfo.retrieve_singlefile_list = []

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = commandline_params
        codeinfo.stdin_name = self._DEFAULT_INPUT_FILE
        codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        codeinfo.stderr_name = self._DEFAULT_ERROR_FILE
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo
