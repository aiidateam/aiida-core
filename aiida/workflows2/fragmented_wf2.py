# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from plum.wait_ons import Checkpoint
from plum.wait import WaitOn
from aiida.workflows2.process import Process, ProcessSpec

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "The AiiDA team"


class _FragmentedWorkfunction2Spec(ProcessSpec):
    def __init__(self):
        super(_FragmentedWorkfunction2Spec, self).__init__()
        self._outline = None

    def outline(self, *commands):
        self._outline = commands \
            if isinstance(commands, _Step) else _Block(commands)

    def get_outline(self):
        return self._outline


class FragmentedWorkfunction2(Process):
    _spec_type = _FragmentedWorkfunction2Spec

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

        def get(self, key, default=None):
            return self._content.get(key, default)

        def setdefault(self, key, default=None):
            return self._content.setdefault(key, default)

    def __init__(self, attributes=None):
        super(FragmentedWorkfunction2, self).__init__(attributes)
        self._context = None
        self._stepper = None

    def save_instance_state(self, bundle):
        super(FragmentedWorkfunction2, self).save_instance_state(bundle)
        for key, val in self._context:
            bundle[key] = val

    @property
    def context(self):
        return self._context

    def _run(self, **kwargs):
        self._stepper = self.spec().get_outline().create_stepper(self)
        return self._do_step()

    def _do_step(self, wait_on=None):
        finished, retval = self._stepper.step()
        if not finished:
            if isinstance(retval, _ResultToContext):
                return _ResultToContext(self._do_step.__name__, **retval.to_assign)
            else:
                return Checkpoint(self._do_step.__name__)

    # Internal messages #################################
    def on_start(self, inputs, exec_engine):
        super(FragmentedWorkfunction2, self).on_start(inputs, exec_engine)
        self._context = self.Context()

    def on_finalise(self):
        super(FragmentedWorkfunction2, self).on_finalise()
        self._last_step = None
    #####################################################


class ResultToContext(object):
    def __init__(self, **kwargs):
        # TODO: Check all values of kwargs are futures
        self.to_assign = kwargs


class _ResultToContext(WaitOn):
    @classmethod
    def create_from(cls, bundle, exec_engine):
        # TODO: Load the futures
        return _ResultToContext(bundle[cls.CALLBACK_NAME])

    def __init__(self, callback_name, **kwargs):
        super(_ResultToContext, self).__init__(callback_name)
        # TODO: Check all values of kwargs are futures
        self._to_assign = kwargs

    def is_ready(self):
        for fut in self._to_assign.itervalues():
            if not fut.done():
                return False
        return True

    def save_instance_state(self, bundle, exec_engine):
        super(_ResultToContext, self).save_instance_state(bundle, exec_engine)

    def assign(self, context):
        for name, fut in self._to_assign.iteritems():
            setattr(context, name, fut.result())


class Stepper(object):
    __metaclass__ = ABCMeta

    def __init__(self, workflow):
        self._workflow = workflow

    @abstractmethod
    def step(self):
        pass


class _Step(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_stepper(self, workflow):
        pass


class _Block(_Step, tuple):
    class Stepper(Stepper):
        def __init__(self, workflow, commands):
            super(_Block.Stepper, self).__init__(workflow)
            self._commands = commands
            self._current_stepper = None
            self._pos = 0

        def step(self):
            assert(self._pos != len(self._commands),
                   "Can't call step after the block is finished")

            command = self._commands[self._pos]

            if self._current_stepper is None and isinstance(command, _Step):
                self._current_stepper = command.create_stepper(self._workflow)

            # If there is a stepper being used then call that, otherwise just
            # call the command (function) directly
            if self._current_stepper is not None:
                finished, retval = self._current_stepper.step()
            else:
                finished, retval = True, command(self._workflow,
                                                 self._workflow.context)

            if finished:
                self._pos += 1
                self._current_stepper = None

            return self._pos == len(self._commands), retval

    def create_stepper(self, workflow):
        return self.Stepper(workflow, self)


class _Conditional(object):
    """
    Object that represents some condition with the corresponding body to be
    executed if the condition is met e.g.:
    if(condition):
      body

    or

    while(condition):
      body
    """
    def __init__(self, parent, condition):
        self._parent = parent
        self._condition = condition
        self._body = None

    @property
    def body(self):
        return self._body

    def is_true(self, workflow):
        return self._condition(workflow, workflow.context)

    def __call__(self, *commands):
        assert self._body is None
        self._body = _Block(commands)
        return self._parent


class _If(_Step):
    class Stepper(Stepper):
        def __init__(self, workflow, if_spec):
            super(_If.Stepper, self).__init__(workflow)
            self._if_spec = if_spec
            self._pos = 0
            self._current_stepper = None

        def step(self):
            if self._current_stepper is None:
                stepper = self._get_next_stepper()
                # If we can't get a stepper then no conditions match, return
                if stepper is None:
                    return True, None
                self._current_stepper = stepper

            finished, retval = self._current_stepper.step()
            if finished:
                self._current_stepper = None
            else:
                self._pos += 1

            return finished, retval

        def _get_next_stepper(self):
            # Check the conditions until we find that that is true
            for conditional in self._if_spec.conditionals[self._pos:]:
                if conditional.is_true(self._workflow):
                    return conditional.body.create_stepper(self._workflow)
            return None

    def __init__(self, condition):
        super(_If, self).__init__()
        self._ifs = [_Conditional(self, condition)]
        self._sealed = False

    def __call__(self, *commands):
        """
        This is how the commands for the if(...) body are set
        :param commands: The commands to run on the original if.
        :return: This instance.
        """
        self._ifs[0](*commands)
        return self

    def elif_(self, condition):
        self._ifs.append(_Conditional(self, condition))
        return self._ifs[-1]

    def else_(self, *commands):
        assert not self._sealed
        cond = _Conditional(self, lambda x, y: True)
        cond(*commands)
        self._ifs.append(cond)
        # Can't do any more after the else
        self._sealed = True
        return self

    def create_stepper(self, workflow):
        return self.Stepper(workflow, self)

    @property
    def conditionals(self):
        return self._ifs


class _While(_Conditional, _Step):
    class Stepper(Stepper):
        def __init__(self, workflow, while_spec):
            super(_While.Stepper, self).__init__(workflow)
            self._spec = while_spec
            self._stepper = None
            self._check_condition = True
            self._finished = False

        def step(self):
            assert (not self._finished,
                    "Can't call step after the loop has finished")

            # Do we need to check the condition?
            if self._check_condition is True:
                self._check_condition = False
                # Should we go into the loop body?
                if self._spec.is_true(self._workflow):
                    self._stepper = self._spec.body.create_stepper(self._workflow)
                else:  # Nope...
                    self._finished = True
                    return True, None

            finished, retval = self._stepper.step()
            if finished:
                self._check_condition = True
                self._stepper = None

            # Are we finished looping?
            return self._finished, retval

        @property
        def _body_stepper(self):
            if self._stepper is None:
                self._stepper =\
                    self._spec.body.create_stepper(self._workflow)
            return self._stepper

    def __init__(self, condition):
        super(_While, self).__init__(self, condition)

    def create_stepper(self, workflow):
        return self.Stepper(workflow, self)


def if_(condition):
    return _If(condition)


def while_(condition):
    return _While(condition)
