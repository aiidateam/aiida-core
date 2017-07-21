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

__all__ = ['defaults', 'EnableCaching']

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
    def __init__(self):
        self._use_cache = _MutableBool(False)

    @property
    def use_cache(self):
        return self._use_cache

    @use_cache.setter
    def use_cache(self, value):
        self._use_cache.set(bool(value))

defaults = _Defaults()

class EnableCaching(object):
    """
    Context manager to temporarily set the caching default. The previous value will be restored upon exiting.
    """
    def __init__(self, value=True):
        self.value = value

    def __enter__(self):
        self.previous_value = bool(defaults.use_cache)
        defaults.use_cache = self.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        defaults.use_cache = self.previous_value
