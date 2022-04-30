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

from aiida.common.lang import type_check
from aiida.orm import Computer

from ..data import Data

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
        default_calc_job_plugin: str = None,
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
    def get_executable(self) -> str:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """

    @property
    @abc.abstractmethod
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """

    @Data.label.setter
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
