# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of CalcJobNode to add two numbers for testing and demonstration purposes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida import orm
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.engine import CalcJob


class ArithmeticAddCalculation(CalcJob):
    """Implementation of CalcJob to add two numbers for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        super(ArithmeticAddCalculation, cls).define(spec)
        spec.input('metadata.options.input_filename', valid_type=six.string_types, default='aiida.in', non_db=True)
        spec.input('metadata.options.output_filename', valid_type=six.string_types, default='aiida.out', non_db=True)
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='arithmetic.add', non_db=True)
        spec.input('x', valid_type=(orm.Int, orm.Float), help='The left operand.')
        spec.input('y', valid_type=(orm.Int, orm.Float), help='The right operand.')
        spec.output('sum', valid_type=(orm.Int, orm.Float), help='The sum of the left and right operand.')
        spec.exit_code(
            100, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(
            110, 'ERROR_READING_OUTPUT_FILE', message='The output file could not be read from the retrieved folder.')
        spec.exit_code(120, 'ERROR_INVALID_OUTPUT', message='The output file contains invalid output.')

    def prepare_for_submission(self, folder):
        """
        This method is called prior to job submission with a set of calculation input nodes.
        The inputs will be validated and sanitized, after which the necessary input files will
        be written to disk in a temporary folder. A CalcInfo instance will be returned that contains
        lists of files that need to be copied to the remote machine before job submission, as well
        as file lists that are to be retrieved after job completion.

        :param folder: an aiida.common.folders.Folder to temporarily write files on disk
        :returns: CalcInfo instance
        """
        input_x = self.inputs.x
        input_y = self.inputs.y
        input_code = self.inputs.code

        self.write_input_files(folder, input_x, input_y)

        retrieve_list = self.get_retrieve_list()
        local_copy_list = self.get_local_copy_list()
        remote_copy_list = self.get_remote_copy_list()

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = ['-in', self.options.input_filename]
        codeinfo.stdout_name = self.options.output_filename
        codeinfo.code_uuid = input_code.uuid

        calcinfo = CalcInfo()
        calcinfo.uuid = str(self.node.uuid)
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = retrieve_list
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list

        return calcinfo

    def get_retrieve_list(self):
        """
        Build the list of files that are to be retrieved upon calculation completion so that they can
        be passed to the parser.

        :returns: list of resource retrieval instructions
        """
        return [self.options.output_filename]

    @staticmethod
    def get_local_copy_list():
        """
        Build the local copy list, which are files that need to be copied from the local to the remote machine

        :returns: list of resource copy instructions
        """
        return []

    @staticmethod
    def get_remote_copy_list():
        """
        Build the remote copy list, which are files that need to be copied from the remote machine from one place
        to the directory of the new calculation on the same remote machine

        :returns: list of resource copy instructions
        """
        return []

    def write_input_files(self, folder, input_x, input_y):
        """
        Take the input_parameters dictionary with the namelists and their flags
        and write the input file to disk in the temporary folder

        :param folder: an aiida.common.folders.Folder to temporarily write files on disk
        :param input_x: the numeric node representing the left operand of the summation
        :param input_y: the numeric node representing the right operand of the summation
        """
        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write(u'{} {}\n'.format(input_x.value, input_y.value))
