# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This is a simple plugin that takes two node inputs, both of type ParameterData,
with the following labels: template and parameters.
You can also add other SinglefileData nodes as input, that will be copied according to
what is written in 'template' (see below).

* parameters: a set of parameters that will be used for substitution.

* template: can contain the following parameters:

    * input_file_template: a string with substitutions to be managed with the format()\
      function of python, i.e. if you want to substitute a variable called 'varname', you write\
      {varname} in the text. See http://www.python.org/dev/peps/pep-3101/ for more\
      details. The replaced file will be the input file.

    * input_file_name: a string with the file name for the input. If it is not provided, no\
      file will be created.

    * output_file_name: a string with the file name for the output. If it is not provided, no\
      redirection will be done and the output will go in the scheduler output file.

    * cmdline_params: a list of strings, to be passed as command line parameters.\
      Each one is substituted with the same rule of input_file_template. Optional

    * input_through_stdin: if True, the input file name is passed via stdin. Default is\
      False if missing.

    * files_to_copy: if defined, a list of tuple pairs, with format ('link_name', 'dest_rel_path');\
         for each tuple, an input link to this calculation is looked for, with link labeled 'link_label',\
         and with file type 'Singlefile', and the content is copied to a remote file named 'dest_rel_path'\
         Errors are raised in the input links are non-existent, or of the wrong type, or if there are \
         unused input files.

TODO: probably use Python's Template strings instead??
TODO: catch exceptions
"""
from aiida.orm.calculation.job import JobCalculation
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.utils import classproperty
from aiida.orm.data.parameter import ParameterData

# TODO: write a 'input_type_checker' routine to automatically check the existence
# and type of inputs + default values etc.



class TemplatereplacerCalculation(JobCalculation):
    """
    Simple stub of a plugin that can be used to replace some text in a given
    template. Can be used for many different codes, or as a starting point
    to develop a new plugin.
    """

    @classproperty
    def _use_methods(cls):
        retdict = JobCalculation._use_methods
        retdict.update({
            "template": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'template',
               'docstring': "A template for the input file",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Parameters used to replace placeholders in the template",
               },
            })
        return retdict

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputs_dict (with the Code!)
        """
        import StringIO

        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data.singlefile import SinglefileData
        from aiida.orm.data.remote import RemoteData
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.common.exceptions import ValidationError

        parameters_node = inputdict.pop('parameters', None)
        if parameters_node is None:
            parameters = {}
        else:
            parameters = parameters_node.get_dict()

        template_node = inputdict.pop('template', None)
        template = template_node.get_dict()

        input_file_template = template.pop('input_file_template', "")
        input_file_name = template.pop('input_file_name', None)
        output_file_name = template.pop('output_file_name', None)
        cmdline_params_tmpl = template.pop('cmdline_params', [])
        input_through_stdin = template.pop('input_through_stdin', False)
        files_to_copy = template.pop('files_to_copy', [])

        if template:
            raise InputValidationError("The following keys could not be "
                                       "used in the template node: {}".format(
                template.keys()))

        try:
            validate_list_of_string_tuples(files_to_copy, tuple_length=2)
        except ValidationError as e:
            raise InputValidationError("invalid file_to_copy format: {}".format(e.message))

        local_copy_list = []
        remote_copy_list = []

        for link_name, dest_rel_path in files_to_copy:
            try:
                fileobj = inputdict.pop(link_name)
            except KeyError:
                raise InputValidationError("You are asking to copy a file link {}, "
                                           "but there is no input link with such a name".format(link_name))
            if isinstance(fileobj, SinglefileData):
                local_copy_list.append((fileobj.get_file_abs_path(), dest_rel_path))
            elif isinstance(fileobj, RemoteData):  # can be a folder
                remote_copy_list.append(
                    (fileobj.get_computer().uuid, fileobj.get_remote_path(), dest_rel_path)
                )
            else:
                raise InputValidationError("If you ask to copy a file link {}, "
                                           "it must be either a SinglefileData or a RemoteData; it is instead of type {}".format(
                    link_name, fileobj.__class__.__name__))

        code = inputdict.pop('code', None)
        if code is None:
            raise InputValidationError("No code in input")

        if len(inputdict) > 0:
            raise InputValidationError("The input nodes with the following labels could not be "
                                       "used by the templatereplacer plugin: {}".format(
                inputdict.keys()))

        if input_file_name is not None and not input_file_template:
            raise InputValidationError("If you give an input_file_name, you "
                                       "must also specify a input_file_template")

        if input_through_stdin and input_file_name is None:
            raise InputValidationError("If you ask for input_through_stdin you have to "
                                       "specify a input_file_name")

        input_file = StringIO.StringIO(input_file_template.format(**parameters))
        if input_file_name:
            tempfolder.create_file_from_filelike(input_file, input_file_name)
        else:
            if input_file_template:
                self.logger.warning("No input file name passed, but a input file template is present")

        cmdline_params = [i.format(**parameters) for i in cmdline_params_tmpl]

        calcinfo = CalcInfo()
        calcinfo.retrieve_list = []

        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = cmdline_params
        if input_through_stdin is not None:
            codeinfo.stdin_name = input_file_name
        if output_file_name:
            codeinfo.stdout_name = output_file_name
            calcinfo.retrieve_list.append(output_file_name)
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo
