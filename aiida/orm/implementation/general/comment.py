# -*- coding: utf-8 -*-
import logging
from abc import abstractmethod, abstractproperty, ABCMeta



class AbstractComment(object):
    __metaclass__ = ABCMeta

    _logger = logging.getLogger(__name__)

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractproperty
    def pk(self):
        pass

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def to_be_stored(self):
        pass

    @abstractproperty
    def uuid(self):
        pass

    @abstractmethod
    def get_ctime(self):
        pass

    @abstractmethod
    def set_ctime(self, val):
        pass

    @abstractmethod
    def get_mtime(self):
        pass

    @abstractmethod
    def set_mtime(self, val):
        pass

    @abstractmethod
    def get_user(self):
        pass

    @abstractmethod
    def set_user(self, val):
        pass

    @abstractmethod
    def get_content(self):
        pass

    @abstractmethod
    def set_content(self, val):
        pass

    @abstractmethod
    def delete(self):
        pass
