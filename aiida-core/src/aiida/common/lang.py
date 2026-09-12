###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities that extend the basic python language."""

import functools
import inspect
import keyword
from collections.abc import Callable
from typing import Any, Generic, TypeVar


def isidentifier(identifier: str) -> bool:
    """Return whether the given string is a valid python identifier.

    :return: boolean, True if identifier is valid, False otherwise
    :raises TypeError: if identifier is not string type
    """
    type_check(identifier, str)
    return identifier.isidentifier() and not keyword.iskeyword(identifier)


T = TypeVar('T')


def type_check(what: T, of_type: Any, msg: 'str | None' = None, allow_none: bool = False) -> T:
    """Verify that object 'what' is of type 'of_type' and if not the case, raise a TypeError.

    :param what: the object to check
    :param of_type: the type (or tuple of types) to compare to
    :param msg: if specified, allows to customize the message that is passed within the TypeError exception
    :param allow_none: boolean, if True will not raise if the passed `what` is `None`

    :return: `what` or `None`
    """
    if allow_none and what is None:
        return what

    if not isinstance(what, of_type):
        if msg is None:
            msg = f"Got object of type '{type(what)}', expecting '{of_type}'"
        raise TypeError(msg)

    return what


MethodType = TypeVar('MethodType', bound=Callable[..., Any])


def super_check(wrapped: MethodType) -> MethodType:
    """Decorate a method to require invocation through :func:`call_with_super_check`."""

    @functools.wraps(wrapped)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
        msg = f"The function '{wrapped.__name__}' was not called through call_with_super_check"
        assert getattr(self, '_called', 0) >= 1, msg
        wrapped(self, *args, **kwargs)
        self._called -= 1

    return wrapper  # type: ignore[return-value]


def call_with_super_check(wrapped: MethodType, *args: Any, **kwargs: Any) -> None:
    """Call a bound method and verify that every override calls ``super()``."""
    self = wrapped.__self__  # type: ignore[attr-defined]
    call_count = getattr(self, '_called', 0)
    self._called = call_count + 1
    wrapped(*args, **kwargs)
    msg = f"Base '{wrapped.__name__}' was not called from '{self.__class__}'\nHint: Did you forget to call the super?"
    assert self._called == call_count, msg


def override_decorator(check: bool = False) -> Callable[[MethodType], MethodType]:
    """Decorator to signal that a method from a base class is being overridden completely."""

    def wrap(func: MethodType) -> MethodType:
        if isinstance(func, property):
            raise RuntimeError('Override must go after @property decorator')

        args = inspect.getfullargspec(func)[0]
        if not args:
            raise RuntimeError('Can only use the override decorator on member functions')

        if not check:
            return func

        @functools.wraps(func)
        def wrapped_fn(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                getattr(super(), func.__name__)
            except AttributeError:
                raise RuntimeError(f'Function {func} does not override a superclass method')

            return func(self, *args, **kwargs)

        return wrapped_fn  # type: ignore[return-value]

    return wrap


override = override_decorator(check=False)

ReturnType = TypeVar('ReturnType')


class classproperty(Generic[ReturnType]):  # noqa: N801
    """A class that, when used as a decorator, works as if the
    two decorators @property and @classmethod where applied together
    (i.e., the object works as a property, both for the Class and for any
    of its instance; and is called with the class cls rather than with the
    instance as its first argument).
    """

    def __init__(self, getter: Callable[[Any], ReturnType]) -> None:
        self.getter = getter

    def __get__(self, instance: Any, owner: type) -> ReturnType:
        return self.getter(owner)
