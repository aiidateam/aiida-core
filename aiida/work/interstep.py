from abc import ABCMeta, abstractmethod
from collections import namedtuple, MutableSequence
from plum.engine.execution_engine import Future
from plum.wait_ons import WaitOnProcess
from aiida.orm import load_node, load_workflow
from aiida.work.run import RunningType, RunningInfo
from aiida.work.legacy.wait_on import WaitOnJobCalculation, WaitOnWorkflow
from aiida.common.lang import override
from aiida.common.utils import get_object_string, get_object_from_string, get_class_string

Action = namedtuple("Action", "running_info fn")


class Savable(object):
    @classmethod
    def create_from(cls, saved_state):
        """
        Create the wait on from a save instance state.

        :param saved_state: The saved instance state
        :type saved_state: :class:`plum.persistence.Bundle`
        :return: The wait on with its state as it was when it was saved
        """
        obj = cls.__new__(cls)
        obj.load_instance_state(saved_state)
        return obj

    @abstractmethod
    def save_instance_state(self, out_state):
        pass

    @abstractmethod
    def load_instance_state(self, saved_state):
        pass

class Interstep(Savable):
    """
    An internstep is an action that is performed between steps of a workchain.
    These allow the user to perform action when a step is finished and when
    the next step (if there is one) is about the start.
    """
    __metaclass__ = ABCMeta

    CLASS_NAME = 'class_name'

    def on_last_step_finished(self, workchain):
        """
        Called when the last step has finished

        :param workchain: The workchain this interstep belongs to
        :type workchain: :class:`WorkChain`
        """
        pass

    def on_next_step_starting(self, workchain):
        """
        Called when the next step is about to start

        :param workchain: The workchain this interstep belongs to
        :type workchain: :class:`WorkChain`
        """
        pass

    def save_instance_state(self, out_state):
        """
        """
        out_state[self.CLASS_NAME] = get_class_string(self)

class UpdateContext(Interstep):
    """
    Intersteps that evaluate an action and store
    the results in the context of the Process
    """

    def __init__(self, key, action):
        self._action = action
        self._key = key

    def __eq__(self, other):
        return (self._action == other._action and self._key == other._key)

    def _create_wait_on(self):
        rinfo = self._action.running_info
        if rinfo.type is RunningType.PROCESS:
            return WaitOnProcess(self._action.fn, rinfo.pid)
        elif rinfo.type is RunningType.LEGACY_CALC:
            return WaitOnJobCalculation(self._action.fn, rinfo.pid)
        elif rinfo.type is RunningType.LEGACY_WORKFLOW:
            return WaitOnWorkflow(self._action.fn, rinfo.pid)

    @override
    def on_last_step_finished(self, workchain):
        workchain.insert_barrier(self._create_wait_on())

    @override
    def save_instance_state(self, out_state):
        super(UpdateContext, self).save_instance_state(out_state)
        out_state['action'] = self._action
        out_state['key'] = self._key

    @override
    def load_instance_state(self, saved_state):
        self._action = saved_state['action']
        self._key = saved_state['key']


class UpdateContextBuilder(object):
    def __init__(self, value):
        if isinstance(value, Action):
            action = value
        elif isinstance(value, RunningInfo):
            action = action_from_running_info(value)
        elif isinstance(value, Future):
            action = Calc(RunningInfo(RunningType.PROCESS, value.pid))
        else:
            action = Legacy(value)
        self._action = action

    @abstractmethod
    def build(self, key):
        pass


class Assign(UpdateContext):
    """
    """

    class Builder(UpdateContextBuilder):
        def build(self, key):
            return Assign(key, self._action)

    @override
    def on_next_step_starting(self, workchain):
        fn = get_object_from_string(self._action.fn)
        key = self._key
        val = fn(self._action.running_info.pid)
        workchain.ctx[key] = val


class Append(UpdateContext):
    """
    """

    class Builder(UpdateContextBuilder):
        def build(self, key):
            return Append(key, self._action)

    @override
    def on_next_step_starting(self, workchain):
        fn = get_object_from_string(self._action.fn)
        key = self._key
        val = fn(self._action.running_info.pid)

        if key in workchain.ctx and not isinstance(workchain.ctx[key], MutableSequence):
            raise TypeError("You are trying to append to an existing key that is not a list")

        workchain.ctx.setdefault(key, []).append(val)


assign_ = Assign.Builder
append_ = Append.Builder


def action_from_running_info(running_info):
    if running_info.type is RunningType.PROCESS:
        return Calc(running_info)
    elif running_info.type is RunningType.LEGACY_CALC or \
                    running_info.type is RunningType.LEGACY_WORKFLOW:
        return Legacy(running_info)
    else:
        raise ValueError("Unknown running type '{}'".format(running_info.type))


def _get_proc_outputs_from_registry(pid):
    calc = load_node(pid)
    if calc.has_failed():
        raise ValueError("Cannot return outputs, calculation '{}' has failed".format(pid))
    return {e[0]: e[1] for e in calc.get_outputs(also_labels=True)}


def _get_wf_outputs(pk):
    return load_workflow(pk=pk).get_results()


def Calc(running_info):
    return Action(running_info, get_object_string(load_node))


def Wf(running_info):
    return Action(running_info, get_object_string(load_workflow))


def Legacy(object):
    if object.type == RunningType.LEGACY_CALC or object.type == RunningType.PROCESS:
        return Calc(object)
    elif object.type is RunningType.LEGACY_WORKFLOW:
        return Wf(object)

    raise ValueError("Could not determine object to be calculation or workflow")


def Outputs(running_info):
    if isinstance(running_info, Future):
        # Create the correct information from the future
        rinfo = RunningInfo(RunningType.PROCESS, running_info.pid)
        return Action(rinfo, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type == RunningType.PROCESS:
        return Action(running_info, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type == RunningType.LEGACY_CALC:
        return Action(running_info, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type is RunningType.LEGACY_WORKFLOW:
        return Action(running_info, get_object_string(_get_wf_outputs))

def load_with_classloader(bundle):
    """
    Load a process from a saved instance state

    :param bundle: The saved instance state bundle
    :return: The process instance
    :rtype: :class:`Process`
    """
    # Get the class using the class loader and instantiate it
    class_name = bundle['class_name']
    proc_class = bundle.get_class_loader().load_class(class_name)
    return proc_class.create_from(bundle)