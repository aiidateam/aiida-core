###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Configuration infrastructure for data dumping."""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from aiida import orm
from aiida.common.log import AIIDA_LOGGER

__all__ = ('DumpConfigType', 'DumpMode', 'GroupDumpConfig', 'ProcessDumpConfig', 'ProfileDumpConfig')

DumpConfigType = Union['ProcessDumpConfig', 'GroupDumpConfig', 'ProfileDumpConfig']


logger = AIIDA_LOGGER.getChild('tools.dumping.config')


class DumpMode(Enum):
    INCREMENTAL = auto()
    OVERWRITE = auto()
    DRY_RUN = auto()


class GroupDumpScope(Enum):
    IN_GROUP = auto()
    ANY = auto()
    NO_GROUP = auto()


def _load_computer_validator(value: Optional[Union[int, str, orm.Computer]]) -> orm.Computer | None:
    """Pydantic validator to load an ``orm.Computer`` from identifier."""
    if value is None or isinstance(value, orm.Computer):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_computer(identifier=value)


def _load_code_validator(value: Optional[Union[int, str, orm.Code]]) -> orm.Code | None:
    """Pydantic validator to load an ``orm.Code`` from identifier."""
    if value is None or isinstance(value, orm.Code):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_code(identifier=value)


# Define Annotated types to apply the validators to list items
ComputerOrNone = Annotated[Optional[orm.Computer], BeforeValidator(_load_computer_validator)]
CodeOrNone = Annotated[Optional[orm.Code], BeforeValidator(_load_code_validator)]


