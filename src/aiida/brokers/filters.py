###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Filters to limit which broadcast messages are received."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

__all__ = ('BroadcastFilter',)


class BroadcastFilter:
    """A filter that can be used to limit the subjects and/or senders that will be received."""

    def __init__(self, subscriber: Callable[..., Any], subject: Any = None, sender: Any = None) -> None:
        self._subscriber = subscriber
        self._subject_filters: list[Callable[[Any], Any]] = []
        self._sender_filters: list[Callable[[Any], Any]] = []
        if subject is not None:
            self.add_subject_filter(subject)
        if sender is not None:
            self.add_sender_filter(sender)

    @property
    def __name__(self) -> str:
        return 'BroadcastFilter'

    def __call__(
        self,
        communicator: Any,
        body: Any,
        sender: Any = None,
        subject: Any = None,
        correlation_id: Any = None,
    ) -> Any:
        if self.is_filtered(sender, subject):
            return None
        return self._subscriber(communicator, body, sender, subject, correlation_id)

    def is_filtered(self, sender: Any, subject: Any) -> bool:
        if subject is not None and self._subject_filters and not any(check(subject) for check in self._subject_filters):
            return True

        if sender is not None and self._sender_filters and not any(check(sender) for check in self._sender_filters):
            return True

        return False

    def add_subject_filter(self, subject_filter: Any) -> None:
        self._subject_filters.append(self._ensure_filter(subject_filter))

    def add_sender_filter(self, sender_filter: Any) -> None:
        self._sender_filters.append(self._ensure_filter(sender_filter))

    @classmethod
    def _ensure_filter(cls, filter_value: Any) -> Callable[[Any], Any]:
        if isinstance(filter_value, str):
            return re.compile(filter_value.replace('.', '[.]').replace('*', '.*')).match
        if isinstance(filter_value, re.Pattern):
            return filter_value.match

        return lambda val: val == filter_value
