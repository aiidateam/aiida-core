# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import ABCMeta, abstractmethod
from collections import namedtuple, MutableSequence
from aiida.work.legacy.wait_on import WaitOnWorkflow
from apricotpy import futures
from aiida.orm import load_node
from . import process

Action = namedtuple("Action", "running_info fn")


class ContextAction(object):
    pass


class Assign(ContextAction):
    def __init__(self, what):
        if isinstance(what, Outputs):
            self.fn = _assign_result
            self.awaitable = what._awaitable
        else:
            self.fn = _assign
            self.awaitable = what


class Append(ContextAction):
    def __init__(self, what):
        if isinstance(what, Outputs):
            self.fn = _append_result
            self.awaitable = what._awaitable
        else:
            self.fn = _append
            self.awaitable = what


assign_ = Assign
append_ = Append


def _assign(key, workchain, awaitable):
    if isinstance(awaitable, WaitOnWorkflow):
        workchain.ctx[key] = awaitable.workflow
    elif isinstance(awaitable, process.Process):
        workchain.ctx[key] = awaitable.calc
    elif isinstance(awaitable, futures.Awaitable):
        workchain.ctx[key] = load_node(awaitable.pid)
    else:
        raise TypeError("Unsupported assign type '{}'".format(awaitable))


def _assign_result(key, workchain, awaitable):
    workchain.ctx[key] = awaitable.result()


def _append(key, workchain, awaitable):
    if isinstance(awaitable, WaitOnWorkflow):
        workchain.ctx.setdefault(key, []).append(awaitable.workflow)
    elif isinstance(awaitable, process.Process):
        workchain.ctx.setdefault(key, []).append(awaitable.calc)
    elif isinstance(awaitable, futures.Awaitable):
        workchain.ctx.setdefault(key, []).append(load_node(awaitable.pid))
    else:
        raise TypeError("Unsupported append type '{}'".format(awaitable))


def _append_result(key, workchain, awaitable):
    workchain.ctx.setdefault(key, []).append(awaitable.result())


class Outputs(object):
    def __init__(self, awaitable):
        self._awaitable = awaitable
