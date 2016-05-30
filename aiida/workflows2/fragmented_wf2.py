# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from plum.wait_ons import Checkpoint
from plum.wait import WaitOn
from aiida.workflows2.process import Process, ProcessSpec


__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "The AiiDA team"


class _Step(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def step(self, local):
        pass

    @abstractmethod
    def reset(self):
        pass


class _SingleCommand(_Step):
    def __init__(self, command):
        self._command = command

    def step(self, local):
        retval = self._command(local)
        return retval, True

    def reset(self):
        pass  # Nothing to do


class _Scope(_Step):
    @staticmethod
    def make_step(command):
        if isinstance(command, _Step):
            return command
        else:
            # Assume it's a direct function
            return _SingleCommand(command)

    def __init__(self, *commands):
        self._commands = [_Scope.make_step(c) for c in commands]
        self._current_pos = 0

    def step(self, local):
        retval, finished = self._commands[self._current_pos].step(local)
        if finished:
            self._current_pos += 1
        return retval, self._current_pos == len(self._commands)

    def reset(self):
        self._current_pos = 0


class _If(_Step):
    def __init__(self, condition):
        super(_If, self).__init__()
        self._ifs = [_Conditional(self, condition)]
        self._else = None
        self._current_block = None

    def elif_(self, condition):
        self._ifs.append(_Conditional(self, condition))
        return self._ifs[-1]

    def else_(self, *commands):
        self._else = _Scope(commands)

    def step(self, local):
        if self._current_block is None:
            # Assume it's the else block unless we match an if that matches
            self._current_block = self._else

            # We need to determine which (if any) condition is met
            for conditional in self._ifs:
                if conditional.is_true(local):
                    self._current_block = conditional
                    break

        if self._current_block is None:
            return None, True
        else:
            return self._current_block.step

    def reset(self):
        self._current_block = None

    def __call__(self, *commands):
        self._ifs[0](commands)
        return self


class _Conditional(_Step):
    def __init__(self, parent, condition):
        self._parent = parent
        self._condition = condition
        self._scope = None

    @property
    def block(self):
        return self._scope

    def is_true(self, local):
        return self._condition(local)

    def step(self, local):
        return self._scope.step(local)

    def reset(self):
        self._scope.reset()

    def __call__(self, *commands):
        assert self._scope is None
        self._scope = _Scope(commands)
        return self._parent


class _While(_Step):
    def __init__(self, condition):
        self._conditional = _Conditional(self, condition)
        self._check_condition = True

    def step(self, local):
        if self._check_condition and not self._conditional.is_true(local):
            return None, True  # We're done

        retval, finished = self._conditional.step(local)
        if finished:
            # Check the condition next time around
            self._check_condition = True
            self._conditional.reset()

        return retval, finished

    def reset(self):
        self._check_condition = False
        self._conditional.reset()

    def __call__(self, *commands):
        self._conditional(commands)


def if_(condition):
    return _If(condition)


def while_(condition):
    return _While(condition)


class _FragmentedWorkfunctionSpec(ProcessSpec):
    def __init__(self):
        super(_FragmentedWorkfunctionSpec, self).__init__()

    def outline(self, *commands):
        self._outline = _Scope(commands)

    def get_outline(self):
        return self._outline


class FragmentedWorkfunction2(Process):
    _spec_type = _FragmentedWorkfunctionSpec

    @staticmethod
    def _define(spec):
        # For now fragmented workflows can accept any input and emit any output
        # _If this changes in the future the spec should be updated here.
        spec.dynamic_input()
        spec.dynamic_output()

    class Context(object):
        _content = {}

        def __init__(self, value=None):
            if value is not None:
                for k, v in value.iteritems():
                    self._content[k] = v

        def _get_dict(self):
            return self._content

        def __getattr__(self, name):
            try:
                return self._content[name]
            except KeyError:
                raise AttributeError("Context does not have a variable {}"
                                     .format(name))

        def __setattr__(self, name, value):
            self._content[name] = value

        def __dir__(self):
            return sorted(self._content.keys())

        def __iter__(self):
            for k in self._content:
                yield k

    def __init__(self, attributes=None):
        super(FragmentedWorkfunction2, self).__init__(attributes)
        self._outline = self.spec().get_outline()

    def _run(self, **kwargs):
        self._outline.reset()
        return self._do_step()

    def _do_step(self, wait_on=None):
        retval, finished = self._outline.step()
        if not finished:
            if isinstance(retval, _ResultToScope):
                return _ResultToScope(self._do_step.__name__, **retval.to_assign)
            else:
                return Checkpoint(self._do_step.__name__)


    ## Internal messages ################################
    def on_start(self, inputs, exec_engine):
        super(FragmentedWorkfunction2, self).on_start(inputs, exec_engine)
        self._scope = self.Context()

    def on_finalise(self):
        self._last_step = None
    #####################################################


class ResultToScope(object):
    def __init__(self, **kwargs):
        # TODO: Check all values of kwargs are futures
        self.to_assign = kwargs


class _ResultToScope(WaitOn):
    @classmethod
    def create_from(cls, bundle, exec_engine):
        # TODO: Load the futures
        return _ResultToScope(bundle[cls.CALLBACK_NAME])

    def __init__(self, callback_name, **kwargs):
        super(_ResultToScope, self).__init__(callback_name)
        # TODO: Check all values of kwargs are futures
        self._to_assign = kwargs

    def is_ready(self):
        for fut in self._to_assign.itervalues():
            if not fut.done():
                return False
        return True

    def save_instance_state(self, bundle, exec_engine):
        super(_ResultToScope, self).save_instance_state(bundle, exec_engine)

    def assign(self, scope):
        for name, fut in self._to_assign.iteritems():
            setattr(scope, name, fut.result())
