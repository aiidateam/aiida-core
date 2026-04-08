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
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from aiida import orm


class DumpMode(Enum):
    INCREMENTAL = auto()
    OVERWRITE = auto()
    DRY_RUN = auto()


class GroupDumpScope(Enum):
    IN_GROUP = auto()
    ANY = auto()
    NO_GROUP = auto()


def _load_computer_validator(value: Union[int, str, orm.Computer]) -> orm.Computer:
    """Pydantic validator to load an ``orm.Computer`` from identifier."""
    if isinstance(value, orm.Computer):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_computer(identifier=value)


def _load_code_validator(value: Union[int, str, orm.Code]) -> orm.Code:
    """Pydantic validator to load an ``orm.Code`` from identifier."""
    if isinstance(value, orm.Code):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_code(identifier=value)


def _validate_user_input(value: Optional[Union[orm.User, str]]) -> orm.User | None:
    """Load User object from email string."""
    if value is None or isinstance(value, orm.User):
        return value
    elif isinstance(value, str):
        return orm.User.collection.get(email=value)


def _validate_computers_input(value: Optional[Union[List[orm.Computer], List[str]]]) -> Optional[List[orm.Computer]]:
    """Load Computer objects from identifiers."""
    if not value:
        return None

    # Apply the validator to each item in the list
    return [_load_computer_validator(item) for item in value]


def _validate_codes_input(value: Optional[Union[List[orm.Code], List[str]]]) -> Optional[List[orm.Code]]:
    """Load Code objects from identifiers."""
    if not value:
        return None

    # Check if all items are strings
    if all(isinstance(item, str) for item in value):
        return [_load_code_validator(item) for item in value]

    # Check if all items are orm.Code objects
    if all(isinstance(item, orm.Code) for item in value):
        # Return list of orm.Code objects as-is
        # mypy doesn't correctly resolve with all and isinstance
        return value  # type: ignore[return-value]

    # Mixed types - not allowed
    types_found = {type(item).__name__ for item in value}
    msg = (
        f"Mixed types in 'groups' list not allowed. Found: {types_found}. "
        'Must be either all strings (UUIDs/labels) OR all Group objects.'
    )
    raise ValueError(msg)


def _validate_groups_input(value: Optional[Union[List[orm.Group], List[str]]]) -> Optional[List[orm.Group]]:
    """Utility function to validate groups input - must be either all strings OR all Group objects."""
    if not value:
        return None

    # Check if all items are strings
    if all(isinstance(item, str) for item in value):
        return [orm.load_group(v) for v in value]

    # Check if all items are orm.Group objects
    if all(isinstance(item, orm.Group) for item in value):
        # Return list of orm.Group objects as-is
        # mypy doesn't correctly resolve with all and isinstance
        return value  # type: ignore[return-value]

    # Mixed types - not allowed
    types_found = {type(item).__name__ for item in value}
    msg = (
        f"Mixed types in 'groups' list not allowed. Found: {types_found}. "
        'Must be either all strings (UUIDs/labels) OR all Group objects.'
    )
    raise ValueError(msg)


class BaseDumpConfig(BaseModel):
    """Base configuration for all dump operations."""

    # Model Configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    # Global options
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
    def _resolve_dump_mode_from_flags(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Map incoming CLI click options to internal representation."""
        # Convert Dump Mode

        if values.pop('dry_run', False):
            values['dump_mode'] = DumpMode.DRY_RUN
        elif values.pop('overwrite', False):
            values['dump_mode'] = DumpMode.OVERWRITE
        else:
            values['dump_mode'] = DumpMode.INCREMENTAL

        return values


class TimeFilterMixin(BaseModel):
    """Mixin for time-based filtering options."""

    start_date: Optional[datetime] = Field(default=None, description='Start date/time for modification time filter')
    end_date: Optional[datetime] = Field(default=None, description='End date/time for modification time filter')
    past_days: Optional[int] = Field(default=None, description='Number of past days to include based on mtime')
    filter_by_last_dump_time: bool = Field(default=True, description='Filter nodes by mtime since last dump')

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
    user: Optional[orm.User] = Field(default=None, description='User object or email to filter by')
    computers: Optional[List[orm.Computer]] = Field(
        default=None, description='List of Computer objects or UUIDs/labels to filter by'
    )
    codes: Optional[List[orm.Code]] = Field(
        default=None, description='List of Code objects or UUIDs/labels to filter by'
    )

    @field_validator('user', mode='before')
    @classmethod
    def validate_user(cls, v):
        return _validate_user_input(v)

    @field_validator('computers', mode='before')
    @classmethod
    def validate_computers(cls, v):
        return _validate_computers_input(v)

    @field_validator('codes', mode='before')
    @classmethod
    def validate_codes(cls, v):
        return _validate_codes_input(v)


class ProcessHandlingMixin(BaseModel):
    """Mixin for node collection options."""

    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    symlink_calcs: bool = False


class GroupManagementMixin(BaseModel):
    """Mixin for group management options."""

    delete_missing: bool = True
    organize_by_groups: bool = True
    relabel_groups: bool = True


class ProcessDumpConfig(BaseDumpConfig, ProcessHandlingMixin):
    """Configuration for dumping individual process nodes."""

    # Process dumps don't need additional configuration beyond the base config and process handling
    pass


class GroupDumpConfig(BaseDumpConfig, ProcessHandlingMixin, TimeFilterMixin, EntityFilterMixin, GroupManagementMixin):
    """Configuration for dumping groups."""

    groups: Optional[Union[List[orm.Group], List[str], List[int]]] = Field(
        default=None, description='Groups to dump (either list of PKs/UUIDs/labels OR list of Group objects)'
    )

    # Group-specific options
    group_scope: GroupDumpScope = Field(
        default=GroupDumpScope.IN_GROUP,
        exclude=True,  # Exclude from standard serialization, internal class
    )

    @field_validator('groups', mode='before')
    @classmethod
    def validate_groups(cls, v):
        return _validate_groups_input(v)

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


class ProfileDumpConfig(BaseDumpConfig, ProcessHandlingMixin, TimeFilterMixin, EntityFilterMixin, GroupManagementMixin):
    """Configuration for dumping entire profiles."""

    groups: Optional[Union[List[orm.Group], List[str], List[int]]] = Field(
        default=None, description='Groups to dump (either list of UUIDs/labels OR list of Group objects)'
    )

    # Profile-specific options
    all_entries: bool = False
    also_ungrouped: bool = False
    group_scope: GroupDumpScope = Field(
        default=GroupDumpScope.ANY,
        exclude=True,  # Exclude from standard serialization, internal class
    )

    @field_validator('groups', mode='before')
    @classmethod
    def validate_groups(cls, v):
        return _validate_groups_input(v)

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


# Rebuild all models to resolve forward references
ProcessDumpConfig.model_rebuild(force=True)
GroupDumpConfig.model_rebuild(force=True)
ProfileDumpConfig.model_rebuild(force=True)
