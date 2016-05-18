# -*- coding: utf-8 -*-

import plum.port as port
from aiida.workflows2.process import Process
from aiida.workflows2.legacy.wait_on import WaitOnJobCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class JobCalculation(Process):
    CALC_NODE_LABEL = 'calc_node'
    _CALC_CLASS = None

    @classmethod
    def build(cls, calc_class):

        def _define(spec):
            for k, v in calc_class._use_methods.iteritems():
                if v.get('additional_parameter'):
                    spec.input_group(v['linkname'], help=v.get('docstring', None),
                                     valid_type=v['valid_types'], required=False)
                else:
                    spec.input(v['linkname'], help=v.get('docstring', None),
                               valid_type=v['valid_types'], required=False)
            spec.has_dynamic_output()

        return type(calc_class.__name__, (JobCalculation,),
                    {'_define': staticmethod(_define),
                     '_CALC_CLASS': calc_class})

    def __init__(self):
        # Need to tell Process to not create output links as these are
        # created internally by the execution manager
        super(JobCalculation, self).__init__(create_output_links=False)

        self._computer = None
        self._resources = None
        self._custom_scheduler_commands = None
        self._queue_name = None
        self._resources = None
        self._max_wallclock_seconds = None

    def set_computer(self, computer):
        self._computer = computer

    def set_resources(self, resources):
        self._resources = resources

    def set_custom_scheduler_commands(self, commands):
        self._custom_scheduler_commands = commands

    def set_queue_name(self, queue_name):
        self._queue_name = queue_name

    def set_max_wallclock_seconds(self, time):
        self._max_wallclock_seconds = time

    def _run(self, **kwargs):
        self._current_calc.submit()
        return WaitOnJobCalculation(
            self.calculation_finished.__name__, self._current_calc.pk)

    def calculation_finished(self):
        assert not self._current_calc._is_running()

        for label, node in self._current_calc.get_outputs_dict():
            self._out(label, node)

    def _create_db_record(self):
        return self._CALC_CLASS()

    def _setup_db_record(self, inputs):
        from aiida.common.links import LinkType

        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()  # (unstored)
        assert (not calc.is_stored)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in inputs.iteritems():
            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional =\
                    self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input.iteritems():
                    getattr(calc, 'use_{}'.format(name))(input, **{additional: v})

            else:
                getattr(calc, 'use_{}'.format(name))(input)

        if self._parent:
            calc.add_link_from(self._parent._current_calc, "CALL", LinkType.CALL)

        if self._computer:
            calc.set_computer(self._computer)
        elif 'code' in inputs:
            code = inputs['code']
            if not code.is_local():
                calc.set_computer(code.get_remote_computer())

        if self._resources:
            calc.set_resources(self._resources)

        if self._custom_scheduler_commands:
            calc.set_custom_scheduler_commands(self._custom_scheduler_commands)

        if self._queue_name:
            calc.set_queue_name(self._queue_name)

        if self._resources:
            calc.set_resources(self._resources)

        if self._max_wallclock_seconds:
            calc.set_max_wallclock_seconds(self._max_wallclock_seconds)

        self._current_calc = calc
        self._current_calc.store_all()
