# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin representing an executable code stored in AiiDA's storage.

This plugin should be used for executables that are not already installed on the target computer, but instead are
available on the machine where AiiDA is running. The plugin assumes that the code is self-contained by a single
directory containing all the necessary files, including a main executable. When constructing a ``PortableCode``, passing
the absolute filepath as ``filepath_files`` will make sure that all the files contained within are uploaded to AiiDA's
storage. The ``filepath_executable`` should indicate the filename of the executable within that directory. Each time a
:class:`aiida.engine.CalcJob` is run using a ``PortableCode``, the uploaded files will be automatically copied to the
working directory on the selected computer and the executable will be run there.
"""
from __future__ import annotations

import pathlib

import click

from aiida.common import exceptions
from aiida.common.folders import Folder
from aiida.common.lang import type_check
from aiida.orm import Computer

from .legacy import Code

__all__ = ('PortableCode',)


class PortableCode(Code):
    """Data plugin representing an executable code stored in AiiDA's storage."""

    _KEY_ATTRIBUTE_FILEPATH_EXECUTABLE: str = 'filepath_executable'

    def __init__(self, filepath_executable: str, filepath_files: pathlib.Path, **kwargs):
        """Construct a new instance.

        .. note:: If the files necessary for this code are not all located in a single directory or the directory
            contains files that should not be uploaded, and so the ``filepath_files`` cannot be used. One can use the
            methods of the :class:`aiida.orm.nodes.repository.NodeRepository` class. This can be accessed through the
            ``base.repository`` attribute of the instance after it has been constructed. For example::

                code = PortableCode(filepath_executable='some_name.exe')
                code.put_object_from_file()
                code.put_object_from_filelike()
                code.put_object_from_tree()

        :param filepath_executable: The relative filepath of the executable within the directory of uploaded files.
        :param filepath_files: The filepath to the directory containing all the files of the code.
        """
        super().__init__(**kwargs)
        type_check(filepath_files, pathlib.Path)
        self.filepath_executable = filepath_executable  # type: ignore[assignment]
        self.base.repository.put_object_from_tree(str(filepath_files))

    def _validate(self):
        """Validate the instance by checking that an executable is defined and it is part of the repository files.

        :raises :class:`aiida.common.exceptions.ValidationError`: If the state of the node is invalid.
        """
        super(Code, self)._validate()  # Change to ``super()._validate()`` once deprecated ``Code`` class is removed.  # pylint: disable=bad-super-call

        try:
            filepath_executable = self.filepath_executable
        except TypeError as exception:
            raise exceptions.ValidationError('The `filepath_executable` is not set.') from exception

        objects = self.base.repository.list_object_names()

        if str(filepath_executable) not in objects:
            raise exceptions.ValidationError(
                f'The executable `{filepath_executable}` is not one of the uploaded files: {objects}'
            )

    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        A ``PortableCode`` should be able to be run on any computer in principle.

        :param computer: The computer.
        :return: ``True`` if the provided computer is the same as the one configured for this code.
        """
        return True

    def get_executable(self) -> pathlib.PurePosixPath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """
        return self.filepath_executable

    def validate_working_directory(self, folder: Folder):
        """Validate content of the working directory created by the :class:`~aiida.engine.CalcJob` plugin.

        This method will be called by :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.presubmit` when a new
        calculation job is launched, passing the :class:`~aiida.common.folders.Folder` that was used by the plugin used
        for the calculation to create the input files for the working directory. This method can be overridden by
        implementations of the ``AbstractCode`` class that need to validate the contents of that folder.

        :param folder: A sandbox folder that the ``CalcJob`` plugin wrote input files to that will be copied to the
            working directory for the corresponding calculation job instance.
        :raises PluginInternalError: The ``CalcJob`` plugin created a file that has the same relative filepath as the
            executable for this portable code.
        """
        if str(self.filepath_executable) in folder.get_content_list():
            raise exceptions.PluginInternalError(
                f'The plugin created a file {self.filepath_executable} that is also the executable name!'
            )

    @property
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """
        return self.label

    @property
    def filepath_executable(self) -> pathlib.PurePosixPath:
        """Return the relative filepath of the executable that this code represents.

        :return: The relative filepath of the executable.
        """
        return pathlib.PurePosixPath(self.base.attributes.get(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE))

    @filepath_executable.setter
    def filepath_executable(self, value: str) -> None:
        """Set the relative filepath of the executable that this code represents.

        :param value: The relative filepath of the executable within the directory of uploaded files.
        """
        type_check(value, str)

        if pathlib.PurePosixPath(value).is_absolute():
            raise ValueError('The `filepath_executable` should not be absolute.')

        self.base.attributes.set(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, value)

    @classmethod
    def _get_cli_options(cls) -> dict:
        """Return the CLI options that would allow to create an instance of this class."""
        options = {
            'filepath_executable': {
                'short_name': '-X',
                'required': True,
                'type': click.STRING,
                'prompt': 'Relative filepath executable',
                'help': 'Relative filepath of executable with directory of code files.',
            },
            'filepath_files': {
                'short_name': '-F',
                'required': True,
                'type': click.Path(exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path),
                'prompt': 'Code directory',
                'help': 'Filepath to directory containing code files.',
            }
        }
        options.update(**super()._get_cli_options())

        return options
