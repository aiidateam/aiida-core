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

from aiida.common import exceptions
from aiida.common.lang import classproperty, override, type_check
from aiida.orm.decorators import attribute


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

    @attribute
    def function_name(self) -> str | None:
        """The function name of the wrapped function."""
        return self.base.attributes.get(self.FUNCTION_NAME_KEY, None)

    @function_name.setter
    def function_name(self, function_name: str) -> None:
        self.base.attributes.set(self.FUNCTION_NAME_KEY, function_name)

    @attribute
    def function_namespace(self) -> str | None:
        """The function namespace of the wrapped function."""
        return self.base.attributes.get(self.FUNCTION_NAMESPACE_KEY, None)

    @function_namespace.setter
    def function_namespace(self, function_namespace: str) -> None:
        self.base.attributes.set(self.FUNCTION_NAMESPACE_KEY, function_namespace)

    @attribute
    def function_starting_line_number(self) -> int | None:
        """The starting line number of the wrapped function in its source file."""
        return self.base.attributes.get(self.FUNCTION_STARTING_LINE_KEY, None)

    @function_starting_line_number.setter
    def function_starting_line_number(self, function_starting_line_number: int) -> None:
        self.base.attributes.set(self.FUNCTION_STARTING_LINE_KEY, function_starting_line_number)

    @attribute
    def function_number_of_lines(self) -> int | None:
        """The number of lines of the wrapped function in its source file."""
        return self.base.attributes.get(self.FUNCTION_NUMBER_OF_LINES_KEY, None)

    @function_number_of_lines.setter
    def function_number_of_lines(self, function_number_of_lines: int) -> None:
        type_check(function_number_of_lines, int)
        self.base.attributes.set(self.FUNCTION_NUMBER_OF_LINES_KEY, function_number_of_lines)

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

    # TODO the following methods are handled above via property operations - consider removing

    def _set_function_name(self, function_name: str):
        """Set the function name of the wrapped function.

        :param function_name: the function name
        """
        self.function_name = function_name

    def _set_function_namespace(self, function_namespace: str) -> None:
        """Set the function namespace of the wrapped function.

        :param function_namespace: the function namespace
        """
        self.function_namespace = function_namespace

    def _set_function_starting_line_number(self, function_starting_line_number: int) -> None:
        """Set the starting line number of the wrapped function in its source file.

        :param function_starting_line_number: the starting line number
        """
        self.function_starting_line_number = function_starting_line_number

    def _set_function_number_of_lines(self, function_number_of_lines: int) -> None:
        """Set the number of lines of the wrapped function in its source file.

        :param function_number_of_lines: the number of lines
        """
        self.function_number_of_lines = function_number_of_lines


class Sealable:
    """Mixin to mark a Node as `sealable`."""

    SEALED_KEY = 'sealed'

    @attribute
    def sealed(self) -> bool:
        """Whether the node is sealed."""
        return self.base.attributes.get(self.SEALED_KEY, False)

    @sealed.setter
    def sealed(self, value: bool) -> None:
        self.base.attributes.set(self.SEALED_KEY, value)

    @property
    def is_sealed(self) -> bool:
        """Returns whether the node is sealed, i.e. whether the sealed attribute has been set to True."""
        return self.sealed

    def seal(self) -> Sealable:
        """Seal the node by setting the sealed attribute to True."""
        if not self.is_sealed:
            self.sealed = True

        return self

    @classproperty
    def _updatable_attributes(cls) -> tuple[str, ...]:  # noqa: N805
        return (cls.SEALED_KEY,)

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
                msg = f'Cannot modify non-updatable attributes of a stored+unsealed node: {keys}'
                raise exceptions.ModificationNotAllowed(msg)
