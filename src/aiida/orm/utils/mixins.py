###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Mixin classes for ORM classes."""

from __future__ import annotations

import inspect

import pydantic

from aiida.common import exceptions
from aiida.common.lang import classproperty, override, type_check
from aiida.common.pydantic import MetadataField
from aiida.common.warnings import warn_deprecation


class FunctionCalculationMixin:
    """This mixin should be used for ProcessNode subclasses that are used to record the execution
    of a python function. For example the process nodes that are used for a function that
    was wrapped by the `workfunction` or `calcfunction` function decorators. The `store_source_info`
    method can then be called with the wrapped function to store information about that function
    in the calculation node through the inspect module. Various property getters are defined to
    later retrieve that information from the node
    """

    FUNCTION_NAME_KEY = 'function_name'
    FUNCTION_NAMESPACE_KEY = 'function_namespace'
    FUNCTION_STARTING_LINE_KEY = 'function_starting_line_number'
    FUNCTION_NUMBER_OF_LINES_KEY = 'function_number_of_lines'
    FUNCTION_SOURCE_FILE_PATH = 'source_file'

    def store_source_info(self, func) -> None:
        """Retrieve source information about the wrapped function `func` through the inspect module,
        and store it in the attributes and repository of the node. The function name, namespace
        and the starting line number in the source file will be stored in the attributes. The
        source file itself will be copied into the repository

        :param func: the function to inspect and whose information to store in the node
        """
        self._set_function_name(func.__name__)

        try:
            source_list, starting_line_number = inspect.getsourcelines(func)
        except OSError:
            pass
        else:
            self._set_function_starting_line_number(starting_line_number)
            self._set_function_number_of_lines(len(source_list))

        try:
            self._set_function_namespace(func.__globals__['__name__'])
        except Exception:
            pass

        try:
            source_file_path = inspect.getsourcefile(func)
            if source_file_path:
                with open(source_file_path, 'rb') as handle:
                    self.base.repository.put_object_from_filelike(  # type: ignore[attr-defined]
                        handle, self.FUNCTION_SOURCE_FILE_PATH
                    )
        except OSError:
            pass

    @property
    def function_name(self) -> str | None:
        """Return the function name of the wrapped function.

        :returns: the function name or None
        """
        return self.base.attributes.get(self.FUNCTION_NAME_KEY, None)  # type: ignore[attr-defined]

    def _set_function_name(self, function_name: str):
        """Set the function name of the wrapped function.

        :param function_name: the function name
        """
        self.base.attributes.set(self.FUNCTION_NAME_KEY, function_name)  # type: ignore[attr-defined]

    @property
    def function_namespace(self) -> str | None:
        """Return the function namespace of the wrapped function.

        :returns: the function namespace or None
        """
        return self.base.attributes.get(self.FUNCTION_NAMESPACE_KEY, None)  # type: ignore[attr-defined]

    def _set_function_namespace(self, function_namespace: str) -> None:
        """Set the function namespace of the wrapped function.

        :param function_namespace: the function namespace
        """
        self.base.attributes.set(self.FUNCTION_NAMESPACE_KEY, function_namespace)  # type: ignore[attr-defined]

    @property
    def function_starting_line_number(self) -> int | None:
        """Return the starting line number of the wrapped function in its source file.

        :returns: the starting line number or None
        """
        return self.base.attributes.get(self.FUNCTION_STARTING_LINE_KEY, None)  # type: ignore[attr-defined]

    def _set_function_starting_line_number(self, function_starting_line_number: int) -> None:
        """Set the starting line number of the wrapped function in its source file.

        :param function_starting_line_number: the starting line number
        """
        self.base.attributes.set(  # type: ignore[attr-defined]
            self.FUNCTION_STARTING_LINE_KEY, function_starting_line_number
        )

    @property
    def function_number_of_lines(self) -> int | None:
        """Return the number of lines of the wrapped function in its source file.

        :returns: the number of lines or None
        """
        return self.base.attributes.get(self.FUNCTION_NUMBER_OF_LINES_KEY, None)  # type: ignore[attr-defined]

    def _set_function_number_of_lines(self, function_number_of_lines: int) -> None:
        """Set the number of lines of the wrapped function in its source file.

        :param function_number_of_lines: the number of lines
        """
        type_check(function_number_of_lines, int)
        self.base.attributes.set(  # type: ignore[attr-defined]
            self.FUNCTION_NUMBER_OF_LINES_KEY, function_number_of_lines
        )

    def get_function_source_code(self) -> str | None:
        """Return the source code of the function stored in the repository.

        If the source code file does not exist, this will return ``None`` instead. This can happen for example when the
        function was defined in an interactive shell in which case ``store_source_info`` will have failed to retrieve
        the source code using ``inspect.getsourcefile``.

        :returns: The source code of the function or ``None`` if it could not be determined when storing the node.
        """
        warn_deprecation('This method will be removed, use `get_source_code_file` instead.', version=3)

        return self.get_source_code_file()

    def get_source_code_file(self) -> str | None:
        """Return the source code of the file in which the process function was defined.

        If the source code file does not exist, this will return ``None`` instead. This can happen for example when the
        function was defined in an interactive shell in which case ``store_source_info`` will have failed to retrieve
        the source code using ``inspect.getsourcefile``.

        :returns: The source code of the function or ``None`` if it could not be determined when storing the node.
        """
        try:
            return self.base.repository.get_object_content(self.FUNCTION_SOURCE_FILE_PATH)  # type: ignore[attr-defined]
        except FileNotFoundError:
            return None

    def get_source_code_function(self) -> str | None:
        """Return the source code of the function including the decorator.

        :returns: The source code of the function or ``None`` if not available.
        """
        source_code = self.get_source_code_file()

        if source_code is None or self.function_number_of_lines is None or self.function_starting_line_number is None:
            return None

        content_list = source_code.splitlines()
        start_line = self.function_starting_line_number
        end_line = start_line + self.function_number_of_lines

        # Start at ``start_line - 1`` to include the decorator
        return '\n'.join(content_list[start_line - 1 : end_line])


