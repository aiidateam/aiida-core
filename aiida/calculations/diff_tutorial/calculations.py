# -*- coding: utf-8 -*-
"""
Calculations provided by aiida_diff tutorial plugin.

Register calculations via the "aiida.calculations" entry point in the pyproject.toml file.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData


class DiffCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the diff executable.

    Simple AiiDA plugin wrapper for 'diffing' two files.
    """

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        # yapf: disable
        super(DiffCalculation, cls).define(spec)

        # new ports
        spec.input('file1', valid_type=SinglefileData, help='First file to be compared.')
        spec.input('file2', valid_type=SinglefileData, help='Second file to be compared.')
        spec.output('diff', valid_type=SinglefileData, help='diff between file1 and file2.')

        spec.input('metadata.options.output_filename', valid_type=str, default='patch.diff')
        spec.inputs['metadata']['options']['resources'].default = {
                                            'num_machines': 1,
                                            'num_mpiprocs_per_machine': 1,
                                            }
        spec.inputs['metadata']['options']['parser_name'].default = 'diff-tutorial'

        spec.exit_code(300, 'ERROR_MISSING_OUTPUT_FILES',
                message='Calculation did not produce all expected output files.')


    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files needed by
            the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        codeinfo = datastructures.CodeInfo()
        codeinfo.cmdline_params = [self.inputs.file1.filename, self.inputs.file2.filename]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (self.inputs.file1.uuid, self.inputs.file1.filename, self.inputs.file1.filename),
            (self.inputs.file2.uuid, self.inputs.file2.filename, self.inputs.file2.filename),
        ]
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo
