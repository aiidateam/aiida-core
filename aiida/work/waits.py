# -*- coding: utf-8 -*-
from enum import Enum
from plum.utils import AttributesDict
from aiida.orm.calculation import Calculation
from aiida.orm.workflow import Workflow

__all__ = ['AwaitableTarget', 'AwaitableAction', 'construct_awaitable', 'Outputs', 'assign_', 'append_']


class AwaitableTarget(Enum):
    """
    Enum that describes the class of the target a given awaitable
    """
    CALCULATION = 'calculation'
    WORKFLOW = 'workflow'


class AwaitableAction(Enum):
    """
    Enum that describes the action to be taken for a given awaitable
    """
    ASSIGN = 'assign'
    APPEND = 'append'


class Awaitable(AttributesDict):
    pass


def construct_awaitable(target):
    """
    """
    if isinstance(target, Awaitable):
        return target

    awaitable = Awaitable(**{
        'pk': target.pk,
        'outputs': False,
        'action': AwaitableAction.ASSIGN
    })

    if isinstance(target, Calculation):
        awaitable.target = AwaitableTarget.CALCULATION
    elif isinstance(target, Workflow):
        awaitable.target = AwaitableTarget.WORKFLOW
    else:
        raise ValueError('incorrect type bla')

    return awaitable


def Outputs(target):
    """
    """
    awaitable = construct_awaitable(target)
    awaitable.outputs = True
    return awaitable


def assign_(target):
    """
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.ASSIGN
    return awaitable


def append_(target):
    """
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.APPEND
    return awaitable