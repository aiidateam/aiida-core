# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import importlib
import threading
from threading import local
import time
import random
import plum.process
from aiida.common.links import LinkType
from aiida.common.lang import override, protected
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.calculation import Calculation
from aiida.orm.data.frozendict import FrozenDict

# The name of the attribute to store the label of a process in a node with.
PROCESS_LABEL_ATTR = '_process_label'


class ProcessStack(object):
    """
    Keep track of the per-thread call stack of processes.
    """
    # Use thread-local storage for the stack
    _thread_local = local()

    @classmethod
    def get_active_process_id(cls):
        """
        Get the pid of the process at the top of the stack

        :return: The pid
        """
        return cls.top().pid

    @classmethod
    def get_active_process_calc_node(cls):
        """
        Get the calculation node of the process at the top of the stack

        :return: The calculation node
        :rtype: :class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation`
        """
        return cls.top().calc

    @classmethod
    def top(cls):
        return cls.stack()[-1]

    @classmethod
    def stack(cls):
        try:
            return cls._thread_local.wf_stack
        except AttributeError:
            cls._thread_local.wf_stack = []
            return cls._thread_local.wf_stack

    @classmethod
    def pids(cls):
        try:
            return cls._thread_local.pids_stack
        except AttributeError:
            cls._thread_local.pids_stack = []
            return cls._thread_local.pids_stack

    @classmethod
    def push(cls, process):
        try:
            process._parent = cls.top()
        except IndexError:
            process._parent = None
        cls.stack().append(process)
        cls.pids().append(process.pid)

    @classmethod
    def pop(cls, process=None, pid=None):
        """
        Pop a process from the stack.  To make sure the stack is not corrupted
        the process instance or pid of the calling process should be supplied
        so we can verify that is really is top of the stack.

        :param process: The process instance
        :param pid: The process id.
        """
        assert process is not None or pid is not None
        if process is not None:
            assert process is cls.top(), \
                "Can't pop a process that is not top of the stack"
        elif pid is not None:
            assert pid == cls.pids()[-1], \
                "Can't pop a process that is not top of the stack"
        else:
            raise ValueError("Must supply process or pid")

        process = cls.stack().pop()
        process._parent = None

        cls.pids().pop()

    def __init__(self):
        raise NotImplementedError("Can't instantiate the ProcessStack")


def load_class(classstring):
    """
    Load a class from a string
    """
    class_data = classstring.split(".")
    module_path = ".".join(class_data[:-1])
    class_name = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_name)


def is_workfunction(func):
    try:
        return func._is_workfunction
    except AttributeError:
        return False


class HeartbeatError(BaseException):
    pass


