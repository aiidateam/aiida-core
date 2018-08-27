# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
import collections
import enum
import logging

import six
from plumpy import ProcessState

from aiida.common.links import LinkType
from aiida.common.log import get_dblogger_extra
from aiida.common.utils import classproperty
from aiida.orm.mixins import Sealable
from aiida.plugins.entry_point import get_entry_point_string_from_class


class AbstractCalculation(Sealable):
    """
    This class provides the definition of an "abstract" AiiDA calculation.
    A calculation in this sense is any computation that converts data into data.

    You will typically use one of its subclasses, often a JobCalculation for
    calculations run via a scheduler.
    """

    CHECKPOINT_KEY = 'checkpoints'
    EXCEPTION_KEY = 'exception'
    EXIT_MESSAGE_KEY = 'exit_message'
    EXIT_STATUS_KEY = 'exit_status'
    PROCESS_LABEL_KEY = '_process_label'
    PROCESS_PAUSED_KEY = 'paused'
    PROCESS_STATE_KEY = 'process_state'
    PROCESS_STATUS_KEY = 'process_status'

    # The link_type might not be correct while the object is being created.
    _hash_ignored_inputs = ['CALL']
    _cacheable = False

    @classproperty
    def _updatable_attributes(cls):
        return super(AbstractCalculation, cls)._updatable_attributes + (
            cls.PROCESS_PAUSED_KEY,
            cls.CHECKPOINT_KEY,
            cls.EXCEPTION_KEY,
            cls.EXIT_MESSAGE_KEY,
            cls.EXIT_STATUS_KEY,
            cls.PROCESS_LABEL_KEY,
            cls.PROCESS_STATE_KEY,
            cls.PROCESS_STATUS_KEY,
        )

    @classproperty
    def _use_methods(cls):
        """
        Return the list of valid input nodes that can be set using the
        use_* method.

        For each key KEY of the return dictionary, the 'use_KEY' method is
        exposed.
        Each value must be a dictionary, defining the following keys:
        * valid_types: a class, or tuple of classes, that will be used to
          validate the parameter using the isinstance() method
        * additional_parameter: None, if no additional parameters can be passed
          to the use_KEY method beside the node, or the name of the additional
          parameter (a string)
        * linkname: the name of the link to create (a string if
          additional_parameter is None, or a callable if additional_parameter is
          a string. The value of the additional parameter will be passed to the
          callable, and it should return a string.
        * docstring: a docstring for the function

        .. note:: in subclasses, always extend the parent class, do not
          substitute it!
        """
        from aiida.orm.code import Code
        return {
            'code': {
                'valid_types': Code,
                'additional_parameter': None,
                'linkname': 'code',
                'docstring': 'Choose the code to use',
            },
        }

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the node
        """
        # get node schema
        from aiida.orm.node import Node
        schema = Node.get_schema()

        # extend it for calculation
        schema["attributes.state"] = {
                "display_name": "State",
                "help_text": "AiiDA state of the calculation",
                "is_foreign_key": False,
                "type": ""
            }
        return schema

    @property
    def logger(self):
        """
        Get the logger of the Calculation object, so that it also logs to the DB.

        :return: LoggerAdapter object, that works like a logger, but also has the 'extra' embedded
        """
        return logging.LoggerAdapter(logger=self._logger, extra=get_dblogger_extra(self))

    def __dir__(self):
        """
        Allow to list all valid attributes, adding also the use_* methods
        """
        return sorted(dir(type(self)) + list(['use_{}'.format(k) for k in self._use_methods.keys()]))

    def __getattr__(self, name):
        """
        Expand the methods with the use_* calls. Note that this method only gets called if 'name'
        is not already defined as a method. Returning one will then automatically raise the
        standard AttributeError exception.
        """
        if name == '_use_methods':
            raise AttributeError("'{0}' object has no attribute '{1}'".format(type(self), name))

        class UseMethod(object):
            """
            Generic class for the use_* methods. To know which use_* methods
            exist, use the ``dir()`` function. To get help on a specific method,
            for instance use_code, use::
              ``print use_code.__doc__``
            """

            def __init__(self, node, actual_name, data):
                self.node = node
                self.actual_name = actual_name
                self.data = data

                try:
                    self.__doc__ = data['docstring']
                except KeyError:
                    # Forgot to define the docstring! Use the default one
                    pass

            def __call__(self, parent_node, *args, **kwargs):
                # Not really needed, will be checked in get_linkname but I do anyway in order to raise
                # an exception as soon as possible, with the most intuitive caller function name
                additional_parameter = _parse_single_arg(
                    function_name='use_{}'.format(self.actual_name),
                    additional_parameter=self.data['additional_parameter'],
                    args=args, kwargs=kwargs)

                # Type check
                if not isinstance(parent_node, self.data['valid_types']):
                    if isinstance(self.data['valid_types'], collections.Iterable):
                        valid_types_string = ','.join([_.__name__ for _ in self.data['valid_types']])
                    else:
                        valid_types_string = self.data['valid_types'].__name__

                    raise TypeError(
                        'The given node is not of the valid type for use_{}.'
                        'Valid types are: {}, while you provided {}'.format(
                            self.actual_name, valid_types_string, parent_node.__class__.__name__))

                # Get actual link name
                actual_linkname = self.node.get_linkname(actual_name, *args, **kwargs)

                # Here I do the real job
                self.node._replace_link_from(parent_node, actual_linkname)

        prefix = 'use_'
        valid_use_methods = ['{}{}'.format(prefix, k) for k in self._use_methods.keys()]

        if name in valid_use_methods:
            actual_name = name[len(prefix):]
            return UseMethod(node=self, actual_name=actual_name, data=self._use_methods[actual_name])
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    def _set_process_type(self, process_class):
        """
        Set the process type

        :param process_class: the process class using this calculation node as storage
        """
        class_module = process_class.__module__
        class_name = process_class.__name__

        # If the process is a registered plugin the corresponding entry point will be used as process type
        process_type = get_entry_point_string_from_class(class_module, class_name)

        # If no entry point was found, default to fully qualified path name
        if process_type is None:
            self.dbnode.process_type = '{}.{}'.format(class_module, class_name)
        else:
            self.dbnode.process_type = process_type

    @property
    def process_label(self):
        """
        Return the process label of the Calculation

        :returns: the process label
        """
        return self.get_attr(self.PROCESS_LABEL_KEY, None)

    def _set_process_label(self, label):
        """
        Set the process label of the Calculation

        :param label: process label string
        """
        self._set_attr(self.PROCESS_LABEL_KEY, label)

    @property
    def process_state(self):
        """
        Return the process state of the Calculation

        :returns: the process state instance of ProcessState enum
        """
        state = self.get_attr(self.PROCESS_STATE_KEY, None)
        if state is None:
            return state
        else:
            return ProcessState(state)

    def _set_process_state(self, state):
        """
        Set the process state of the Calculation

        :param state: value or instance of ProcessState enum
        """
        if isinstance(state, ProcessState):
            state = state.value
        return self._set_attr(self.PROCESS_STATE_KEY, state)

    @property
    def process_status(self):
        """
        Return the process status of the Calculation

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed

        :returns: the process status
        """
        return self.get_attr(self.PROCESS_STATUS_KEY, None)

    def _set_process_status(self, status):
        """
        Set the process status of the Calculation

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed.
        If status is None, the corresponding attribute will be deleted.

        :param status: string process status
        """
        if status is None:
            try:
                self._del_attr(self.PROCESS_STATUS_KEY)
            except AttributeError:
                pass
            return

        if not isinstance(status, six.string_types):
            raise TypeError('process status should be a string')

        return self._set_attr(self.PROCESS_STATUS_KEY, status)

    @property
    def is_terminated(self):
        """
        Returns whether the Calculation has terminated, meaning that it reached any terminal state

        :return: True if the calculation has terminated, False otherwise
        :rtype: bool
        """
        return self.is_excepted or self.is_finished or self.is_killed

    @property
    def is_excepted(self):
        """
        Returns whether the Calculation has excepted, meaning that during execution an exception
        was raised that was not properly dealt with

        :return: True if during execution of the calculation an exception occurred, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.EXCEPTED

    @property
    def is_killed(self):
        """
        Returns whether the Calculation was killed

        :return: True if the calculation was killed by the user, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.KILLED

    @property
    def is_finished(self):
        """
        Returns whether the Calculation has finished. Note that this does not necessarily
        mean successfully, but a terminal state was reached nominally

        :return: True if the calculation has finished, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.FINISHED

    @property
    def is_finished_ok(self):
        """
        Returns whether the Calculation has finished successfully, which means that it
        terminated nominally and had a zero exit status indicating a successful execution

        :return: True if the calculation has finished successfully, False otherwise
        :rtype: bool
        """
        return self.is_finished and self.exit_status == 0

    @property
    def is_failed(self):
        """
        Returns whether the Calculation has failed, which means that it terminated nominally
        but it had a non-zero exit status

        :return: True if the calculation has failed, False otherwise
        :rtype: bool
        """
        return self.is_finished and self.exit_status != 0

    @property
    def exit_status(self):
        """
        Return the exit status of the Calculation

        :returns: the exit status, an integer exit code or None
        """
        return self.get_attr(self.EXIT_STATUS_KEY, None)

    def _set_exit_status(self, status):
        """
        Set the exit status of the Calculation

        :param state: an integer exit code or None, which will be interpreted as zero
        """
        if status is None:
            status = 0

        if isinstance(status, enum.Enum):
            status = status.value

        if not isinstance(status, int):
            raise ValueError('exit status has to be an integer, got {}'.format(status))

        return self._set_attr(self.EXIT_STATUS_KEY, status)

    @property
    def exit_message(self):
        """
        Return the exit message of the Calculation

        :returns: the exit message
        """
        return self.get_attr(self.EXIT_MESSAGE_KEY, None)

    def _set_exit_message(self, message):
        """
        Set the exit message of the Calculation, if None nothing will be done

        :param message: a string message
        """
        if message is None:
            return

        if not isinstance(message, six.string_types):
            raise ValueError('exit message has to be a string type, got {}'.format(type(message)))

        return self._set_attr(self.EXIT_MESSAGE_KEY, message)

    @property
    def exception(self):
        """
        Return the exception of the Calculation or None if the calculation is not EXCEPTED. If the calculation
        is marked as EXCEPTED yet there is no exception attribute, an empty string will be returned

        :returns: the exception message or None
        """
        if self.is_excepted:
            return self.get_attr(self.EXCEPTION_KEY, '')

    def _set_exception(self, exception):
        """
        Set the exception of the Calculation

        :param exception: the exception message
        """
        if not isinstance(exception, six.string_types):
            raise ValueError('exception message has to be a string type, got {}'.format(type(exception)))

        return self._set_attr(self.EXCEPTION_KEY, exception)

    @property
    def checkpoint(self):
        """
        Return the checkpoint bundle set for the Calculation

        :returns: checkpoint bundle if it exists, None otherwise
        """
        return self.get_attr(self.CHECKPOINT_KEY, None)

    def set_checkpoint(self, checkpoint):
        """
        Set the checkpoint bundle set for the Calculation

        :param state: string representation of the stepper state info
        """
        return self._set_attr(self.CHECKPOINT_KEY, checkpoint)

    def del_checkpoint(self):
        """
        Delete the checkpoint bundle set for the Calculation
        """
        try:
            self._del_attr(self.CHECKPOINT_KEY)
        except AttributeError:
            pass

    @property
    def paused(self):
        """
        Return whether the Process corresponding to this Calculation node is paused

        :returns: True if the Calculation is marked as paused, False otherwise
        """
        return self.get_attr(self.PROCESS_PAUSED_KEY, False)

    def pause(self):
        """
        Mark the Calculation as paused by setting the corresponding attribute. This serves only to reflect
        that the corresponding Process is paused and so this method should not be called by anyone but the Process.
        """
        return self._set_attr(self.PROCESS_PAUSED_KEY, True)

    def unpause(self):
        """
        Mark the Calculation as unpaused by removing the corresponding attribute. This serves only to reflect
        that the corresponding Process is unpaused and so this method should not be called by anyone but the Process.
        """
        try:
            self._del_attr(self.PROCESS_PAUSED_KEY)
        except AttributeError:
            pass

    @property
    def called(self):
        """
        Return a list of nodes that the Calculation called

        :returns: list of Calculation nodes called by this Calculation instance
        """
        return self.get_outputs(link_type=LinkType.CALL)

    @property
    def called_descendants(self):
        """
        Return a list of all nodes that the Calculation called recursively calling this
        function on all its called children and extending the list
        """
        descendants = []

        for descendant in self.called:
            descendants.append(descendant)
            descendants.extend(descendant.called_descendants)

        return descendants

    @property
    def called_by(self):
        """
        Return the Calculation that called this Calculation, or None if it does not have a caller

        :returns: Calculation that called this Calculation instance or None
        """
        called_by = self.get_inputs(link_type=LinkType.CALL)
        if called_by:
            return called_by[0]
        else:
            return None

    def get_linkname(self, link, *args, **kwargs):
        """
        Return the linkname used for a given input link

        Pass as parameter "NAME" if you would call the use_NAME method.
        If the use_NAME method requires a further parameter, pass that
        parameter as the second parameter.
        """
        try:
            data = self._use_methods[link]
        except KeyError:
            raise ValueError("No '{}' link is defined for this calculation".format(link))

        # Raises if the wrong # of parameters is passed
        additional_parameter = _parse_single_arg(
            function_name='get_linkname',
            additional_parameter=data['additional_parameter'],
            args=args, kwargs=kwargs)

        if data['additional_parameter'] is not None:
            # Call the callable to get the proper linkname
            actual_linkname = data['linkname'](additional_parameter)
        else:
            actual_linkname = data['linkname']

        return actual_linkname

    def _linking_as_output(self, dest, link_type):
        """
        An output of a calculation can only be a data.

        :param dest: a Data object instance of the database
        :raise: ValueError if a link from self to dest is not allowed.
        """
        from aiida.orm.data import Data

        if link_type is LinkType.CREATE or link_type is LinkType.RETURN:
            if not isinstance(dest, Data):
                raise ValueError('The output of a calculation node can only be a data node')
        elif link_type is LinkType.CALL:
            if not isinstance(dest, AbstractCalculation):
                raise ValueError('Call links can only link two calculations')
        else:
            raise ValueError('Calculation cannot have links of type {} as output'.format(link_type))

        return super(AbstractCalculation, self)._linking_as_output(dest, link_type)

    def add_link_from(self, src, label=None, link_type=LinkType.INPUT):
        """
        Add a link with a code as destination.

        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. Default=None
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        from aiida.orm.code import Code
        from aiida.orm.data import Data

        if link_type is LinkType.INPUT:
            if not isinstance(src, (Data, Code)):
                raise ValueError('Nodes entering calculation as input link can only be of type data or code')
        elif link_type is LinkType.CALL:
            if not isinstance(src, AbstractCalculation):
                raise ValueError('Call links can only link two calculations')
        else:
            raise ValueError('Calculation cannot have links of type {} as input'.format(link_type))

        return super(AbstractCalculation, self).add_link_from( src, label, link_type)

    def get_code(self):
        """
        Return the code for this calculation, or None if the code
        was not set.
        """
        from aiida.orm.code import Code

        return dict(self.get_inputs(node_type=Code, also_labels=True)).get(
            self._use_methods['code']['linkname'], None)

    def _replace_link_from(self, src, label, link_type=LinkType.INPUT):
        """
        Replace a link.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link.
        """
        from aiida.orm.code import Code
        from aiida.orm.data import Data

        if not isinstance(src, (Data, Code)):
            raise ValueError('Nodes entering in calculation can only be of type data or code')

        return super(AbstractCalculation, self)._replace_link_from(src, label, link_type)

    def _is_valid_cache(self):
        """
        Return whether the node is valid for caching

        :returns: True if Calculation is valid to be used for caching, False otherwise
        """
        return super(AbstractCalculation, self)._is_valid_cache() and self.is_finished_ok

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        res = super(AbstractCalculation, self)._get_objects_to_hash()
        res.append({
            key: value.get_hash()
            for key, value in self.get_inputs_dict(link_type=LinkType.INPUT).items()
            if key not in self._hash_ignored_inputs
        })
        return res


def _parse_single_arg(function_name, additional_parameter, args, kwargs):
    """
    Verifies that a single additional argument has been given (or no
    additional argument, if additional_parameter is None). Also
    verifies its name.

    :param function_name: the name of the caller function, used for
        the output messages
    :param additional_parameter: None if no additional parameters
        should be passed, or a string with the name of the parameter
        if one additional parameter should be passed.

    :return: None, if additional_parameter is None, or the value of
        the additional parameter
    :raise TypeError: on wrong number of inputs
    """
    # Here all the logic to check if the parameters are correct.
    if additional_parameter is not None:
        if len(args) == 1:
            if kwargs:
                raise TypeError("{}() received too many args".format(
                    function_name))
            additional_parameter_data = args[0]
        elif len(args) == 0:
            kwargs_copy = kwargs.copy()
            try:
                additional_parameter_data = kwargs_copy.pop(
                    additional_parameter)
            except KeyError:
                if kwargs_copy:
                    raise TypeError("{}() got an unexpected keyword "
                                    "argument '{}'".format(
                        function_name, kwargs_copy.keys()[0]))
                else:
                    raise TypeError("{}() requires more "
                                    "arguments".format(function_name))
            if kwargs_copy:
                raise TypeError("{}() got an unexpected keyword "
                                "argument '{}'".format(
                    function_name, kwargs_copy.keys()[0]))
        else:
            raise TypeError("{}() received too many args".format(
                function_name))
        return additional_parameter_data
    else:
        if kwargs:
            raise TypeError("{}() got an unexpected keyword "
                            "argument '{}'".format(
                function_name, kwargs.keys()[0]))
        if len(args) != 0:
            raise TypeError("{}() received too many args".format(
                function_name))

        return None
