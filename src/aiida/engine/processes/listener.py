###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################
import abc
from typing import TYPE_CHECKING, Any

from aiida.common.lang import protected as protected_decorator
from aiida.engine.processes import persistence
from aiida.engine.processes.persistence import SAVED_STATE_TYPE
from aiida.engine.processes.settings import check_protected

__all__: tuple[str, ...] = ()

protected = protected_decorator(check=check_protected)

if TYPE_CHECKING:
    from aiida.engine.processes.generic.process import Process


@persistence.auto_persist('_params')
class ProcessListener(persistence.Savable, metaclass=abc.ABCMeta):
    # region Persistence methods

    def __init__(self) -> None:
        super().__init__()
        self._params: dict[str, Any] = {}

    def init(self, **kwargs: Any) -> None:
        self._params = kwargs

    @protected
    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self.init(**saved_state['_params'])

    # endregion

    def on_process_created(self, process: 'Process') -> None:
        """
        Called when the process has been started

        :param process: The process

        """

    def on_process_running(self, process: 'Process') -> None:
        """
        Called when the process is about to enter the RUNNING state

        :param process: The process

        """

    def on_process_waiting(self, process: 'Process') -> None:
        """
        Called when the process is about to enter the WAITING state

        :param process: The process

        """

    def on_process_paused(self, process: 'Process') -> None:
        """
        Called when the process is about to re-enter the RUNNING state

        :param process: The process

        """

    def on_process_played(self, process: 'Process') -> None:
        """
        Called when the process is about to re-enter the RUNNING state

        :param process: The process

        """

    def on_output_emitted(self, process: 'Process', output_port: str, value: Any, dynamic: bool) -> None:
        """
        Called when the process has emitted an output value

        :param process: The process
        :param output_port: The output port that the value was outputted on
        :param value: The value that was outputted
        :param dynamic: True if the port is dynamic, False otherwise

        """

    def on_process_finished(self, process: 'Process', outputs: Any) -> None:
        """
        Called when the process has finished successfully

        :param process: The process
        :param outputs: The process outputs

        """

    def on_process_excepted(self, process: 'Process', reason: str) -> None:
        """
        Called when the process has excepted

        :param process: The process
        :param reason: A string of the exception message

        """

    def on_process_killed(self, process: 'Process', msg: str) -> None:
        """
        Called when the process was killed

        :param process: The process

        """