class Sealable:
    """Mixin to mark a Node as `sealable`."""

    SEALED_KEY = 'sealed'

    class AttributesModel(pydantic.BaseModel, defer_build=True):
        sealed: bool = MetadataField(description='Whether the node is sealed')

    @classproperty
    def _updatable_attributes(cls) -> tuple[str, ...]:  # noqa: N805
        return (cls.SEALED_KEY,)

    @property
    def sealed(self) -> bool:
        return self.base.attributes.get(self.SEALED_KEY, False)  # type: ignore[attr-defined]

    @property
    def is_sealed(self) -> bool:
        """Returns whether the node is sealed, i.e. whether the sealed attribute has been set to True."""
        return self.sealed

    def seal(self) -> 'Sealable':
        """Seal the node by setting the sealed attribute to True."""
        if not self.is_sealed:
            self.base.attributes.set(self.SEALED_KEY, True)  # type: ignore[attr-defined]

        return self

    @override
    def _check_mutability_attributes(self, keys: list[str] | None = None) -> None:
        """Check if the entity is mutable and raise an exception if not.

        This is called from `NodeAttributes` methods that modify the attributes.

        :param keys: the keys that will be mutated, or all if None
        """
        if self.is_sealed:
            raise exceptions.ModificationNotAllowed('attributes of a sealed node are immutable')

        if self.is_stored:  # type: ignore[attr-defined]
            # here we are more lenient than the base class, since we allow the modification of some attributes
            if keys is None:
                raise exceptions.ModificationNotAllowed('Cannot bulk modify attributes of a stored+unsealed node')
            elif any(key not in self._updatable_attributes for key in keys):
                raise exceptions.ModificationNotAllowed(
                    f'Cannot modify non-updatable attributes of a stored+unsealed node: {keys}'
                )
