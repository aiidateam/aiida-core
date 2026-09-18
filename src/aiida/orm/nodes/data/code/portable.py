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

import logging
import pathlib
import typing as t

from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.folders import Folder
from aiida.common.lang import type_check
from aiida.common.typing import FilePath
from aiida.orm.cli import CliFieldInfo
from aiida.orm.decorators.attributes import attribute
from aiida.orm.models.adapters import PathStrAdapter
from aiida.orm.nodes.data.code.abstract import AbstractCode

if t.TYPE_CHECKING:
    from aiida.orm.computers import Computer

__all__ = ('PortableCode',)

_LOGGER = logging.getLogger(__name__)


class PortableCode(AbstractCode):
    """Data plugin representing an executable code stored in AiiDA's storage."""

    _KEY_ATTRIBUTE_FILEPATH_EXECUTABLE: str = 'filepath_executable'

    @classmethod
    def from_directory(
        cls,
        filepath_executable: FilePath,
        filepath_files: FilePath,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a portable code from a directory containing the code files.

        .. note:: If the files necessary for this code are not all located in a single directory or the directory
            contains files that should not be uploaded, construct the node normally and use the methods of the
            :class:`aiida.orm.nodes.repository.NodeRepository` class. This can be accessed through the
            ``base.repository`` attribute of the instance.

        :param filepath_executable: The relative filepath of the executable within the directory of uploaded files.
        :param filepath_files: The filepath to the directory containing all the files of the code.
        """
        type_check(filepath_files, (pathlib.PurePath, str))

        filepath_files_path = pathlib.Path(filepath_files)

        if not filepath_files_path.exists():
            msg = f'The filepath `{filepath_files}` does not exist.'
            raise ValueError(msg)

        if not filepath_files_path.is_dir():
            msg = f'The filepath `{filepath_files}` is not a directory.'
            raise ValueError(msg)

        node = cls(
            attributes={
                cls._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE: str(filepath_executable),
            },
            **kwargs,
        )
        node.base.repository.put_object_from_tree(str(filepath_files_path))

        return node

    @attribute(
        model_adapter=PathStrAdapter(),
        cli_field_info=CliFieldInfo(
            short_name='-X',
            priority=1,
        ),
    )
    def filepath_executable(self) -> pathlib.PurePath:
        """The relative filepath of the executable that this code represents."""
        return pathlib.PurePath(self.base.attributes.get(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE))

    @filepath_executable.setter
    def filepath_executable(self, value: FilePath) -> None:
        type_check(value, (str, pathlib.PurePath))

        if pathlib.PurePath(value).is_absolute():
            raise ValueError('The `filepath_executable` should not be absolute.')

        self.base.attributes.set(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, str(value))

    @property
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """
        return self.label

    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        A ``PortableCode`` should be able to be run on any computer in principle.

        :param computer: The computer.
        :return: ``True`` if the provided computer is the same as the one configured for this code.
        """
        return True

    def get_executable(self) -> pathlib.PurePath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """
        return self.filepath_executable

    def validate_working_directory(self, folder: Folder) -> None:
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
            msg = f'The plugin created a file {self.filepath_executable} that is also the executable name!'
            raise exceptions.PluginInternalError(msg)

    def get_executable_cmdline_params(self, cmdline_params: list[str] | None = None) -> list[str]:
        """Return the list of executable with its command line parameters.

        :param cmdline_params: List of command line parameters provided by the ``CalcJob`` plugin.
        :return: List of the executable followed by its command line parameters.
        """
        executable = self.get_executable()

        # Add './' if the executable is in the top folder (and not in a subfolder)
        # otherwise a bash shell will not execute it (by default, `./` is not in the PATH).
        if str(executable.parent) == '.':
            str_executable = f'./{executable}'
        else:
            str_executable = str(executable)

        return [str_executable] + (cmdline_params or [])

    def _validate(self) -> None:
        """Validate the instance by checking that an executable is defined and it is part of the repository files.

        :raises :class:`aiida.common.exceptions.ValidationError`: If the state of the node is invalid.
        """
        super()._validate()

        try:
            filepath_executable = self.filepath_executable
        except (AttributeError, TypeError) as exc:
            raise exceptions.ValidationError('The `filepath_executable` is not set.') from exc

        try:
            with self.base.repository.open(filepath_executable, 'r'):
                # Try opening the file to see if it's in the repository.
                # Note: we don't just check `self.base.repository.list_object_names()`
                # since the file could be in a subdirectory.
                pass
        except FileNotFoundError as exc:
            msg = f'The executable `{filepath_executable}` is not one of the uploaded files in the node repository.'
            raise exceptions.ValidationError(msg) from exc

    def _export_filepath_files_from_repo(
        self,
        repository_dump_path: pathlib.Path | None = None,
        written: bool = False,
    ) -> str:
        """Export repository contents to a directory.

        :param repository_dump_path: the path to which the repository contents should be dumped. If not provided,
            a temporary directory will be created and used.
        :param written: whether the repository content was already written.
        """
        import tempfile

        if not written:
            if repository_dump_path is None:
                repository_dump_path = pathlib.Path(tempfile.mkdtemp()) / self.label

            repository_dump_path.mkdir(parents=True, exist_ok=True)

            for root, _, filenames in self.base.repository.walk():
                for filename in filenames:
                    rel_path = root / filename
                    export_path = repository_dump_path / rel_path
                    export_path.parent.mkdir(parents=True, exist_ok=True)
                    export_path.write_bytes(self.base.repository.get_object_content(str(rel_path), mode='rb'))

        return str(repository_dump_path)

    def _prepare_yaml(self, *args: t.Any, **kwargs: t.Any) -> tuple[bytes, dict]:
        """Export code to a YAML file."""
        import yaml

        target = pathlib.Path.cwd() / self.label
        context = {
            'repository_dump_path': target,
            'written': False,
        }

        code_data = type(self).cli_spec.serialize(self, context=context)
        code_data['filepath_files'] = self._export_filepath_files_from_repo(target)

        _LOGGER.info(f'Repository files for PortableCode <{self.pk}> dumped to folder `{target}`.')

        return yaml.dump(code_data, sort_keys=kwargs.get('sort', False), encoding='utf-8'), {}
