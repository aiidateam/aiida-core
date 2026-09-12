###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Parser for a :class:`~aiida.calculations.shell.ShellJob` job."""

from __future__ import annotations

import pathlib
import re
import typing as t

from aiida.calculations.shell import ShellJob
from aiida.engine import ExitCode
from aiida.orm import Data, FolderData, SinglefileData
from aiida.parsers.parser import Parser


class ShellParser(Parser):
    """Parser for a :class:`~aiida.calculations.shell.ShellJob` job."""

    def parse(self, **kwargs: t.Any) -> ExitCode:
        """Parse the contents of the output files stored in the ``retrieved`` output node."""
        dirpath = pathlib.Path(kwargs['retrieved_temporary_folder'])

        missing_filepaths = self.parse_custom_outputs(dirpath)
        exit_code = self.parse_default_outputs(dirpath)

        if 'parser' in self.node.inputs:
            try:
                self.call_parser_hook(dirpath)
            except Exception as exception:
                return self.exit_code('ERROR_PARSER_HOOK_EXCEPTED', exception=exception)

        if missing_filepaths:
            return self.exit_code('ERROR_OUTPUT_FILEPATHS_MISSING', missing_filepaths=', '.join(missing_filepaths))

        return exit_code

    def exit_code(self, key: str, **kwargs: t.Any) -> ExitCode:
        """Return the exit code corresponding to the given key.

        :param key: The key under which the exit code is registered.
        :param kwargs: Any keyword arguments to format the exit code message.
        :returns: The formatted exit code.
        """
        exit_code: ExitCode = getattr(self.exit_codes, key).format(**kwargs)
        return exit_code

    @staticmethod
    def format_link_label(filename: str) -> str:
        """Format the link label from a given filename.

        Valid link labels can only contain alphanumeric characters and underscores, without consecutive underscores.
        They can also not start with a number. So all characters that are not alphanumeric or an underscore are
        converted to underscores, where consecutive underscores are merged into one. Filenames that start with a number
        are prefixed with ``aiida_shell_``.

        :param filename: The filename.
        :returns: The link label.
        """
        if re.match('^[0-9]+.*', filename):
            filename = f'aiida_shell_{filename}'

        alphanumeric = re.sub('[^0-9a-zA-Z_]+', '_', filename)
        link_label = re.sub('_[_]+', '_', alphanumeric)
        return link_label

    def parse_default_outputs(self, dirpath: pathlib.Path) -> ExitCode:
        """Parse the output files that should have been retrieved by default.

        :param dirpath: Directory containing the retrieved files.
        :returns: An exit code.
        """
        try:
            with (dirpath / ShellJob.FILENAME_STDERR).open(mode='rb') as handle:
                node_stderr = SinglefileData(handle, filename=ShellJob.FILENAME_STDERR)
        except FileNotFoundError:
            stderr = ''
        else:
            stderr = node_stderr.get_content(mode='r')
            self.out(ShellJob.FILENAME_STDERR, node_stderr)

        filename_stdout = self.node.get_option('output_filename') or ShellJob.FILENAME_STDOUT

        try:
            with (dirpath / filename_stdout).open(mode='rb') as handle:
                node_stdout = SinglefileData(handle, filename=filename_stdout)
        except FileNotFoundError:
            return self.exit_code('ERROR_OUTPUT_STDOUT_MISSING')

        self.out(self.format_link_label(filename_stdout), node_stdout)

        try:
            exit_status = int((dirpath / ShellJob.FILENAME_STATUS).read_text())
        except FileNotFoundError:
            return self.exit_code('ERROR_OUTPUT_STATUS_MISSING')
        except ValueError:
            return self.exit_code('ERROR_OUTPUT_STATUS_INVALID')

        if exit_status != 0:
            return self.exit_code('ERROR_COMMAND_FAILED', status=exit_status, stderr=stderr)

        if stderr:
            return self.exit_code('ERROR_STDERR_NOT_EMPTY')

        return ExitCode()

    def parse_custom_outputs(self, dirpath: pathlib.Path) -> list[str]:
        """Parse the output files that have been requested through the ``outputs`` input.

        :param dirpath: Directory containing the retrieved files.
        :returns: List of missing output filepaths.
        """
        if 'outputs' not in self.node.inputs:
            return []

        missing_filepaths = []

        for filename in self.node.inputs.outputs.get_list():
            for filepath in dirpath.glob(filename) if '*' in filename else (dirpath / filename,):
                if not filepath.exists():
                    missing_filepaths.append(filepath.name)
                    continue

                if filepath.is_file():
                    self.out(self.format_link_label(filepath.name), SinglefileData(filepath, filename=filepath.name))
                else:
                    self.out(self.format_link_label(filepath.name), FolderData(tree=filepath))

        return missing_filepaths

    def call_parser_hook(self, dirpath: pathlib.Path) -> None:
        """Execute the ``parser`` custom parser hook that was passed as input to the ``ShellJob``."""
        from inspect import signature

        unpickled_parser = self.node.inputs.parser.load()
        parser_signature = signature(unpickled_parser)

        if 'parser' in parser_signature.parameters:
            results = unpickled_parser(dirpath, self) or {}
        else:
            results = unpickled_parser(dirpath) or {}

        if not isinstance(results, dict) or any(not isinstance(value, Data) for value in results.values()):
            msg = f'{unpickled_parser} did not return a dictionary of `Data` nodes but: {results}'
            raise TypeError(msg)

        for key, value in results.items():
            self.out(key, value)
