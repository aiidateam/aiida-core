# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities that extend the basic python language."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools

import plumpy.lang

override = plumpy.lang.override(check=False)  # pylint: disable=invalid-name
protected = plumpy.lang.protected(check=False)  # pylint: disable=invalid-name


class classproperty(object):  # pylint: disable=too-few-public-methods,invalid-name,useless-object-inheritance
    """
    A class that, when used as a decorator, works as if the
    two decorators @property and @classmethod where applied together
    (i.e., the object works as a property, both for the Class and for any
    of its instance; and is called with the class cls rather than with the
    instance as its first argument).
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class abstractclassmethod(classmethod):  # pylint: disable=too-few-public-methods, invalid-name
    """
    A decorator indicating abstract classmethods.

    Backported from python3.
    """
    __isabstractmethod__ = True

    def __init__(self, callable):  # pylint: disable=redefined-builtin
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class abstractstaticmethod(staticmethod):  # pylint: disable=too-few-public-methods, invalid-name
    """
    A decorator indicating abstract staticmethods.

    Similar to abstractmethod.
    Backported from python3.
    """

    __isabstractmethod__ = True

    def __init__(self, callable):  # pylint: disable=redefined-builtin
        callable.__isabstractmethod__ = True  # pylint: disable=redefined-builtin
        super(abstractstaticmethod, self).__init__(callable)


class combomethod(object):  # pylint: disable=invalid-name,too-few-public-methods,useless-object-inheritance
    """
    A decorator that wraps a function that can be both a classmethod or
    instancemethod and behaves accordingly::

        class A():

            @combomethod
            def do(self, **kwargs):
                isclass = kwargs.get('isclass')
                if isclass:
                    print("I am a class", self)
                else:
                    print("I am an instance", self)

        A.do()
        A().do()

        >>> I am a class __main__.A
        >>> I am an instance <__main__.A instance at 0x7f2efb116e60>

    Attention: For ease of handling, pass keyword **isclass**
    equal to True if this was called as a classmethod and False if this
    was called as an instance.
    The argument self is therefore ambiguous!
    """

    def __init__(self, method):
        self.method = method

    def __get__(self, obj=None, objtype=None):  # pylint: disable=missing-docstring

        @functools.wraps(self.method)
        def _wrapper(*args, **kwargs):  # pylint: disable=missing-docstring
            kwargs.pop('isclass', None)
            if obj is not None:
                return self.method(obj, *args, isclass=False, **kwargs)
            return self.method(objtype, *args, isclass=True, **kwargs)

        return _wrapper


class EmptyContextManager(object):  # pylint: disable=too-few-public-methods,useless-object-inheritance
    """
    A dummy/no-op context manager.
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def type_check(what, of_type):
    if not isinstance(what, of_type):
        raise TypeError("Got object of type '{}', expecting '{}'".format(type(what), of_type))
