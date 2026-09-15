###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract data plugin representing an executable code."""

from __future__ import annotations

import abc
import functools
import pathlib
import typing as t

import pydantic as pdt

from aiida.cmdline.params.options.interactive import TemplateInteractiveOption
from aiida.common import exceptions
from aiida.common.folders import Folder
from aiida.common.lang import type_check
from aiida.orm.cli import CliFieldInfo
from aiida.orm.decorators import attribute, column
from aiida.orm.nodes.data.data import Data
from aiida.plugins import CalculationFactory

if t.TYPE_CHECKING:
    from aiida.engine import ProcessBuilder
    from aiida.orm.computers import Computer

__all__ = ('AbstractCode',)


class AbstractCode(Data, metaclass=abc.ABCMeta):
    """Abstract data plugin representing an executable code."""

    KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN: str = 'default_calc_job_plugin'
    KEY_ATTRIBUTE_APPEND_TEXT: str = 'append_text'
    KEY_ATTRIBUTE_PREPEND_TEXT: str = 'prepend_text'
    KEY_ATTRIBUTE_USE_DOUBLE_QUOTES: str = 'use_double_quotes'
    KEY_ATTRIBUTE_WITH_MPI: str = 'with_mpi'
    KEY_ATTRIBUTE_WRAP_CMDLINE_PARAMS: str = 'wrap_cmdline_params'
    KEY_EXTRA_IS_HIDDEN: str = 'is_hidden'

    def __str__(self):
        if self.computer is None:
            return f"Local code '{self.label}' pk: {self.pk}, uuid: {self.uuid}"

        return f"Remote code '{self.label}' on {self.computer.label} pk: {self.pk}, uuid: {self.uuid}"

    @column(
        updatable=True,
        cli_field_info=CliFieldInfo(priority=4),
    )
    def label(self) -> str:
        """The unique label of the code."""
        return self.backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        type_check(value, str)

        if '@' in value:
            raise ValueError('The label contains a `@` symbol, which is not allowed.')

        self.backend_entity.label = value

    @column(
        updatable=True,
        model_field_info=pdt.fields.FieldInfo(default=''),
        cli_field_info=CliFieldInfo(priority=3),
    )
    def description(self) -> str:
        """The description of the code."""
        return self.backend_entity.description

    @description.setter
    def description(self, value: str) -> None:
        type_check(value, str)
        self.backend_entity.description = value

    @attribute
    def default_calc_job_plugin(self) -> str | None:
        """The entry point name of the default ``CalcJob`` plugin."""
        return self.base.attributes.get(self.KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN, None)

    @default_calc_job_plugin.setter
    def default_calc_job_plugin(self, value: str | None) -> None:
        type_check(value, str, allow_none=True)
        self.base.attributes.set(self.KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN, value)

    @attribute(model_field_info=pdt.fields.FieldInfo(default=False))
    def use_double_quotes(self) -> bool:
        """Whether the command line invocation of this code should be escaped with double quotes."""
        return self.base.attributes.get(self.KEY_ATTRIBUTE_USE_DOUBLE_QUOTES, False)

    @use_double_quotes.setter
    def use_double_quotes(self, value: bool) -> None:
        type_check(value, bool)
        self.base.attributes.set(self.KEY_ATTRIBUTE_USE_DOUBLE_QUOTES, value)

    @attribute
    def with_mpi(self) -> bool | None:
        """Whether the command should be run as an MPI program."""
        return self.base.attributes.get(self.KEY_ATTRIBUTE_WITH_MPI, None)

    @with_mpi.setter
    def with_mpi(self, value: bool | None) -> None:
        type_check(value, bool, allow_none=True)
        self.base.attributes.set(self.KEY_ATTRIBUTE_WITH_MPI, value)

    @attribute(model_field_info=pdt.fields.FieldInfo(default=False))
    def wrap_cmdline_params(self) -> bool:
        """Whether all command line parameters should be wrapped with double quotes to form a single argument."""
        return self.base.attributes.get(self.KEY_ATTRIBUTE_WRAP_CMDLINE_PARAMS, False)

    @wrap_cmdline_params.setter
    def wrap_cmdline_params(self, value: bool) -> None:
        type_check(value, bool)
        self.base.attributes.set(self.KEY_ATTRIBUTE_WRAP_CMDLINE_PARAMS, value)

    @attribute(
        model_field_info=pdt.fields.FieldInfo(
            default='',
            title='Append scripts',
        ),
        cli_field_info=CliFieldInfo(
            option_cls=functools.partial(
                TemplateInteractiveOption,
                extension='.bash',
                header='APPEND_TEXT: if there is any bash commands that should be appended to the executable call '
                'in all submit scripts for this code, type that between the equal signs below and save the file.',
                footer='All lines that start with `#=`: will be ignored.',
            ),
        ),
    )
    def append_text(self) -> str:
        """The text to add after the run line in the job script.

        This can include ``bash`` commands or other shell instructions to run after the main command,
        e.g., cleaning up temporary files, logging, etc.
        """
        return self.base.attributes.get(self.KEY_ATTRIBUTE_APPEND_TEXT, '')

    @append_text.setter
    def append_text(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTE_APPEND_TEXT, value)

    @attribute(
        model_field_info=pdt.fields.FieldInfo(
            default='',
            title='Prepend scripts',
        ),
        cli_field_info=CliFieldInfo(
            option_cls=functools.partial(
                TemplateInteractiveOption,
                extension='.bash',
                header='PREPEND_TEXT: if there is any bash commands that should be prepended to the executable call '
                'in all submit scripts for this code, type that between the equal signs below and save the file.',
                footer='All lines that start with `#=`: will be ignored.',
            ),
        ),
    )
    def prepend_text(self) -> str:
        """The text to add before the run line in the job script.

        This can include ``bash`` commands or other shell instructions to run before the main command,
        e.g., setting environment variables, loading modules, etc.
        """
        return self.base.attributes.get(self.KEY_ATTRIBUTE_PREPEND_TEXT, '')

    @prepend_text.setter
    def prepend_text(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTE_PREPEND_TEXT, value)

    @property
    @abc.abstractmethod
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """

    @property
    def is_hidden(self) -> bool:
        """Return whether the code is hidden.

        :return: ``True`` if the code is hidden, ``False`` otherwise, which is also the default.
        """
        return self.base.extras.get(self.KEY_EXTRA_IS_HIDDEN, False)

    @is_hidden.setter
    def is_hidden(self, value: bool) -> None:
        """Define whether the code is hidden or not.

        :param value: ``True`` if the code should be hidden, ``False`` otherwise.
        """
        type_check(value, bool)
        self.base.extras.set(self.KEY_EXTRA_IS_HIDDEN, value)

    @abc.abstractmethod
    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        :param computer: The computer.
        :return: ``True`` if the code can run on ``computer``, ``False`` otherwise.
        """

    def get_description(self):
        """Return a string description of this Code instance.

        :return: string description of this Code instance
        """
        return self.full_label

    @abc.abstractmethod
    def get_executable(self) -> pathlib.PurePath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """

    def get_executable_cmdline_params(self, cmdline_params: list[str] | None = None) -> list[str]:
        """Return the list of executable with its command line parameters.

        :param cmdline_params: List of command line parameters provided by the ``CalcJob`` plugin.
        :return: List of the executable followed by its command line parameters.
        """
        return [str(self.get_executable())] + (cmdline_params or [])

    def get_prepend_cmdline_params(
        self,
        mpi_args: list[str] | None = None,
        extra_mpirun_params: list[str] | None = None,
    ) -> list[str]:
        """Return List of command line parameters to be prepended to the executable in submission line.

        These command line parameters are typically parameters related to MPI invocations.

        :param mpi_args: List of MPI parameters provided by the ``Computer.get_mpirun_command`` method.
        :param extra_mpiruns_params: List of MPI parameters provided by the ``metadata.options.extra_mpirun_params``
            input of the ``CalcJob``.
        :return: List of command line parameters to be prepended to the executable in submission line.
        """
        return (mpi_args or []) + (extra_mpirun_params or [])

    def validate_working_directory(self, folder: Folder) -> None:
        """Validate content of the working directory created by the :class:`~aiida.engine.CalcJob` plugin.

        This method will be called by :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.presubmit` when a new
        calculation job is launched, passing the :class:`~aiida.common.folders.Folder` that was used by the plugin used
        for the calculation to create the input files for the working directory. This method can be overridden by
        implementations of the ``AbstractCode`` class that need to validate the contents of that folder.

        :param folder: A sandbox folder that the ``CalcJob`` plugin wrote input files to that will be copied to the
            working directory for the corresponding calculation job instance.
        :raises PluginInternalError: If the content of the sandbox folder is not valid.
        """

    def get_builder(self) -> ProcessBuilder:
        """Create and return a new ``ProcessBuilder`` for the ``CalcJob`` class of the plugin configured for this code.

        The configured calculation plugin class is defined by the ``default_calc_job_plugin`` property.

        .. note:: it also sets the ``builder.code`` value.

        :return: a ``ProcessBuilder`` instance with the ``code`` input already populated with ourselves
        :raise aiida.common.EntryPointError: if the specified plugin does not exist.
        :raise ValueError: if no default plugin was specified.
        """
        entry_point = self.default_calc_job_plugin

        if entry_point is None:
            raise ValueError('No default calculation input plugin specified for this code')

        try:
            process_class = CalculationFactory(entry_point)
        except exceptions.EntryPointError:
            msg = f'The calculation entry point `{entry_point}` could not be loaded'
            raise exceptions.EntryPointError(msg)

        builder = process_class.get_builder()  # type: ignore[union-attr]
        builder.code = self

        return builder

    def _prepare_yaml(self, *args, **kwargs):
        """Export code to a YAML file."""
        import yaml

        context = {'repository_dump_path': pathlib.Path.cwd() / self.label}
        code_data = type(self).cli_spec.serialize(self, context=context)

        return yaml.dump(code_data, sort_keys=kwargs.get('sort', False), encoding='utf-8'), {}

    def _prepare_yml(self, *args, **kwargs):
        """Also allow for export as .yml"""
        return self._prepare_yaml(*args, **kwargs)

    # TODO deprecated; update calls and remove

    def get_execname(self):
        """Return the executable string to be put in the script.
        For local codes, it is ./LOCAL_EXECUTABLE_NAME
        For remote codes, it is the absolute path to the executable.
        """
        return str(self.get_executable())
