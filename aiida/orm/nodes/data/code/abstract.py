# -*- coding: utf-8 -*-
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
import collections
import pathlib
from typing import TYPE_CHECKING

import click

from aiida.cmdline.params.options.interactive import TemplateInteractiveOption
from aiida.common import exceptions
from aiida.common.folders import Folder
from aiida.common.lang import type_check
from aiida.orm import Computer
from aiida.plugins import CalculationFactory

from ..data import Data

if TYPE_CHECKING:
    from aiida.engine import ProcessBuilder

__all__ = ('AbstractCode',)


class AbstractCode(Data, metaclass=abc.ABCMeta):
    """Abstract data plugin representing an executable code."""

    # Should become ``default_calc_job_plugin`` once ``Code`` is dropped in ``aiida-core==3.0``
    _KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN: str = 'input_plugin'
    _KEY_ATTRIBUTE_APPEND_TEXT: str = 'append_text'
    _KEY_ATTRIBUTE_PREPEND_TEXT: str = 'prepend_text'
    _KEY_ATTRIBUTE_USE_DOUBLE_QUOTES: str = 'use_double_quotes'
    _KEY_EXTRA_IS_HIDDEN: str = 'hidden'  # Should become ``is_hidden`` once ``Code`` is dropped

    def __init__(
        self,
        default_calc_job_plugin: str | None = None,
        append_text: str = '',
        prepend_text: str = '',
        use_double_quotes: bool = False,
        is_hidden: bool = False,
        **kwargs
    ):
        """Construct a new instance.

        :param default_calc_job_plugin: The entry point name of the default ``CalcJob`` plugin to use.
        :param append_text: The text that should be appended to the run line in the job script.
        :param prepend_text: The text that should be prepended to the run line in the job script.
        :param use_double_quotes: Whether the command line invocation of this code should be escaped with double quotes.
        :param is_hidden: Whether the code is hidden.
        """
        super().__init__(**kwargs)
        self.default_calc_job_plugin = default_calc_job_plugin
        self.append_text = append_text
        self.prepend_text = prepend_text
        self.use_double_quotes = use_double_quotes
        self.use_double_quotes = use_double_quotes
        self.is_hidden = is_hidden

    @abc.abstractmethod
    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        :param computer: The computer.
        :return: ``True`` if the code can run on ``computer``, ``False`` otherwise.
        """

    @abc.abstractmethod
    def get_executable(self) -> pathlib.PurePosixPath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """

    def get_executable_cmdline_params(self, cmdline_params: list[str] | None = None) -> list:
        """Return the list of executable with its command line parameters.

        :param cmdline_params: List of command line parameters provided by the ``CalcJob`` plugin.
        :return: List of the executable followed by its command line parameters.
        """
        return [str(self.get_executable())] + (cmdline_params or [])

    def get_prepend_cmdline_params( # pylint: disable=no-self-use
        self,
        mpi_args: list[str] | None = None,
        extra_mpirun_params: list[str] | None = None
    ) -> list[str]:
        """Return List of command line parameters to be prepended to the executable in submission line.
        These command line parameters are typically parameters related to MPI invocations.

        :param mpi_args: List of MPI parameters provided by the ``Computer.get_mpirun_command`` method.
        :param extra_mpiruns_params: List of MPI parameters provided by the ``metadata.options.extra_mpirun_params``
            input of the ``CalcJob``.
        :return: List of command line parameters to be prepended to the executable in submission line.
        """
        return (mpi_args or []) + (extra_mpirun_params or [])

    def validate_working_directory(self, folder: Folder):
        """Validate content of the working directory created by the :class:`~aiida.engine.CalcJob` plugin.

        This method will be called by :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.presubmit` when a new
        calculation job is launched, passing the :class:`~aiida.common.folders.Folder` that was used by the plugin used
        for the calculation to create the input files for the working directory. This method can be overridden by
        implementations of the ``AbstractCode`` class that need to validate the contents of that folder.

        :param folder: A sandbox folder that the ``CalcJob`` plugin wrote input files to that will be copied to the
            working directory for the corresponding calculation job instance.
        :raises PluginInternalError: If the content of the sandbox folder is not valid.
        """

    @property
    @abc.abstractmethod
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """

    @property
    def label(self) -> str:
        """Return the label.

        :return: The label.
        """
        return self.backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        """Set the label.

        The label cannot contain any ``@`` symbols.

        :param value: The new label.
        :raises ValueError: If the label contains invalid characters.
        """
        type_check(value, str)

        if '@' in value:
            raise ValueError('The label contains a `@` symbol, which is not allowed.')

        self.backend_entity.label = value

    @property
    def default_calc_job_plugin(self) -> str | None:
        """Return the optional default ``CalcJob`` plugin.

        :return: The entry point name of the default ``CalcJob`` plugin to use.
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN, None)

    @default_calc_job_plugin.setter
    def default_calc_job_plugin(self, value: str | None) -> None:
        """Set the default ``CalcJob`` plugin.

        :param value: The entry point name of the default ``CalcJob`` plugin to use.
        """
        type_check(value, str, allow_none=True)
        self.base.attributes.set(self._KEY_ATTRIBUTE_DEFAULT_CALC_JOB_PLUGIN, value)

    @property
    def append_text(self) -> str:
        """Return the text that should be appended to the run line in the job script.

        :return: The text that should be appended to the run line in the job script.
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_APPEND_TEXT, '')

    @append_text.setter
    def append_text(self, value: str) -> None:
        """Set the text that should be appended to the run line in the job script.

        :param value: The text that should be appended to the run line in the job script.
        """
        type_check(value, str, allow_none=True)
        self.base.attributes.set(self._KEY_ATTRIBUTE_APPEND_TEXT, value)

    @property
    def prepend_text(self) -> str:
        """Return the text that should be prepended to the run line in the job script.

        :return: The text that should be prepended to the run line in the job script.
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_PREPEND_TEXT, '')

    @prepend_text.setter
    def prepend_text(self, value: str) -> None:
        """Set the text that should be prepended to the run line in the job script.

        :param value: The text that should be prepended to the run line in the job script.
        """
        type_check(value, str, allow_none=True)
        self.base.attributes.set(self._KEY_ATTRIBUTE_PREPEND_TEXT, value)

    @property
    def use_double_quotes(self) -> bool:
        """Return whether the command line invocation of this code should be escaped with double quotes.

        :return: ``True`` if to escape with double quotes, ``False`` otherwise.
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_USE_DOUBLE_QUOTES, False)

    @use_double_quotes.setter
    def use_double_quotes(self, value: bool) -> None:
        """Set whether the command line invocation of this code should be escaped with double quotes.

        :param value: ``True`` if to escape with double quotes, ``False`` otherwise.
        """
        type_check(value, bool)
        self.base.attributes.set(self._KEY_ATTRIBUTE_USE_DOUBLE_QUOTES, value)

    @property
    def is_hidden(self) -> bool:
        """Return whether the code is hidden.

        :return: ``True`` if the code is hidden, ``False`` otherwise, which is also the default.
        """
        return self.base.extras.get(self._KEY_EXTRA_IS_HIDDEN, False)

    @is_hidden.setter
    def is_hidden(self, value: bool) -> None:
        """Define whether the code is hidden or not.

        :param value: ``True`` if the code should be hidden, ``False`` otherwise.
        """
        type_check(value, bool)
        self.base.extras.set(self._KEY_EXTRA_IS_HIDDEN, value)

    def get_builder(self) -> 'ProcessBuilder':
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
            raise exceptions.EntryPointError(f'The calculation entry point `{entry_point}` could not be loaded')

        builder = process_class.get_builder()  # type: ignore
        builder.code = self

        return builder

    @staticmethod
    def cli_validate_label_uniqueness(_, __, value):
        """Validate the uniqueness of the label of the code."""
        from aiida.orm import load_code

        try:
            load_code(value)
        except exceptions.NotExistent:
            pass
        except exceptions.MultipleObjectsError:
            raise click.BadParameter(f'Multiple codes with the label `{value}` already exist.')
        else:
            raise click.BadParameter(f'A code with the label `{value}` already exists.')

        return value

    @classmethod
    def get_cli_options(cls) -> collections.OrderedDict:
        """Return the CLI options that would allow to create an instance of this class."""
        return collections.OrderedDict(cls._get_cli_options())

    @classmethod
    def _get_cli_options(cls) -> dict:
        """Return the CLI options that would allow to create an instance of this class."""
        return {
            'label': {
                'short_name': '-L',
                'required': True,
                'type': click.STRING,
                'prompt': 'Label',
                'help': 'A unique label to identify the code by.',
                'callback': cls.cli_validate_label_uniqueness,
            },
            'description': {
                'short_name': '-D',
                'type': click.STRING,
                'prompt': 'Description',
                'help': 'Human-readable description of this code ideally including version and compilation environment.'
            },
            'default_calc_job_plugin': {
                'short_name': '-P',
                'type': click.STRING,
                'prompt': 'Default `CalcJob` plugin',
                'help': 'Entry point name of the default plugin (as listed in `verdi plugin list aiida.calculations`).'
            },
            'prepend_text': {
                'cls': TemplateInteractiveOption,
                'type': click.STRING,
                'default': '',
                'prompt': 'Prepend script',
                'help': 'Bash commands that should be prepended to the run line in all submit scripts for this code.',
                'extension': '.bash',
                'header': 'PREPEND_TEXT: if there is any bash commands that should be prepended to the executable call '
                'in all submit scripts for this code, type that between the equal signs below and save the file.',
                'footer': 'All lines that start with `#=`: will be ignored.'
            },
            'append_text': {
                'cls': TemplateInteractiveOption,
                'type': click.STRING,
                'default': '',
                'prompt': 'Append script',
                'help': 'Bash commands that should be appended to the run line in all submit scripts for this code.',
                'extension': '.bash',
                'header': 'APPEND_TEXT: if there is any bash commands that should be appended to the executable call '
                'in all submit scripts for this code, type that between the equal signs below and save the file.',
                'footer': 'All lines that start with `#=`: will be ignored.'
            },
            'use_double_quotes': {
                'is_flag': True,
                'default': False,
                'help': 'Whether the executable and arguments of the code in the submission script should be escaped '
                'with single or double quotes.',
                'prompt': 'Escape using double quotes',
            },
        }
