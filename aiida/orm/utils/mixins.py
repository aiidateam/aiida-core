# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Mixin classes for ORM classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import inspect
import io

from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override
from aiida.common.lang import classproperty


class FunctionCalculationMixin(object):  # pylint: disable=useless-object-inheritance
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
            with io.open(source_file_path, 'r', encoding='utf8') as handle:
                self._set_source_file(handle)
        except (IOError, OSError):
            pass

    @property
    def function_name(self):
        """
        Return the function name of the wrapped function

        :returns: the function name or None
        """
        return self.get_attribute(self.FUNCTION_NAME_KEY, None)

    def _set_function_name(self, function_name):
        """
        Set the function name of the wrapped function

        :param function_name: the function name
        """
        self.set_attribute(self.FUNCTION_NAME_KEY, function_name)

    @property
    def function_namespace(self):
        """
        Return the function namespace of the wrapped function

        :returns: the function namespace or None
        """
        return self.get_attribute(self.FUNCTION_NAMESPACE_KEY, None)

    def _set_function_namespace(self, function_namespace):
        """
        Set the function namespace of the wrapped function

        :param function_namespace: the function namespace
        """
        self.set_attribute(self.FUNCTION_NAMESPACE_KEY, function_namespace)

    @property
    def function_starting_line_number(self):
        """
        Return the starting line number of the wrapped function in its source file

        :returns: the starting line number or None
        """
        return self.get_attribute(self.FUNCTION_STARTING_LINE_KEY, None)

    def _set_function_starting_line_number(self, function_starting_line_number):
        """
        Set the starting line number of the wrapped function in its source file

        :param function_starting_line_number: the starting line number
        """
        self.set_attribute(self.FUNCTION_STARTING_LINE_KEY, function_starting_line_number)

    def get_function_source_code(self):
        """
        Return the absolute path to the source file in the repository

        :returns: the absolute path of the source file in the repository, or None if it does not exist
        """
        return self.get_object_content(self.FUNCTION_SOURCE_FILE_PATH)

    def _set_source_file(self, source_file_handle):
        """
        Store a copy of the source file from `source_file_handle` in the repository

        :param source_file_handle: a file like object with the source file
        """
        self.put_object_from_filelike(source_file_handle, self.FUNCTION_SOURCE_FILE_PATH)


class Sealable(object):  # pylint: disable=useless-object-inheritance
    """Mixin to mark a Node as `sealable`."""
    # pylint: disable=no-member,unsupported-membership-test

    SEALED_KEY = 'sealed'

    @classproperty
    def _updatable_attributes(cls):  # pylint: disable=no-self-argument
        return (cls.SEALED_KEY,)

    def validate_incoming(self, source, link_type, link_label):
        """
        Validate adding a link of the given type from a given node to ourself.

        Adding an incoming link to a sealed node is forbidden.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise aiida.common.ModificationNotAllowed: if the target node (self) is sealed
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot add a link to a sealed node')

        super(Sealable, self).validate_incoming(source, link_type=link_type, link_label=link_label)

    def validate_outgoing(self, target, link_type, link_label):
        """
        Validate adding a link of the given type from ourself to a given node.

        Adding an outgoing link from a sealed node is forbidden.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise aiida.common.ModificationNotAllowed: if the source node (self) is sealed
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot add a link from a sealed node')

        super(Sealable, self).validate_outgoing(target, link_type=link_type, link_label=link_label)

    @property
    def is_sealed(self):
        """
        Returns whether the node is sealed, i.e. whether the sealed attribute has been set to True
        """
        return self.get_attribute(self.SEALED_KEY, False)

    def seal(self):
        """
        Seal the node by setting the sealed attribute to True
        """
        if not self.is_sealed:
            self.set_attribute(self.SEALED_KEY, True)

    @override
    def set_attribute(self, key, value, **kwargs):
        """
        Set a new attribute

        :param key: attribute name
        :param value: attribute value
        :raise aiida.common.ModificationNotAllowed: if the node is already sealed or if the node is already stored
            and the attribute is not updatable
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot change the attributes of a sealed node')

        if self.is_stored and key not in self._updatable_attributes:
            raise ModificationNotAllowed('Cannot change the immutable attributes of a stored node')

        super(Sealable, self).set_attribute(key, value, stored_check=False, **kwargs)

    @override
    def delete_attribute(self, key):
        """
        Delete an attribute

        :param key: attribute name
        :raise AttributeError: if key does not exist
        :raise aiida.common.ModificationNotAllowed: if the node is already sealed or if the node is already stored
            and the attribute is not updatable
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot change the attributes of a sealed node')

        if self.is_stored and key not in self._updatable_attributes:
            raise ModificationNotAllowed('Cannot change the immutable attributes of a stored node')

        super(Sealable, self).delete_attribute(key, stored_check=False)
