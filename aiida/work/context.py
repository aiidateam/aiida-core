# -*- coding: utf-8 -*-
from .awaitable import construct_awaitable, AwaitableAction

__all__ = ['ToContext', 'assign_', 'append_']

ToContext = dict


def assign_(target):
    """
    Convenience function that will construct an Awaitable for a given class instance
    with the context action set to ASSIGN. When the awaitable target is completed
    it will be assigned to the context for a key that is to be defined later

    :param target: an instance of Calculation, Workflow or Awaitable
    :returns: the awaitable
    :rtype: Awaitable
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.ASSIGN
    return awaitable


def append_(target):
    """
    Convenience function that will construct an Awaitable for a given class instance
    with the context action set to APPEND. When the awaitable target is completed
    it will be appended to a list in the context for a key that is to be defined later

    :param target: an instance of Calculation, Workflow or Awaitable
    :returns: the awaitable
    :rtype: Awaitable
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.APPEND
    return awaitable
