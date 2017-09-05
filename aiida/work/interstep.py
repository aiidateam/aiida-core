import apricotpy
from abc import ABCMeta, abstractmethod
from collections import namedtuple, MutableSequence
from aiida.orm import load_node, load_workflow
from aiida.work.launch import RunningType, RunningInfo
from aiida.work.legacy.wait_on import WaitOnProcessTerminated, WaitOnWorkflow
from aiida.common.lang import override
from aiida.common.utils import get_object_string, get_object_from_string
from . import utils

Action = namedtuple("Action", "running_info fn")


class Interstep(utils.Savable):
    """
    An internstep is an action that is performed between steps of a workchain.
    These allow the user to perform action when a step is finished and when
    the next step (if there is one) is about the start.
    """
    __metaclass__ = ABCMeta

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


class UpdateContext(Interstep):
    """
    Interstep that evaluates an action and store
    the results in the context of the Process
    """

    def __init__(self, key, action):
        self._action = action
        self._key = key

    def __eq__(self, other):
        return self._action == other._action and self._key == other._key

    def _create_wait_on(self):
        rinfo = self._action.running_info
        if rinfo.type is RunningType.LEGACY_CALC or rinfo.type is RunningType.PROCESS:
            return WaitOnProcessTerminated(rinfo.pid)
        elif rinfo.type is RunningType.LEGACY_WORKFLOW:
            return WaitOnWorkflow(rinfo.pid)

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
        super(UpdateContext, self).load_instance_state(saved_state)

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
    if isinstance(running_info, apricotpy.Awaitable):
        return running_info
    elif running_info.type == RunningType.PROCESS:
        return Action(running_info, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type == RunningType.LEGACY_CALC:
        return Action(running_info, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type is RunningType.LEGACY_WORKFLOW:
        return Action(running_info, get_object_string(_get_wf_outputs))
