from __future__ import annotations

import logging
import traceback
from typing import Any

from node_graph.error_handler import ErrorHandlerSpec


class ErrorHandlerManager:
    def __init__(self, process: Any, logger: logging.Logger) -> None:
        self.process = process
        self.logger = logger

    @property
    def ctx(self) -> Any:
        """Read the context off the process, which replaces it wholesale when loading from a checkpoint."""
        return self.process.ctx

    def run_error_handlers(self, task_name: str) -> None:
        """Run error handlers for a task."""

        self.process.report(f'Run error handlers for {task_name}')

        node = self.process.task_manager.state_manager.get_task_runtime_info(task_name, 'process')
        if not node or not node.exit_status:
            return
        # error_handlers from the task
        error_handlers = self.process.wg.tasks[task_name].get_error_handlers()
        for data in error_handlers.values():
            if node.exit_status in data.exit_codes:
                self.run_error_handler(data, task_name)
                return
        # error_handlers from the workgraph
        for data in self.process.wg._error_handlers.values():
            if node.exit_code.status in data['tasks'].get(task_name, {}).get('exit_codes', []):
                self.run_error_handler(data, task_name)
                return

    def run_error_handler(self, handler: ErrorHandlerSpec, task_name: str) -> None:
        """Run the error handler for a task."""
        from inspect import signature

        from node_graph.executor import RuntimeExecutor

        executor = RuntimeExecutor(**handler.executor.to_dict()).callable
        executor_sig = signature(executor)
        self.process.report(f'Run error handler: {executor.__name__}')
        if handler.retry < handler.max_retries:
            task = self.process.task_manager.get_task(task_name)
            prev_allow_overrides = getattr(task, '_allow_input_overrides', False)
            try:
                task.set_input_resolver(self.process.task_manager.get_socket_value)
                task._allow_input_overrides = True
                # Run the error handler to update the inputs of the task
                if 'engine' in executor_sig.parameters:
                    msg = executor(task, engine=self, **(handler.kwargs or {}))
                else:
                    msg = executor(task, **(handler.kwargs or {}))
                # Reset the task to rerun it
                self.process.task_manager.state_manager.reset_task(task.name)
                # Save the updated task into self.ctx._wgdata
                tdata = task.to_dict()
                self.ctx._wgdata['tasks'][task.name] = tdata
                if msg:
                    self.process.report(msg)
                handler.retry += 1
            except Exception as e:
                error_traceback = traceback.format_exc()  # Capture the full traceback
                self.logger.error(f'Error in running error handler for {task_name}: {e}\n{error_traceback}')
                self.process.report(f'Error in running error handler for {task_name}: {e}\n{error_traceback}')
            finally:
                task._allow_input_overrides = prev_allow_overrides
