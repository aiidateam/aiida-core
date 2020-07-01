# -*- coding: utf-8 -*-
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.engine import CalcJob

class ArithmeticAddCalculation(CalcJob):
    """Implementation of CalcJob to add two numbers for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int, help='The left operand.')
        spec.input('y', valid_type=orm.Int, help='The right operand.')
        spec.output('sum', valid_type=orm.Int, help='The sum of the left and right operand.')

    def prepare_for_submission(self, folder):
        """Write the input files that are required for the code to run.

        :param folder: an `~aiida.common.folders.Folder` to temporarily write files on disk
        :return: `~aiida.common.datastructures.CalcInfo` instance
        """
        input_x = self.inputs.x
        input_y = self.inputs.y

        # Write the input file based on the inputs that were passed
        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write('{} {}\n'.format(input_x.value, input_y.value))

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.options.output_filename
        codeinfo.cmdline_params = ['-in', self.options.input_filename]

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = []

        return calcinfo