class BaseDumpConfig(BaseModel):
    """Base configuration for all dump operations."""

    # Model Configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    # Global options - use default_factory to ensure proper precedence
    dump_mode: DumpMode = Field(default=DumpMode.INCREMENTAL, description='Dump mode to use')

    # Process dump options - common to all dump types
    include_inputs: bool = True
    include_outputs: bool = False
    include_attributes: bool = True
    include_extras: bool = False
    flat: bool = False
    dump_unsealed: bool = False

    @model_validator(mode='before')
    @classmethod
    def _map_click_options_to_internal(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Map incoming Click-option-like keys to internal representation."""
        # Handle Dump Mode - set default if not already set
        if 'dump_mode' not in values:
            if values.pop('dry_run', False):
                values['dump_mode'] = DumpMode.DRY_RUN
            elif values.pop('overwrite', False):
                values['dump_mode'] = DumpMode.OVERWRITE
            else:
                values['dump_mode'] = DumpMode.INCREMENTAL
        else:
            # Clean up dry_run/overwrite if dump_mode is explicitly set
            values.pop('dry_run', None)
            values.pop('overwrite', None)

        return values


class TimeFilterMixin(BaseModel):
    """Mixin for time-based filtering options."""

    start_date: Optional[datetime] = Field(default=None, description='Start date/time for modification time filter')
    end_date: Optional[datetime] = Field(default=None, description='End date/time for modification time filter')
    past_days: Optional[int] = Field(default=None, description='Number of past days to include based on mtime.')
    filter_by_last_dump_time: bool = True

    @model_validator(mode='after')
    def _check_date_filters(self) -> 'TimeFilterMixin':
        """Ensure past_days is not used with start_date or end_date."""
        if self.past_days is not None and (self.start_date is not None or self.end_date is not None):
            msg = 'Cannot use `past_days` filter together with `start_date` or `end_date`.'
            raise ValueError(msg)
        return self


class EntityFilterMixin(BaseModel):
    """Mixin for entity-based filtering options."""

    # Model Configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    user: Optional[Union[orm.User, str]] = Field(default=None, description='User object or email to filter by')
    computers: Optional[List[Union[orm.Computer, str]]] = Field(
        default=None, description='List of Computer objects or UUIDs/labels to filter by'
    )
    codes: Optional[List[Union[orm.Code, str]]] = Field(
        default=None, description='List of Code objects or UUIDs/labels to filter by'
    )

    @field_validator('user', mode='before')
    def _validate_user_input(cls, value: Any) -> orm.User | None:  # noqa: N805
        """Load User object from email string."""
        if value is None or isinstance(value, orm.User):
            return value
        if isinstance(value, str):
            return orm.User.collection.get(email=value)
        msg = f'Invalid input type for user: {type(value)}. Expected email string or User object.'
        raise ValueError(msg)


class NodeCollectionMixin(BaseModel):
    """Mixin for node collection options."""

    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    symlink_calcs: bool = False


class GroupManagementMixin(BaseModel):
    """Mixin for group management options."""

    delete_missing: bool = True
    organize_by_groups: bool = True
    relabel_groups: bool = True


class ProcessDumpConfig(BaseDumpConfig, NodeCollectionMixin):
    """Configuration for dumping individual process nodes."""

    # Process dumps don't need additional configuration beyond the base and node collection
    pass


class GroupDumpConfig(BaseDumpConfig, TimeFilterMixin, EntityFilterMixin, NodeCollectionMixin, GroupManagementMixin):
    """Configuration for dumping groups."""

    groups: Optional[Union[List[str], List[orm.Group]]] = Field(
        default=None, description='Groups to dump (either list of UUIDs/labels OR list of Group objects)'
    )

    # Group-specific options
    group_scope: GroupDumpScope = Field(
        default=GroupDumpScope.IN_GROUP,
        exclude=True,  # Exclude from standard serialization, internal class
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def filters_set(self) -> bool:
        """Check if any filters are configured."""
        return bool(
            self.codes
            or self.computers
            or self.groups
            or self.past_days
            or self.start_date
            or self.end_date
            or self.user
        )

    @field_validator('groups', mode='before')
    @classmethod
    def _validate_groups_input(cls, value: Any) -> Optional[Union[List[str], List[orm.Group]]]:
        """Validate groups input - must be either all strings OR all Group objects."""
        if value is None:
            return None
        if not isinstance(value, list):
            msg = f'Invalid input type for groups: {type(value)}. Expected a list.'
            raise ValueError(msg)

        if not value:  # Empty list
            return None

        # Check if all items are strings
        if all(isinstance(item, str) for item in value):
            return value  # Return list of strings as-is

        # Check if all items are orm.Group objects
        if all(isinstance(item, orm.Group) for item in value):
            return value  # Return list of orm.Group objects as-is

        # Mixed types - not allowed
        types_found = {type(item).__name__ for item in value}
        msg = (
            f"Mixed types in 'groups' list not allowed. Found: {types_found}. "
            'Must be either all strings (UUIDs/labels) OR all Group objects.'
        )
        raise ValueError(msg)


class ProfileDumpConfig(BaseDumpConfig, TimeFilterMixin, EntityFilterMixin, NodeCollectionMixin, GroupManagementMixin):
    """Configuration for dumping entire profiles."""

    groups: Optional[Union[List[str], List[orm.Group]]] = Field(
        default=None, description='Groups to dump (either list of UUIDs/labels OR list of Group objects)'
    )

    # Profile-specific options
    all_entries: bool = False
    also_ungrouped: bool = False
    group_scope: GroupDumpScope = Field(
        default=GroupDumpScope.ANY,
        exclude=True,  # Exclude from standard serialization, internal class
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def filters_set(self) -> bool:
        """Check if any filters are configured."""
        return bool(
            self.codes
            or self.computers
            or self.groups
            or self.past_days
            or self.start_date
            or self.end_date
            or self.user
        )

    @field_validator('groups', mode='before')
    @classmethod
    def _validate_groups_input(cls, value: Any) -> Optional[Union[List[str], List[orm.Group]]]:
        """Validate groups input - must be either all strings OR all Group objects."""
        if value is None:
            return None
        if not isinstance(value, list):
            msg = f'Invalid input type for groups: {type(value)}. Expected a list.'
            raise ValueError(msg)

        if not value:  # Empty list
            return None

        # Check if all items are strings
        if all(isinstance(item, str) for item in value):
            return value  # Return list of strings as-is

        # Check if all items are orm.Group objects
        if all(isinstance(item, orm.Group) for item in value):
            return value  # Return list of orm.Group objects as-is

        # Mixed types - not allowed
        types_found = {type(item).__name__ for item in value}
        msg = (
            f"Mixed types in 'groups' list not allowed. Found: {types_found}. "
            'Must be either all strings (UUIDs/labels) OR all Group objects.'
        )
        raise ValueError(msg)


# Rebuild all models to resolve forward references
ProcessDumpConfig.model_rebuild(force=True)
GroupDumpConfig.model_rebuild(force=True)
ProfileDumpConfig.model_rebuild(force=True)
