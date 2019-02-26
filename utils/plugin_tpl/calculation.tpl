#-*- coding: utf8 -*-
"""
defines {{classname}}
"""
from aiida.orm import JobCalculation


class {{classname}}(JobCalculation):
    """TODO: describe the calculation"""

    def _init_internal_params(self):
        """Initialize internal parameters"""
        super({{classname}}, self)._init_internal_params()

        self._INPUT_FILE_NAME = '{{ifilename}}'
        self._OUTPUT_FILE_NAME = '{{ofilename}}'
        self._default_parser = '{{parser}}'

    @classproperty
    def _use_methods(cls):
        """
        input node declaration hook
        """

        '''
        Start by getting the _use_methods from super and update the dictionary
        before returning it.

        Each entry should look like this::

            '<name>': { # the input will be set with calc.use_<name>(Data)
                'valid_types': <DataClass | (DataClass, [DataClass,])>,
                'additional_parameter': <param-name(s)>,
                    # -> use_<name>_<param-name>(Data)
                'linkname': <link name>
                    # The name attached to the link in the db between the input
                    # and the calculation. Will be used for queries.
                'docstring': <A description of the input>
            }
        '''
        retdict = super({{classname}}, self)._use_methods
        retdict.update({
            {% for item in inputs %}
            '{{item.name}}: {
            'valid_types': {{item.types}},
            'additional_parameter': {{item.adn_par}},
            'linkname': '{{item.get("lname", item.name)}}'
            'docstring': '{{item.docstring}}'
            },
            {% endfor %}
        })
        return retdict

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        Hook for the deamon to create input files and do everything
        else necessary before submitting the calculation to the computer.

        :param tempfolder: all input files should be put into this :py:class:`aiida.common.folders.Folder` subclass
        :param inputdict: a dictionary containing all the inputs, keys are link names
        """
        self.verify_inputs(self, inputdict)

        self._write_inputfiles(self, tempfolder, inputdict)

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        '''list of files to copy to the computer'''
        calcinfo.local_copy_list = [] # [('<local src abspath>', '<relative dest path>')]
        calcinfo.remote_copy_list = [] # [('<remote name>', '<remote src abspath>', '<relative dest path>')]
        calcinfo.retrieve_list = [self._OUTPUT_FILE_NAME] # add all files to be parsed

        code = inputdict['code']
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = [] # example: ['-i {}'.format(self._INPUT_FILE_NAME)]
        codeinfo.code_uuid = code.uuid

        calcinfo.codes_info = [codeinfo]

        return calcinfo

    def verify_inputs(self, inputdict):
        """
        ensure required input nodes are given, of the right type and nothing else

        raise ValidationError(<message>) otherwise

        example required node::

            try:
                param_name = inputdict.pop(self.get_linkname(param_name))
            except KeyError:
                raise InputValidationError("Missing: param_name")

            if not isinstance(param_name, param_type(s)):
                raise InputValidationError("Wrong type: param_name")

        example no superfluous nodes::

            # after pop() - ing all expected nodes
            if inputdict:
                raise ValidationError("Superflous input nodes!")
        """

        '''TODO: implement input checks'''

    def _write_input_files(self, tempfolder, inputdict):
        """
        write inputfiles to a temporary folder in preparation to submitting

        example using json input format::

            # Dict input nodes
            input_params = inputdict['param_name'].get_dict()
            secondary_params = inputdict['secondary_name'].get_dict()

            input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
            with open(input_filename, 'w') as infile:
                json.dump(input_params, infile)

            secondary_input_filename = tempfolder.get_abs_path('secondary.inp')
            with open(secondary_input_filename, 'w') as infile:
                json.dump(secondary_params, infile)
        """

        '''TODO: implement input file writing
