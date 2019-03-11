# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of CalcJobNode to replace a template for testing and demonstration purposes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida import orm
from aiida.common import exceptions
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.engine import CalcJob


class TemplatereplacerCalculation(CalcJob):
    """
    Simple stub of a plugin that can be used to replace some text in a given template.
    Can be used for many different codes, or as a starting point to develop a new plugin.

    This simple plugin takes two node inputs, both of type Dict, with the labels
    'parameters' and 'template'

    You can also add other SinglefileData nodes as input, that will be copied according to
    what is written in 'template' (see below).

    * parameters: a set of parameters that will be used for substitution.

    * template: can contain the following parameters:

        * input_file_template: a string with substitutions to be managed with the format()
          function of python, i.e. if you want to substitute a variable called 'varname', you write
          {varname} in the text. See http://www.python.org/dev/peps/pep-3101/ for more
          details. The replaced file will be the input file.

        * input_file_name: a string with the file name for the input. If it is not provided, no
          file will be created.

        * output_file_name: a string with the file name for the output. If it is not provided, no
          redirection will be done and the output will go in the scheduler output file.

        * cmdline_params: a list of strings, to be passed as command line parameters.
          Each one is substituted with the same rule of input_file_template. Optional

        * input_through_stdin: if True, the input file name is passed via stdin. Default is False if missing.

        * files_to_copy: if defined, a list of tuple pairs, with format ('link_name', 'dest_rel_path');
            for each tuple, an input link to this calculation is looked for, with link labeled 'link_label',
            and with file type 'Singlefile', and the content is copied to a remote file named 'dest_rel_path'
            Errors are raised in the input links are non-existent, or of the wrong type, or if there are
            unused input files.

        * retrieve_temporary_files: a list of relative filepaths, that if defined, will be retrieved and
            temporarily stored in an unstored FolderData node that will be available during the
            Parser.parser_with_retrieved call under the key specified by the Parser.retrieved_temporary_folder key

    """

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super(TemplatereplacerCalculation, cls).define(spec)
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='templatereplacer.doubler',
            non_db=True)
        spec.input('template', valid_type=orm.Dict,
            help='A template for the input file.')
        spec.input('parameters', valid_type=orm.Dict, required=False,
            help='Parameters used to replace placeholders in the template.')
        spec.input_namespace('files', valid_type=(orm.RemoteData, orm.SinglefileData), required=False)

        spec.output('output_parameters', valid_type=orm.Dict, required=True)
        spec.default_output_node = 'output_parameters'

        spec.exit_code(100, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(101, 'ERROR_NO_TEMPORARY_RETRIEVED_FOLDER',
            message='The temporary retrieved folder data node could not be accessed.')
        spec.exit_code(105, 'ERROR_NO_OUTPUT_FILE_NAME_DEFINED',
            message='The `template` input node did not specify the key `output_file_name`.')
        spec.exit_code(110, 'ERROR_READING_OUTPUT_FILE',
            message='The output file could not be read from the retrieved folder.')
        spec.exit_code(111, 'ERROR_READING_TEMPORARY_RETRIEVED_FILE',
            message='A temporary retrieved file could not be read from the temporary retrieved folder.')
        spec.exit_code(120, 'ERROR_INVALID_OUTPUT',
            message='The output file contains invalid output.')

    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where the plugin should put all its files.
        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        from six.moves import StringIO
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.common.exceptions import ValidationError

        code = self.inputs.code
        template = self.inputs.template.get_dict()

        try:
            parameters = self.inputs.parameters.get_dict()
        except AttributeError:
            parameters = {}

        input_file_template = template.pop('input_file_template', '')
        input_file_name = template.pop('input_file_name', None)
        output_file_name = template.pop('output_file_name', None)
        cmdline_params_tmpl = template.pop('cmdline_params', [])
        input_through_stdin = template.pop('input_through_stdin', False)
        files_to_copy = template.pop('files_to_copy', [])
        retrieve_temporary_files = template.pop('retrieve_temporary_files', [])

        if template:
            raise exceptions.InputValidationError(
                'The following keys could not be used in the template node: {}'.format(template.keys()))

        try:
            validate_list_of_string_tuples(files_to_copy, tuple_length=2)
        except ValidationError as exc:
            raise exceptions.InputValidationError("invalid file_to_copy format: {}".format(exc))

        local_copy_list = []
        remote_copy_list = []

        for link_name, dest_rel_path in files_to_copy:
            try:
                fileobj = self.inputs.files[link_name]
            except AttributeError:
                raise exceptions.InputValidationError("You are asking to copy a file link {}, "
                                                      "but there is no input link with such a name".format(link_name))
            if isinstance(fileobj, orm.SinglefileData):
                local_copy_list.append((fileobj.uuid, fileobj.filename, dest_rel_path))
            elif isinstance(fileobj, orm.RemoteData):  # can be a folder
                remote_copy_list.append((fileobj.computer.uuid, fileobj.get_remote_path(), dest_rel_path))
            else:
                raise exceptions.InputValidationError(
                    "If you ask to copy a file link {}, "
                    "it must be either a SinglefileData or a RemoteData; it is instead of type {}".format(
                        link_name, fileobj.__class__.__name__))

        if input_file_name is not None and not input_file_template:
            raise exceptions.InputValidationError(
                "If you give an input_file_name, you must also specify a input_file_template")

        if input_through_stdin and input_file_name is None:
            raise exceptions.InputValidationError(
                "If you ask for input_through_stdin you have to specify a input_file_name")

        input_content = input_file_template.format(**parameters)
        if input_file_name:
            folder.create_file_from_filelike(StringIO(input_content), input_file_name, 'w', encoding='utf8')
        else:
            if input_file_template:
                self.logger.warning("No input file name passed, but a input file template is present")

        cmdline_params = [i.format(**parameters) for i in cmdline_params_tmpl]

        calcinfo = CalcInfo()
        calcinfo.retrieve_list = []
        calcinfo.retrieve_temporary_list = []

        calcinfo.uuid = self.node.uuid
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = cmdline_params

        if input_through_stdin:
            codeinfo.stdin_name = input_file_name

        if output_file_name:
            codeinfo.stdout_name = output_file_name
            calcinfo.retrieve_list.append(output_file_name)

        if retrieve_temporary_files:
            calcinfo.retrieve_temporary_list = retrieve_temporary_files

        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo
