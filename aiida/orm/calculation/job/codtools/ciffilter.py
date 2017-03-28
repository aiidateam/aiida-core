# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty



class CiffilterCalculation(JobCalculation):
    """
    Generic input plugin for scripts from cod-tools package.
    """

    def _init_internal_params(self):
        super(CiffilterCalculation, self)._init_internal_params()

        # Name of the default parser
        self._default_parser = 'codtools.ciffilter'

        # Default command line parameters
        self._default_commandline_params = []

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'
        self._DEFAULT_ERROR_FILE = 'aiida.err'

    def set_resources(self, resources_dict):
        """
        Overrides the original ``set_resouces()`` in order to prevent
        parallelization, which is not supported and may cause strange
        behaviour.

        :raises FeatureNotAvailable: when ``num_machines`` or
            ``num_mpiprocs_per_machine`` are being set to something other
            than 1.
        """
        self._validate_resources(**resources_dict)
        super(CiffilterCalculation, self).set_resources(resources_dict)

    @classproperty
    def _use_methods(cls):
        retdict = JobCalculation._use_methods
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

    def _validate_resources(self, **kwargs):
        from aiida.common.exceptions import FeatureNotAvailable

        for key in ['num_machines', 'num_mpiprocs_per_machine',
                    'tot_num_mpiprocs']:
            if key in kwargs and kwargs[key] != 1:
                raise FeatureNotAvailable(
                    "Cannot set resouce '{}' to value '{}' for {}: "
                    "parallelization is not supported, only value of "
                    "'1' is accepted.".format(key, kwargs[key],
                                              self.__class__.__name__))

    def _prepare_for_submission(self, tempfolder, inputdict):
        from aiida.orm.calculation.job.codtools import commandline_params_from_dict
        import shutil

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

        code = inputdict.pop(self.get_linkname('code'), None)
        if code is None:
            raise InputValidationError("Code not found in input")

        self._validate_resources(**self.get_resources())

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        shutil.copy(cif.get_file_abs_path(), input_filename)

        commandline_params = self._default_commandline_params
        commandline_params.extend(
            commandline_params_from_dict(parameters.get_dict()))

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
