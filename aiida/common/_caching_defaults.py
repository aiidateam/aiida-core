#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines the default values for using the caching mechanism. The values are mutable, meaning they have the following behavior:

.. code :: python
    >>> x = defaults.use_cache
    >>> print(x)
    False
    >>> defaults.use_cache = True
    >>> print(x)
    True
"""

__all__ = ['defaults']

class _MutableBool(object):
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return self.value

    def __str__(self):
        return str(bool(self))

class _Defaults(object):
    """
    A class containing the default values for caching.
    """
    __slots__ = ['_use_cache']

    def __init__(self):
        self._use_cache = _MutableBool(False)

    @property
    def use_cache(self):
        return self._use_cache

    @use_cache.setter
    def use_cache(self, value):
        self._use_cache.set(value)

defaults = _Defaults()
