# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import abc
import plumpy
from threading import local
import time
import random
from aiida.common.links import LinkType
from aiida.common.lang import override, protected
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.calculation import Calculation
from aiida.orm.data.frozendict import FrozenDict

from . import class_loader

__all__ = ['ProcessStack']

load_object = plumpy.utils.load_object
load_class = load_object


def class_name(identifier, verify=True):
    return plumpy.utils.class_name(identifier, class_loader.CLASS_LOADER, verify)


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

        self._heartbeat_expires = None
        self._heartbeat_tag = random.randint(0, 2147483647)

        self._heartbeat_callback = None

    def on_loop_inserted(self, loop):
        super(CalculationHeartbeat, self).on_loop_inserted(loop)

        self._acquire_heartbeat()

        # Figure out how long we've got left and give us a bit of leeway
        delta = self._heartbeat_expires - loop.time()
        self._heartbeat_callback = self.loop().call_later(0.9 * delta, self.run)

    def run(self):
        self._heartbeat_callback = None

        if self._update_heartbeat():
            # Figure out how long we've got left and give us a bit of leeway
            delta = self._heartbeat_expires - self.loop().time()
            self._heartbeat_callback = self.loop().call_later(0.9 * delta, self.run)
        else:
            # Lost the heartbeat
            if self._lost_callback is not None:
                self.loop().call_soon(self._lost_callback, self)

            self.loop().remove(self)

    def on_loop_removed(self):
        if self._heartbeat_callback is not None:
            self._heartbeat_callback.cancel()

        # Try to clean up after ourselves
        try:
            self._calc._del_attr(self.HEARTBEAT_EXPIRES)
            self._calc._del_attr(self.HEARTBEAT_TAG)
        except ModificationNotAllowed:
            pass

    def _acquire_heartbeat(self):
        current_expiry = self._calc.get_attr(self.HEARTBEAT_EXPIRES, None)
        if current_expiry is None or current_expiry < self.loop().time():
            expiry_time = time.time() + self._beat_interval
            try:
                self._calc._set_attr(self.HEARTBEAT_EXPIRES, expiry_time)
                self._calc._set_attr(self.HEARTBEAT_TAG, self._heartbeat_tag)
            except ModificationNotAllowed as e:
                raise HeartbeatError("Failed to acquire heartbeat\n{}".format(e.message))
            else:
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
            if not self._update_expiry():
                return False

            if not self._update_tag():
                return False

            return True
        else:
            return False

    def _update_expiry(self):
        expiry_time = self.loop().time() + self._beat_interval
        try:
            self._calc._set_attr(self.HEARTBEAT_EXPIRES, expiry_time)
        except ModificationNotAllowed:
            return False

        self._heartbeat_expires = expiry_time
        return True

    def _update_tag(self):
        tag = (self._heartbeat_tag + 1) % 2147483647
        try:
            self._calc._set_attr(self.HEARTBEAT_TAG, tag)
        except ModificationNotAllowed:
            return False

        self._heartbeat_tag = tag
        return True


class HeartbeatMixin(object):
    """
    A mixin of sorts to add a calculation heartbeat to Process calculations.
    """

    def __init__(self, *args, **kwargs):
        super(HeartbeatMixin, self).__init__(*args, **kwargs)
        self._heartbeat = None

    def on_loop_inserted(self, loop):
        super(HeartbeatMixin, self).on_loop_inserted(loop)
        self._start_heartbeat()

    def on_loop_removed(self):
        self._stop_heartbeat()
        super(HeartbeatMixin, self).on_loop_removed()

    def on_start(self):
        super(HeartbeatMixin, self).on_start()
        assert self._heartbeat is not None

    def on_run(self):
        super(HeartbeatMixin, self).on_run()
        assert self._heartbeat is not None

    def on_wait(self, awaiting_uuid):
        super(HeartbeatMixin, self).on_wait(awaiting_uuid)
        assert self._heartbeat is not None

    def on_resume(self):
        super(HeartbeatMixin, self).on_resume()
        assert self._heartbeat is not None

    def on_finish(self):
        super(HeartbeatMixin, self).on_finish()
        assert self._heartbeat is not None

    def on_stop(self):
        super(HeartbeatMixin, self).on_stop()
        assert self._heartbeat is not None
        self._stop_heartbeat()

    def on_fail(self, exc_info):
        super(HeartbeatMixin, self).on_fail(exc_info)

        # Check here if we still have a heartbeat, the reason for the failure
        # may be precisely because we lost it.
        if self._heartbeat is not None:
            self._stop_heartbeat()

    @override
    def on_stop(self):
        super(HeartbeatMixin, self).on_stop()
        self._stop_heartbeat()

    @protected
    def has_heartbeat(self):
        return self._heartbeat is not None

    def _start_heartbeat(self):
        self._heartbeat = CalculationHeartbeat(self.calc, lost_callback=self._heartbeat_lost)
        self.loop()._insert(self._heartbeat)

    def _stop_heartbeat(self):
        if self._heartbeat is not None:
            self.loop()._remove(self._heartbeat)
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