class CalculationHeartbeat(object):
    """
    This class implements a thread that runs in the background updating the
    heartbeat expiry of a calculation.  The intended behaviour is that while
    the heartbeat is alive the process that created it has permission to change
    the calculation.  It is a type of optimistic locking.

    If the heartbeat has lost ownership over the calculation it will stop and
    call an optional (given) callback

    .. warning::
        This class is not immune to race conditions, i.e. two hearbeats trying
        to take ownership simultaneously could collide.  Until we have a
        QUERY+UPDATE atomic operation it is not possible to avoid this but the
        problem *should* be discovered at the next beat.
    """
    # The attribute used to store the expiry
    HEARTBEAT_EXPIRES = 'heartbeat_expires'
    HEARTBEAT_TAG = 'heartbeat_tag'
    DEFAULT_BEAT_INTERVAL = 60.0  # seconds

    def __init__(self, calc, beat_interval=DEFAULT_BEAT_INTERVAL, lost_callback=None):
        super(CalculationHeartbeat, self).__init__()
        self._calc = calc
        self._beat_interval = beat_interval
        self._lost_callback = lost_callback

        self._finished = threading.Event()
        self._heartbeat_expires = None
        self._heartbeat_tag = random.randint(0, 2147483647)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @override
    def start(self):
        from aiida.work.globals import get_heartbeat_pool

        self._acquire_heartbeat()
        future = get_heartbeat_pool().submit(self.run)
        while not future.running():
            pass

    @override
    def run(self):
        # Here we should have the lock already from the start() call
        while not self._finished.is_set():
            # Figure out how long we've got left and give us a bit of leeway
            delta = self._heartbeat_expires - time.time()
            if self._finished.wait(timeout=0.9 * delta):
                break
            if not self._update_heartbeat():
                break
        self._heartbeat_expires = None

    def stop(self):
        # Check if we've started
        if self._heartbeat_expires is not None:
            self._finished.set()
            # Try to clean up after ourselves
            try:
                self._calc._del_attr(self.HEARTBEAT_EXPIRES)
                self._calc._del_attr(self.HEARTBEAT_TAG)
            except ModificationNotAllowed:
                pass

    def _acquire_heartbeat(self):
        current_expiry = self._calc.get_attr(self.HEARTBEAT_EXPIRES, None)
        if current_expiry is None or current_expiry < time.time():
            expiry_time = time.time() + self._beat_interval
            try:
                self._calc._set_attr(self.HEARTBEAT_EXPIRES, expiry_time)
                self._calc._set_attr(self.HEARTBEAT_TAG, self._heartbeat_tag)
            except ModificationNotAllowed as e:
                raise HeartbeatError("Failed to acquire heartbeat\n{}".format(e.message))
            self._heartbeat_expires = expiry_time
        else:
            raise HeartbeatError(
                "Failed to acquire heartbeat, it is currently locked.")

    def _update_heartbeat(self):
        """
        Set the calculation attribute that stores when the heartbeat will
        timeout to be the current time plus timeout but only if the
        calculation is owned by us or not owned at all.
        """
        tag = self._calc.get_attr(self.HEARTBEAT_TAG, None)

        # Check that we still have the heartbeat
        if tag == self._heartbeat_tag:
            self._update_expiry()
            self._update_tag()
            return True
        else:
            # Lost the heartbeat
            if self._lost_callback is not None:
                self._lost_callback(self)
            return False

    def _update_expiry(self):
        expiry_time = time.time() + self._beat_interval
        self._calc._set_attr(self.HEARTBEAT_EXPIRES, expiry_time)
        self._heartbeat_expires = expiry_time

    def _update_tag(self):
        tag = (self._heartbeat_tag + 1) % 2147483647
        self._calc._set_attr(self.HEARTBEAT_TAG, tag)
        self._heartbeat_tag = tag


class WithHeartbeat(plum.process.Process):
    """
    A mixin of sorts to add a calculation heartbeat to Process calculations.
    """

    def __init__(self, inputs, pid, logger=None):
        super(WithHeartbeat, self).__init__(inputs, pid, logger)
        self._heartbeat = None

    @override
    def on_playing(self):
        super(WithHeartbeat, self).on_playing()
        self._start_heartbeat()

    @override
    def on_done_playing(self):
        super(WithHeartbeat, self).on_done_playing()
        self._stop_heartbeat()

    def on_start(self):
        super(WithHeartbeat, self).on_start()
        assert self._heartbeat is not None

    def on_run(self):
        super(WithHeartbeat, self).on_run()
        assert self._heartbeat is not None

    def on_wait(self, wait_on):
        super(WithHeartbeat, self).on_wait(wait_on)
        assert self._heartbeat is not None

    def on_resume(self):
        super(WithHeartbeat, self).on_resume()
        assert self._heartbeat is not None

    def on_finish(self):
        super(WithHeartbeat, self).on_finish()
        assert self._heartbeat is not None

    def on_stop(self):
        super(WithHeartbeat, self).on_stop()
        assert self._heartbeat is not None
        self._stop_heartbeat()

    def on_fail(self):
        super(WithHeartbeat, self).on_fail()
        # Check here if we still have a heartbeat, the reason for the failure
        # may be precisely because we lost it.
        if self._heartbeat is not None:
            self._stop_heartbeat()

    @override
    def on_stop(self):
        super(WithHeartbeat, self).on_stop()
        self._stop_heartbeat()

    @protected
    def has_heartbeat(self):
        return self._heartbeat is not None

    def _start_heartbeat(self):
        self._heartbeat = CalculationHeartbeat(
            self.calc, lost_callback=self._heartbeat_lost)
        self._heartbeat.start()

    def _stop_heartbeat(self):
        if self._heartbeat is not None:
            self._heartbeat.stop()
            self._heartbeat = None

    def _heartbeat_lost(self, heartbeat):
        self._heartbeat = None


def get_or_create_output_group(calculation):
    """
    For a given Calculation, get or create a new frozendict Data node that
    has as its values all output Data nodes of the Calculation.

    :param calculation: Calculation
    """
    if not isinstance(calculation, Calculation):
        raise TypeError("Can only create output groups for type Calculation")

    d = calculation.get_outputs_dict(link_type=LinkType.CREATE)
    d.update(calculation.get_outputs_dict(link_type=LinkType.RETURN))

    return FrozenDict(dict=d)
