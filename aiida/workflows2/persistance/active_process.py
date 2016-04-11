# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty
from enum import Enum
from collections import MutableMapping

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class ActiveProcessStatus(Enum):
    RUNNING = 1
    FINISHED = 2
    FAILED = 3


class InstanceState(MutableMapping):
    def __init__(self):
        pass

    @abstractmethod
    def save(self):
        pass


class ActiveProcessRecord(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def retronode_pk(self):
        pass

    @abstractproperty
    def process_class(self):
        pass

    @abstractproperty
    def status(self):
        """
        The status of the process.  Should be one of ActiveProcessStatus enums.
        :return: The current status of the process.
        """
        pass

    @abstractproperty
    def user(self):
        pass

    @abstractproperty
    def inputs(self):
        pass

    @abstractproperty
    def last_saved(self):
        pass

    @abstractproperty
    def instance_state(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def add_child(self, pid):
        pass

    @abstractmethod
    def remove_child(self, pid):
        pass

    @abstractmethod
    def has_child(self, pid):
        pass


