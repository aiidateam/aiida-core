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
from typing import Any

from aiida.common.extendeddicts import AttributeDict
from aiida.engine.processes import persistence
from aiida.engine.processes.persistence import SAVED_STATE_TYPE

__all__: tuple[str, ...] = ()


class ContextMixin(persistence.Savable):
    """
    Add a context to a Process.  The contents of the context will be saved
    in the instance state unlike standard instance variables.
    """

    CONTEXT: str = '_context'

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._context: AttributeDict | None = AttributeDict()

    @property
    def ctx(self) -> AttributeDict | None:
        return self._context

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        """Add the instance state to ``out_state``.
        .. important::

            The instance state will contain a pointer to the ``ctx``,
            and so should be deep copied or serialised before persisting.
        """
        super().save_instance_state(out_state, save_context)
        if self._context is not None:
            out_state[self.CONTEXT] = self._context.__dict__

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        try:
            self._context = AttributeDict(saved_state[self.CONTEXT])
        except KeyError:
            pass
