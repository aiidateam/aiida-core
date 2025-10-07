###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility module with mapper objects that map database entities projections on attributes and labels."""

from __future__ import annotations

from typing import Any, Callable

from . import formatting


class ProjectionMapper:
    """Class to map projection names from the CLI to entity labels, attributes and formatters.

    The command line interface will often have to display database entities and their attributes. The names of
    the attributes exposed on the CLI do not always match one-to-one with the attributes in the ORM and often
    they need to be formatted for the screen in some way. Additionally, for commands that display lists of entries,
    often a header needs to be printed with a label for each attribute, which also are not necessarily identical.

    For any given entity, the CLI typically exposes a set of projections, which are the keywords to reference certain
    attributes. This mapper class serves to map these projections onto the corresponding label and attribute names, as
    well as formatter functions to format the attribute values into strings, suitable to be printed by the CLI.
    """

    _valid_projections: tuple[str, ...] = ()

    def __init__(
        self,
        projection_labels: dict[str, str] | None = None,
        projection_attributes: dict[str, str] | None = None,
        projection_formatters: dict[str, Callable[[Any], str]] | None = None,
    ):
        """Construct new instance."""
        if not self._valid_projections:
            raise NotImplementedError('no valid projections were specified by the sub class')

        self._projection_labels = {}
        self._projection_attributes = {}
        self._projection_formatters = {}

        if projection_labels is not None:
            for projection in self._valid_projections:
                try:
                    self._projection_labels[projection] = projection_labels[projection]
                except KeyError:
                    self._projection_labels[projection] = projection.replace('_', ' ').capitalize()

        if projection_attributes is not None:
            for projection in self._valid_projections:
                try:
                    self._projection_attributes[projection] = projection_attributes[projection]
                except KeyError:
                    self._projection_attributes[projection] = projection

        if projection_formatters is not None:
            for projection in self._valid_projections:
                try:
                    self._projection_formatters[projection] = projection_formatters[projection]
                except KeyError:
                    attribute = self._projection_attributes[projection]
                    self._projection_formatters[projection] = lambda value, attribute=attribute: value[attribute]  # type: ignore[misc]

    @property
    def valid_projections(self) -> tuple[str, ...]:
        return self._valid_projections

    def get_label(self, projection: str) -> str:
        return self._projection_labels[projection]

    def get_attribute(self, projection: str) -> str:
        return self._projection_attributes[projection]

    def get_formatter(self, projection: str) -> Callable[[Any], str]:
        return self._projection_formatters[projection]

    def format(self, projection: str, value: Any) -> str:
        return self.get_formatter(projection)(value)


class CalculationProjectionMapper(ProjectionMapper):
    """The CLI projection mapper for Calculation derived entities."""

    def __init__(
        self,
        projections: tuple[str, ...],
        projection_labels: dict[str, str] | None = None,
        projection_attributes: dict[str, str] | None = None,
        projection_formatters: dict[str, Callable[[Any], str]] | None = None,
    ):
        from aiida.orm import ProcessNode
        from aiida.orm.nodes.caching import NodeCaching
        from aiida.orm.utils.mixins import Sealable

        self._valid_projections = projections

        sealed_key = f'attributes.{Sealable.SEALED_KEY}'
        job_state_key = 'attributes.state'
        scheduler_state_key = 'attributes.scheduler_state'
        process_paused_key = f'attributes.{ProcessNode.PROCESS_PAUSED_KEY}'
        process_label_key = f'attributes.{ProcessNode.PROCESS_LABEL_KEY}'
        process_state_key = f'attributes.{ProcessNode.PROCESS_STATE_KEY}'
        process_status_key = f'attributes.{ProcessNode.PROCESS_STATUS_KEY}'
        exit_status_key = f'attributes.{ProcessNode.EXIT_STATUS_KEY}'
        exit_message_key = f'attributes.{ProcessNode.EXIT_MESSAGE_KEY}'
        exception_key = f'attributes.{ProcessNode.EXCEPTION_KEY}'
        cached_from_key = f'extras.{NodeCaching.CACHED_FROM_KEY}'

        default_labels = {
            'pk': 'PK',
            'uuid': 'UUID',
            'ctime': 'Created',
            'mtime': 'Modified',
            'state': 'Process State',
            'cached': '\u267b',
        }

        default_attributes = {
            'pk': 'id',
            'job_state': job_state_key,
            'scheduler_state': scheduler_state_key,
            'sealed': sealed_key,
            'paused': process_paused_key,
            'process_label': process_label_key,
            'process_state': process_state_key,
            'process_status': process_status_key,
            'exit_status': exit_status_key,
            'exit_message': exit_message_key,
            'exception': exception_key,
            'cached': cached_from_key,
            'cached_from': cached_from_key,
        }

        default_formatters = {
            'ctime': lambda value: formatting.format_relative_time(value['ctime']),
            'mtime': lambda value: formatting.format_relative_time(value['mtime']),
            'state': lambda v: formatting.format_state(v[process_state_key], v[process_paused_key], v[exit_status_key]),
            'process_state': lambda value: formatting.format_process_state(value[process_state_key]),
            'sealed': lambda value: formatting.format_sealed(value[sealed_key]),
            'cached': lambda value: '\u2714' if value[cached_from_key] else '',
        }

        if projection_labels is not None:
            for projection, label in projection_labels.items():
                if projection not in self.valid_projections:
                    raise ValueError(f'{projection} is not a valid projection')
                else:
                    default_labels[projection] = label

        if projection_attributes is not None:
            for projection, attribute in projection_attributes.items():
                if projection not in self.valid_projections:
                    raise ValueError(f'{projection} is not a valid projection')
                else:
                    default_attributes[projection] = attribute

        if projection_formatters is not None:
            for projection, formatter in projection_formatters.items():
                if projection not in self.valid_projections:
                    raise ValueError(f'{projection} is not a valid projection')
                else:
                    default_formatters[projection] = formatter

        super().__init__(default_labels, default_attributes, default_formatters)
