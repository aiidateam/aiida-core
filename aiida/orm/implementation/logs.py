# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend group module"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc
import six

from . import backends

__all__ = 'BackendLog', 'BackendLogCollection'


@six.add_metaclass(abc.ABCMeta)
class BackendLog(backends.BackendEntity):
    """
    Backend Log interface
    """

    @abc.abstractproperty
    def time(self):
        """
        Get the time corresponding to the entry

        :return: The entry timestamp
        :rtype: :class:`!datetime.datetime`
        """
        pass

    @abc.abstractproperty
    def loggername(self):
        """
        The name of the logger that created this entry

        :return: The entry loggername
        :rtype: basestring
        """
        pass

    @abc.abstractproperty
    def levelname(self):
        """
        The name of the log level

        :return: The entry log level name
        :rtype: basestring
        """
        pass

    @abc.abstractproperty
    def objpk(self):
        """
        Get the id of the object that created the log entry

        :return: The entry timestamp
        :rtype: int
        """
        pass

    @abc.abstractproperty
    def objname(self):
        """
        Get the name of the object that created the log entry

        :return: The entry object name
        :rtype: basestring
        """
        pass

    @abc.abstractproperty
    def message(self):
        """
        Get the message corresponding to the entry

        :return: The entry message
        :rtype: basestring
        """
        pass

    @abc.abstractproperty
    def metadata(self):
        """
        Get the metadata corresponding to the entry

        :return: The entry metadata
        :rtype: :class:`!json.json`
        """
        pass


@six.add_metaclass(abc.ABCMeta)
class BackendLogCollection(backends.BackendCollection[BackendLog]):
    """The collection of Group entries."""

    ENTITY_CLASS = BackendLog

    @abc.abstractmethod
    def delete_many(self, filters):
        """
        Delete multiple log entries in the table
        """
