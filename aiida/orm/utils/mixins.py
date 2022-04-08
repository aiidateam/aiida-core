# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Mixin classes for ORM classes."""
import inspect
from typing import List, Optional

from aiida.common import exceptions
from aiida.common.lang import classproperty, override


class FunctionCalculationMixin:
    """
    This mixin should be used for ProcessNode subclasses that are used to record the execution
    of a python function. For example the process nodes that are used for a function that
    was wrapped by the `workfunction` or `calcfunction` function decorators. The `store_source_info`
    method can then be called with the wrapped function to store information about that function
    in the calculation node through the inspect module. Various property getters are defined to
    later retrieve that information from the node
    """

    FUNCTION_NAME_KEY = 'function_name'
    FUNCTION_NAMESPACE_KEY = 'function_namespace'
    FUNCTION_STARTING_LINE_KEY = 'function_starting_line_number'
    FUNCTION_SOURCE_FILE_PATH = 'source_file'

    def store_source_info(self, func):
        """
        Retrieve source information about the wrapped function `func` through the inspect module,
        and store it in the attributes and repository of the node. The function name, namespace
        and the starting line number in the source file will be stored in the attributes. The
        source file itself will be copied into the repository

        :param func: the function to inspect and whose information to store in the node
        """
        self._set_function_name(func.__name__)

        try:
            _, starting_line_number = inspect.getsourcelines(func)
            self._set_function_starting_line_number(starting_line_number)
        except (IOError, OSError):
            pass

        try:
            self._set_function_namespace(func.__globals__['__name__'])
        except Exception:  # pylint: disable=broad-except
            pass

        try:
            source_file_path = inspect.getsourcefile(func)
            with open(source_file_path, 'rb') as handle:
                self.base.repository.put_object_from_filelike(handle, self.FUNCTION_SOURCE_FILE_PATH)
        except (IOError, OSError):
            pass

    @property
    def function_name(self):
        """Return the function name of the wrapped function.

        :returns: the function name or None
        """
        return self.base.attributes.get(self.FUNCTION_NAME_KEY, None)

    def _set_function_name(self, function_name):
        """Set the function name of the wrapped function.

        :param function_name: the function name
        """
        self.base.attributes.set(self.FUNCTION_NAME_KEY, function_name)

    @property
    def function_namespace(self):
        """Return the function namespace of the wrapped function.

        :returns: the function namespace or None
        """
        return self.base.attributes.get(self.FUNCTION_NAMESPACE_KEY, None)

    def _set_function_namespace(self, function_namespace):
        """Set the function namespace of the wrapped function.

        :param function_namespace: the function namespace
        """
        self.base.attributes.set(self.FUNCTION_NAMESPACE_KEY, function_namespace)

    @property
    def function_starting_line_number(self):
        """Return the starting line number of the wrapped function in its source file.

        :returns: the starting line number or None
        """
        return self.base.attributes.get(self.FUNCTION_STARTING_LINE_KEY, None)

    def _set_function_starting_line_number(self, function_starting_line_number):
        """Set the starting line number of the wrapped function in its source file.

        :param function_starting_line_number: the starting line number
        """
        self.base.attributes.set(self.FUNCTION_STARTING_LINE_KEY, function_starting_line_number)

    def get_function_source_code(self):
        """Return the absolute path to the source file in the repository.

        :returns: the absolute path of the source file in the repository, or None if it does not exist
        """
        return self.base.repository.get_object_content(self.FUNCTION_SOURCE_FILE_PATH)


class Sealable:
    """Mixin to mark a Node as `sealable`."""
    # pylint: disable=no-member,unsupported-membership-test

    SEALED_KEY = 'sealed'

    @classproperty
    def _updatable_attributes(cls):  # pylint: disable=no-self-argument
        return (cls.SEALED_KEY,)

    @property
    def is_sealed(self):
        """Returns whether the node is sealed, i.e. whether the sealed attribute has been set to True."""
        return self.base.attributes.get(self.SEALED_KEY, False)

    def seal(self):
        """Seal the node by setting the sealed attribute to True."""
        if not self.is_sealed:
            self.base.attributes.set(self.SEALED_KEY, True)

    @override
    def _check_mutability_attributes(self, keys: Optional[List[str]] = None) -> None:  # pylint: disable=unused-argument
        """Check if the entity is mutable and raise an exception if not.

        This is called from `NodeAttributes` methods that modify the attributes.

        :param keys: the keys that will be mutated, or all if None
        """
        if self.is_sealed:
            raise exceptions.ModificationNotAllowed('attributes of a sealed node are immutable')

        if self.is_stored:
            # here we are more lenient than the base class, since we allow the modification of some attributes
            if keys is None:
                raise exceptions.ModificationNotAllowed('Cannot bulk modify attributes of a stored+unsealed node')
            elif any(key not in self._updatable_attributes for key in keys):
                raise exceptions.ModificationNotAllowed(
                    f'Cannot modify non-updatable attributes of a stored+unsealed node: {keys}'
                )
