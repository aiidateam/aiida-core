# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base implementation of `WorkChain` class that implements a simple automated restart mechanism for sub processes."""
from aiida import orm
from aiida.common import AttributeDict
from aiida.common.lang import classproperty

from .context import ToContext, append_
from .workchain import WorkChain
from .utils import ProcessHandlerReport

__all__ = ('BaseRestartWorkChain',)


class BaseRestartWorkChain(WorkChain):
    """Base restart work chain.

    This work chain serves as the starting point for more complex work chains that will be designed to run a sub process
    that might need multiple restarts to come to a successful end. These restarts may be necessary because a single
    process run is not sufficient to achieve a fully converged result, or certain errors maybe encountered which
    are recoverable.

    This work chain implements the most basic functionality to achieve this goal. It will launch the sub process,
    restarting until it is completed successfully or the maximum number of iterations is reached. It can recover from
    errors through error handlers that can be registered to the class through the `register_process_handler` decorator.

    The idea is to sub class this work chain and leverage the generic error handling that is implemented in the few
    outline methods. The minimally required outline would look something like the following::

        cls.setup
        while_(cls.should_run_process)(
            cls.run_process,
            cls.inspect_process,
        )

    Each of these methods can of course be overriden but they should be general enough to fit most process cycles. The
    `run_process` method will take the inputs for the process from the context under the key `inputs`. The user should,
    therefore, make sure that before the `run_process` method is called, that the to be used inputs are stored under
    `self.ctx.inputs`. One can update the inputs based on the results from a prior process by calling an outline method
    just before the `run_process` step, for example::

        cls.setup
        while_(cls.should_run_process)(
            cls.prepare_inputs,
            cls.run_process,
            cls.inspect_process,
        )

    Where in the `prepare_calculation` method, the inputs dictionary at `self.ctx.inputs` is updated before the next
    process will be run with those inputs.

    The `_process_class` attribute should be set to the `Process` class that should be run in the loop.
    """

    _verbose = False
    _process_class = None

    _handler_entry_point = None
    __handlers = tuple()

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.input('max_iterations', valid_type=orm.Int, default=lambda: orm.Int(5),
            help='Maximum number of iterations the work chain will restart the process to finish successfully.')
        spec.input('clean_workdir', valid_type=orm.Bool, default=lambda: orm.Bool(False),
            help='If `True`, work directories of all called calculation jobs will be cleaned at the end of execution.')
        spec.exit_code(301, 'ERROR_SUB_PROCESS_EXCEPTED',
            message='The sub process excepted.')
        spec.exit_code(302, 'ERROR_SUB_PROCESS_KILLED',
            message='The sub process was killed.')
        spec.exit_code(401, 'ERROR_MAXIMUM_ITERATIONS_EXCEEDED',
            message='The maximum number of iterations was exceeded.')
        spec.exit_code(402, 'ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE',
            message='The process failed for an unknown reason, twice in a row.')

    def setup(self):
        """Initialize context variables that are used during the logical flow of the `BaseRestartWorkChain`."""
        self.ctx.process_name = self._process_class.__name__
        self.ctx.unhandled_failure = False
        self.ctx.is_finished = False
        self.ctx.iteration = 0

    def should_run_process(self):
        """Return whether a new process should be run.

        This is the case as long as the last process has not finished successfully and the maximum number of restarts
        has not yet been exceeded.
        """
        return not self.ctx.is_finished and self.ctx.iteration < self.inputs.max_iterations.value

    def run_process(self):
        """Run the next process, taking the input dictionary from the context at `self.ctx.inputs`."""
        self.ctx.iteration += 1

        try:
            unwrapped_inputs = self.ctx.inputs
        except AttributeError:
            raise AttributeError('no process input dictionary was defined in `self.ctx.inputs`')

        # Set the `CALL` link label
        unwrapped_inputs['metadata']['call_link_label'] = 'iteration_{:02d}'.format(self.ctx.iteration)

        inputs = self._wrap_bare_dict_inputs(self._process_class.spec().inputs, unwrapped_inputs)
        node = self.submit(self._process_class, **inputs)

        # Add a new empty list to the `called_process_handlers` extra. If any errors handled registered through the
        # `register_process_handler` decorator return an `ProcessHandlerReport`, their name will be appended to that
        # list.
        called_process_handlers = self.node.get_extra('called_process_handlers', [])
        called_process_handlers.append([])
        self.node.set_extra('called_process_handlers', called_process_handlers)

        self.report('launching {}<{}> iteration #{}'.format(self.ctx.process_name, node.pk, self.ctx.iteration))

        return ToContext(children=append_(node))

    def inspect_process(self):  # pylint: disable=inconsistent-return-statements,too-many-branches
        """Analyse the results of the previous process and call the handlers when necessary.

        If the process is excepted or killed, the work chain will abort. Otherwise any attached handlers will be called
        in order of their specified priority. If the process was failed and no handler returns a report indicating that
        the error was handled, it is considered an unhandled process failure and the process is relaunched. If this
        happens twice in a row, the work chain is aborted. In the case that at least one handler returned a report the
        following matrix determines the logic that is followed:

            Process  Handler    Handler     Action
            result   report?    exit code
            -----------------------------------------
            Success      yes        == 0     Restart
            Success      yes        != 0     Abort
            Failed       yes        == 0     Restart
            Failed       yes        != 0     Abort

        If no handler returned a report and the process finished successfully, the work chain's work is considered done
        and it will move on to the next step that directly follows the `while` conditional, if there is one defined in
        the outline.
        """
        node = self.ctx.children[self.ctx.iteration - 1]

        if node.is_excepted:
            return self.exit_codes.ERROR_SUB_PROCESS_EXCEPTED  # pylint: disable=no-member

        if node.is_killed:
            return self.exit_codes.ERROR_SUB_PROCESS_KILLED  # pylint: disable=no-member

        # Sort the handlers with a priority defined, based on their priority in reverse order
        handlers = [handler for handler in self._handlers if handler.priority]
        handlers = sorted(handlers, key=lambda x: x.priority, reverse=True)

        last_report = None

        for handler in handlers:

            report = handler.method(self, node)

            if report is not None and not isinstance(report, ProcessHandlerReport):
                name = handler.method.__name__
                raise RuntimeError('handler `{}` returned a value that is not a ProcessHandlerReport'.format(name))

            # If an actual report was returned, save it so it is not overridden by next handler returning `None`
            if report:
                last_report = report

            # After certain handlers, we may want to skip all other handlers
            if report and report.do_break:
                break

        report_args = (self.ctx.process_name, node.pk)

        # If the process failed and no handler returned a report we consider it an unhandled failure
        if node.is_failed and not last_report:
            if self.ctx.unhandled_failure:
                template = '{}<{}> failed and error was not handled for the second consecutive time, aborting'
                self.report(template.format(*report_args))
                return self.exit_codes.ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE  # pylint: disable=no-member

            self.ctx.unhandled_failure = True
            self.report('{}<{}> failed and error was not handled, restarting once more'.format(*report_args))
            return

        # Here either the process finished successful or at least one handler returned a report so it can no longer be
        # considered to be an unhandled failed process and therefore we reset the flag
        self.ctx.unhandled_failure = True

        # If at least one handler returned a report, the action depends on its exit code and that of the process itself
        if last_report:
            if node.is_finished_ok and last_report.exit_code.status == 0:
                template = '{}<{}> finished successfully but a handler was triggered, restarting'
            elif node.is_failed and last_report.exit_code.status == 0:
                template = '{}<{}> failed but a handler dealt with the problem, restarting'
            elif node.is_finished_ok and last_report.exit_code.status != 0:
                template = '{}<{}> finished successfully but a handler detected an unrecoverable problem, aborting'
            elif node.is_failed and last_report.exit_code.status != 0:
                template = '{}<{}> failed but a handler detected an unrecoverable problem, aborting'

            self.report(template.format(*report_args))

            return report.exit_code

        # Otherwise the process was successful and no handler returned anything so we consider the work done
        self.ctx.is_finished = True

    def results(self):  # pylint: disable=inconsistent-return-statements
        """Attach the outputs specified in the output specification from the last completed process."""
        node = self.ctx.children[self.ctx.iteration - 1]

        # We check the `is_finished` attribute of the work chain and not the successfulness of the last process
        # because the error handlers in the last iteration can have qualified a "failed" process as satisfactory
        # for the outcome of the work chain and so have marked it as `is_finished=True`.
        if not self.ctx.is_finished and self.ctx.iteration >= self.inputs.max_iterations.value:
            self.report('reached the maximum number of iterations {}: last ran {}<{}>'.format(
                self.inputs.max_iterations.value, self.ctx.process_name, node.pk))
            return self.exit_codes.ERROR_MAXIMUM_ITERATIONS_EXCEEDED  # pylint: disable=no-member

        self.report('work chain completed after {} iterations'.format(self.ctx.iteration))

        for name, port in self.spec().outputs.items():

            try:
                output = node.get_outgoing(link_label_filter=name).one().node
            except ValueError:
                if port.required:
                    self.report("required output '{}' was not an output of {}<{}>".format(
                        name, self.ctx.process_name, node.pk))
            else:
                self.out(name, output)
                if self._verbose:
                    self.report("attaching the node {}<{}> as '{}'".format(output.__class__.__name__, output.pk, name))

    def __init__(self, *args, **kwargs):
        """Construct the instance."""
        from ..process import Process  # pylint: disable=cyclic-import
        super().__init__(*args, **kwargs)

        if self._process_class is None or not issubclass(self._process_class, Process):
            raise ValueError('no valid Process class defined for `_process_class` attribute')

    @classproperty
    def _handlers(cls):  # pylint: disable=no-self-argument
        """Return the tuple of all registered handlers for this class and of any parent class.

        :return: tuple of handler methods
        """
        return getattr(super(), '__handlers', tuple()) + cls.__handlers

    @classmethod
    def register_handler(cls, name, handler):
        """Register a new handler to this class.

        :param name: the name under which to register the handler
        :param handler: a method with the signature `self, node`.
        """
        setattr(cls, name, handler)
        cls.__handlers = cls.__handlers + (handler,)

    def on_terminated(self):
        """Clean the working directories of all child calculation jobs if `clean_workdir=True` in the inputs."""
        super().on_terminated()

        if self.inputs.clean_workdir.value is False:
            self.report('remote folders will not be cleaned')
            return

        cleaned_calcs = []

        for called_descendant in self.node.called_descendants:
            if isinstance(called_descendant, orm.CalcJobNode):
                try:
                    called_descendant.outputs.remote_folder._clean()  # pylint: disable=protected-access
                    cleaned_calcs.append(str(called_descendant.pk))
                except (IOError, OSError, KeyError):
                    pass

        if cleaned_calcs:
            self.report('cleaned remote folders of calculations: {}'.format(' '.join(cleaned_calcs)))

    def _wrap_bare_dict_inputs(self, port_namespace, inputs):
        """Wrap bare dictionaries in `inputs` in a `Dict` node if dictated by the corresponding inputs portnamespace.

        :param port_namespace: a `PortNamespace`
        :param inputs: a dictionary of inputs intended for submission of the process
        :return: an attribute dictionary with all bare dictionaries wrapped in `Dict` if dictated by the port namespace
        """
        from aiida.engine.processes import PortNamespace

        wrapped = {}

        for key, value in inputs.items():

            if key not in port_namespace:
                wrapped[key] = value
                continue

            port = port_namespace[key]

            if isinstance(port, PortNamespace):
                wrapped[key] = self._wrap_bare_dict_inputs(port, value)
            elif port.valid_type == orm.Dict and isinstance(value, dict):
                wrapped[key] = orm.Dict(dict=value)
            else:
                wrapped[key] = value

        return AttributeDict(wrapped)
