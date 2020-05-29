# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`CalcJob` implementation to add two numbers using bash for testing and demonstration purposes."""
from aiida import orm
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.engine import CalcJob


class ArithmeticAddCalculation(CalcJob):
    """`CalcJob` implementation to add two numbers using bash for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        # yapf: disable
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'
        spec.inputs['metadata']['options']['input_filename'].default = 'aiida.in'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'
        spec.inputs['metadata']['options']['resources'].default = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
        spec.input('x', valid_type=(orm.Int, orm.Float), help='The left operand.')
        spec.input('y', valid_type=(orm.Int, orm.Float), help='The right operand.')
        spec.input('settings', required=False, valid_type=orm.Dict, help='Optional settings.')
        spec.output('sum', valid_type=(orm.Int, orm.Float), help='The sum of the left and right operand.')
        spec.exit_code(300, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(310, 'ERROR_READING_OUTPUT_FILE',
            message='The output file could not be read from the retrieved folder.')
        spec.exit_code(320, 'ERROR_INVALID_OUTPUT',
            message='The output file contains invalid output.')
        spec.exit_code(410, 'ERROR_NEGATIVE_NUMBER',
            message='The sum of the operands is a negative number. Only thrown if `settings.allow_negative = False`.')

    def prepare_for_submission(self, folder):
        """Prepare the calculation for submission.

        This method will convert the input nodes into the corresponding input files that the code will read in. In
        addition, it will prepare and return a `CalcInfo` instance, that contains information for the engine, for
        example, on what files to copy to the remote machine, what files to retrieve once it has completed, specific
        scheduler settings and more.
        :param folder: an `aiida.common.folders.Folder` to write the input files to
        :returns: `aiida.common.datastructures.CalcInfo` instance
        """
        input_x = self.inputs.x
        input_y = self.inputs.y
        input_code = self.inputs.code

        self.write_input_files(folder, input_x, input_y)

        codeinfo = CodeInfo()
        codeinfo.stdin_name = self.options.input_filename
        codeinfo.stdout_name = self.options.output_filename
        codeinfo.code_uuid = input_code.uuid

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [self.options.output_filename]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []

        return calcinfo

    def write_input_files(self, folder, input_x, input_y):
        """
        Take the input_parameters dictionary with the namelists and their flags
        and write the input file to disk in the temporary folder

        :param folder: an aiida.common.folders.Folder to temporarily write files on disk
        :param input_x: the numeric node representing the left operand of the summation
        :param input_y: the numeric node representing the right operand of the summation
        """
        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write('echo $(({} + {}))\n'.format(input_x.value, input_y.value))
