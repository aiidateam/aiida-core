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
import inspect


def type_check(what, of_type, msg=None, allow_none=False):
    """Verify that object 'what' is of type 'of_type' and if not the case, raise a TypeError.

    :param what: the object to check
    :param of_type: the type (or tuple of types) to compare to
    :param msg: if specified, allows to customize the message that is passed within the TypeError exception
    :param allow_none: boolean, if True will not raise if the passed `what` is `None`
    """
    if allow_none and what is None:
        return

    if not isinstance(what, of_type):
        if msg is None:
            msg = "Got object of type '{}', expecting '{}'".format(type(what), of_type)
        raise TypeError(msg)


def protected_decorator(check=False):
    """Decorator to ensure that the decorated method is not called from outside the class hierarchy."""

    def wrap(func):  # pylint: disable=missing-docstring
        if isinstance(func, property):
            raise RuntimeError("Protected must go after @property decorator")

        args = inspect.getargspec(func)[0]  # pylint: disable=deprecated-method
        if not args:
            raise RuntimeError("Can only use the protected decorator on member functions")

        # We can only perform checks if the interpreter is capable of giving
        # us the stack i.e. currentframe() produces a valid object
        if check and inspect.currentframe() is not None:

            @functools.wraps(func)
            def wrapped_fn(self, *args, **kwargs):  # pylint: disable=missing-docstring
                try:
                    calling_class = inspect.stack()[1][0].f_locals['self']
                    assert self is calling_class
                except (KeyError, AssertionError):
                    raise RuntimeError("Cannot access protected function {} from outside"
                                       " class hierarchy".format(func.__name__))

                return func(self, *args, **kwargs)
        else:
            wrapped_fn = func

        return wrapped_fn

    return wrap


def override_decorator(check=False):
    """Decorator to signal that a method from a base class is being overridden completely."""

    def wrap(func):  # pylint: disable=missing-docstring
        if isinstance(func, property):
            raise RuntimeError("Override must go after @property decorator")

        args = inspect.getargspec(func)[0]  # pylint: disable=deprecated-method
        if not args:
            raise RuntimeError("Can only use the override decorator on member functions")

        if check:

            @functools.wraps(func)
            def wrapped_fn(self, *args, **kwargs):  # pylint: disable=missing-docstring
                try:
                    getattr(super(self.__class__, self), func.__name__)
                except AttributeError:
                    raise RuntimeError("Function {} does not override a superclass method".format(func))

                return func(self, *args, **kwargs)
        else:
            wrapped_fn = func

        return wrapped_fn

    return wrap


protected = protected_decorator(check=False)  # pylint: disable=invalid-name
override = override_decorator(check=False)  # pylint: disable=invalid-name


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
