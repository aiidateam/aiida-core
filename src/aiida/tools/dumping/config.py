###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

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
    model_serializer,
    model_validator,
)

from aiida import orm
from aiida.common.log import AIIDA_LOGGER


class DumpMode(Enum):
    INCREMENTAL = auto()
    OVERWRITE = auto()
    DRY_RUN = auto()


class GroupDumpScope(Enum):
    IN_GROUP = auto()
    ANY = auto()
    NO_GROUP = auto()


logger = AIIDA_LOGGER.getChild('tools.dumping.config')


def _load_computer_validator(value: Optional[Union[int, str, orm.Computer]]) -> orm.Computer | None:
    """Pydantic validator function to load Computer from identifier."""
    if value is None or isinstance(value, orm.Computer):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_computer(identifier=value)


def _load_code_validator(value: Optional[Union[int, str, orm.Code]]) -> orm.Code | None:
    """Pydantic validator function to load Code from identifier."""
    if value is None or isinstance(value, orm.Code):
        return value
    elif isinstance(value, (str, int)):
        return orm.load_code(identifier=value)


# Define Annotated types to apply the validators to list items
ComputerOrNone = Annotated[Optional[orm.Computer], BeforeValidator(_load_computer_validator)]
CodeOrNone = Annotated[Optional[orm.Code], BeforeValidator(_load_code_validator)]


class DumpConfig(BaseModel):
    """
    Unified Pydantic configuration for dump operations.
    Handles serialization/deserialization to/from Click-option-like keys.
    """

    # --- Model Configuration ---
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    groups: Optional[List[Union[str, orm.Group]]] = Field(default=None, description='Groups to dump (UUIDs or labels)')
    start_date: Optional[datetime] = Field(default=None, description='Start date/time for modification time filter')
    end_date: Optional[datetime] = Field(default=None, description='End date/time for modification time filter')
    past_days: Optional[int] = Field(default=None, description='Number of past days to include based on mtime.')

    user: Optional[Union[orm.User, str]] = Field(default=None, description='User object or email to filter by')

    computers: Optional[List[Union[orm.Computer, str]]] = Field(
        default=None, description='List of Computer objects or UUIDs/labels to filter by'
    )

    codes: Optional[List[Union[orm.Code, str]]] = Field(
        default=None, description='List of Code objects or UUIDs/labels to filter by'
    )

    # --- Global options ---
    dump_mode: DumpMode = DumpMode.INCREMENTAL

    # --- Node collection options ---
    filter_by_last_dump_time: bool = True
    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    group_scope: GroupDumpScope = Field(
        default=GroupDumpScope.IN_GROUP,
        exclude=True,  # Exclude from standard serialization, internal class
    )

    # --- Process dump options ---
    include_inputs: bool = True
    include_outputs: bool = False
    include_attributes: bool = True
    include_extras: bool = False
    flat: bool = False
    dump_unsealed: bool = False
    symlink_calcs: bool = False

    # --- Group/Profile options ---
    delete_missing: bool = True
    organize_by_groups: bool = True
    also_ungrouped: bool = False
    relabel_groups: bool = True
    all_entries: bool = False

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

    # --- Pydantic Field Validators ---
    @field_validator('groups', mode='before')
    @classmethod
    def _validate_groups_input(cls, value: Any) -> Optional[List[str]]:
        """
        Validate and transform the input for the 'groups' field.
        Accepts a list containing orm.Group objects or strings (labels/UUIDs),
        and converts all elements to strings (using group label).
        """
        if value is None:
            return None
        if not isinstance(value, list):
            msg = f'Invalid input type for groups: {type(value)}. Expected a list.'
            raise ValueError(msg)

        processed_groups: List[str] = []
        for item_idx, item in enumerate(value):
            if isinstance(item, orm.Group):
                processed_groups.append(item.label)
            elif isinstance(item, str):
                processed_groups.append(item)
            else:
                msg = (
                    f"Invalid item type in 'groups' list at index {item_idx}: {type(item)}. "
                    'Expected an AiiDA Group object or a string (label/UUID).'
                )
                raise ValueError(msg)
        return processed_groups if processed_groups else None

    @field_validator('user', mode='before')
    def _validate_user_input(cls, value: Any) -> orm.User | None:  # noqa: N805
        """Load User object from email string."""
        if value is None or isinstance(value, orm.User):
            return value
        if isinstance(value, str):
            return orm.User.collection.get(email=value)
        msg = f'Invalid input type for user: {type(value)}. Expected email string or User object.'
        raise ValueError(msg)

    @model_validator(mode='after')
    def _check_date_filters(self) -> 'DumpConfig':
        """Ensure past_days is not used with start_date or end_date."""
        if self.past_days is not None and (self.start_date is not None or self.end_date is not None):
            msg = 'Cannot use `past_days` filter together with `start_date` or `end_date`.'
            raise ValueError(msg)
        return self

    @model_validator(mode='before')
    @classmethod
    def _map_click_options_to_internal(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Map incoming Click-option-like keys to internal representation."""
        # Handle Dump Mode
        if values.pop('dry_run', False):
            values['dump_mode'] = DumpMode.DRY_RUN
        elif values.pop('overwrite', False):
            values['dump_mode'] = DumpMode.OVERWRITE

        return values

# --- IMPORTANT: Finalize Pydantic Model ---
# Call model_rebuild() after the class definition to resolve forward references
# and build the final schema needed for validation/serialization.
DumpConfig.model_rebuild(force=True)
