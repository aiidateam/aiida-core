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
"""Helpers for process events."""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from aiida.engine.processes import persistence

if TYPE_CHECKING:
    from aiida.engine.processes.listener import ProcessListener

_LOGGER = logging.getLogger(__name__)


@persistence.auto_persist('_listeners', '_listener_type')
class EventHelper(persistence.Savable):
    """Maintain a set of listeners and dispatch process events to them."""

    def __init__(self, listener_type: 'type[ProcessListener]'):
        """Construct the helper for listeners of the given type.

        :param listener_type: the process listener class that registered listeners should be instances of
        :raises AssertionError: if the listener type is ``None``
        """
        assert listener_type is not None, 'Must provide valid listener type'

        self._listener_type = listener_type
        self._listeners: set[ProcessListener] = set()

    def add_listener(self, listener: 'ProcessListener') -> None:
        """Register a listener to be notified of events.

        :param listener: the listener to add
        :raises AssertionError: if the listener is not an instance of the listener type
        """
        assert isinstance(listener, self._listener_type), 'Listener is not of right type'
        self._listeners.add(listener)

    def remove_listener(self, listener: 'ProcessListener') -> None:
        """Unregister a listener, if it is currently registered.

        :param listener: the listener to remove
        """
        self._listeners.discard(listener)

    def remove_all_listeners(self) -> None:
        """Unregister all currently registered listeners."""
        self._listeners.clear()

    @property
    def listeners(self) -> 'set[ProcessListener]':
        """Return the currently registered listeners.

        :return: the set of registered listeners
        """
        return self._listeners

    def fire_event(self, event_function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Call an event method on all listeners.

        Exceptions raised by a listener are logged rather than propagated, so that one broken listener cannot
        prevent the remaining ones from being notified.

        :param event_function: the method of the ProcessListener
        :param args: arguments to pass to the method
        :param kwargs: keyword arguments to pass to the method
        :raises ValueError: if the event method is ``None``
        """
        if event_function is None:
            raise ValueError('Must provide valid event method')

        # Make a copy of the list for iteration just in case it changes in a callback
        for listener in list(self.listeners):
            try:
                getattr(listener, event_function.__name__)(*args, **kwargs)
            except Exception as exception:
                _LOGGER.error("Listener '%s' produced an exception:\n%s", listener, exception)
