# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty
from enum import Enum

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class ActiveProcessStatus(Enum):
    RUNNING = 1
    FINISHED = 2
    FAILED = 3


class ActiveProcessRecord(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def process_class(self):
        pass

    @abstractproperty
    def status(self):
        pass

    @abstractproperty
    def user(self):
        pass

    @abstractproperty
    def inputs(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class ActiveWorkflowRecord(ActiveProcessRecord):
    __metaclass__ = ABCMeta

    pass


