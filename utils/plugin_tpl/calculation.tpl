#-*- coding: utf8 -*-
"""
module {{module_path}}

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
        This will be called by the deamon to create input files and do everything
        else necessary before submitting the calculation to the computer.

        :param tempfolder: all input files should be put into this :py:class:`aiida.common.folders.Folder` subclass
        :param inputdict: a dictionary containing all the inputs, keys are link names
        """

