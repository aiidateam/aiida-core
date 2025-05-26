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
from aiida.common.exceptions import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.orm import Code, Computer, User


class DumpMode(Enum):
    INCREMENTAL = auto()
    OVERWRITE = auto()
    DRY_RUN = auto()


class GroupDumpScope(Enum):
    IN_GROUP = auto()
    ANY = auto()
    NO_GROUP = auto()


logger = AIIDA_LOGGER.getChild('tools.dumping.config')


def _load_computer_validator(value: int | str | orm.Computer) -> orm.Computer | None:
    """Pydantic validator function to load Computer from identifier."""
    if value is None or isinstance(value, orm.Computer):
        return value
    if isinstance(value, (str, int)):
        try:
            return orm.load_computer(identifier=value)
        except NotExistent:
            logger.warning(f"Computer with identifier '{value}' not found in DB. Returning None for this item.")
            return None
    logger.warning(f'Invalid input type for computer validation: {type(value)}. Returning None.')
    return None


def _load_code_validator(value: int | str | orm.Code) -> orm.Code | None:
    """Pydantic validator function to load Code from identifier."""
    if value is None or isinstance(value, orm.Code):
        return value
    if isinstance(value, (str, int)):
        try:
            node = orm.load_node(identifier=value)
            if isinstance(node, orm.Code):
                return node
            else:
                msg = f"Node identifier '{value}' does not correspond to a Code. Returning None for this item."
                logger.warning(msg)
                return None
        except NotExistent:
            logger.warning(f"Code with identifier '{value}' not found in DB. Returning None for this item.")
            return None
    logger.warning(f'Invalid input type for code validation: {type(value)}. Returning None.')
    return None


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

    user: Optional[Union[User, str]] = Field(default=None, description='User object or email to filter by')

    computers: Optional[List[Union[Computer, str]]] = Field(
        default=None, description='List of Computer objects or UUIDs/labels to filter by'
    )

    codes: Optional[List[Union[Code, str]]] = Field(
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

    @computed_field  # type: ignore[misc]
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
            # According to the error, a list is expected.
            # If other types are possible at this stage from Click, adjust as needed.
            raise ValueError(f'Invalid input type for groups: {type(value)}. Expected a list.')

        processed_groups: List[str] = []
        for item_idx, item in enumerate(value):
            if isinstance(item, orm.Group):
                # Using group's label as the string representation.
                # Change to item.uuid if UUIDs are preferred.
                processed_groups.append(item.label)
            elif isinstance(item, str):
                processed_groups.append(item)
            else:
                msg = (
                    f"Invalid item type in 'groups' list at index {item_idx}: {type(item)}. "
                    'Expected an AiiDA Group object or a string (label/UUID).'
                )
                raise ValueError(msg)
        # Return None if list is empty to match Field(default=None) behavior if desired,
        # or always return the list (Pydantic will handle default if input is None).
        return processed_groups if processed_groups else None

    @field_validator('user', mode='before')
    def _validate_user(cls, value: Any) -> User | None:  # noqa: N805
        """Load User object from email string."""
        if value is None or isinstance(value, orm.User):
            return value
        if isinstance(value, str):
            try:
                return orm.User.collection.get(email=value)
            except NotExistent:
                logger.warning(f"User with email '{value}' not found in DB. Returning None.")
                return None
        # Raise error for completely invalid input types during validation
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

    # --- Serialization override ---
    @model_serializer(mode='wrap', when_used='json')
    def _serialize_to_click_options(self, handler):
        """Serialize to dict with Click-option-like keys."""
        # Exclude internal fields before handler runs if possible,
        # otherwise remove them after. `exclude=True` on Field helps here.
        data = handler(self)

        # Add Click keys based on internal fields
        # 1. Dump Mode -> flags
        # Access internal fields via self
        data['dry_run'] = self.dump_mode == DumpMode.DRY_RUN
        data['overwrite'] = self.dump_mode == DumpMode.OVERWRITE
        data.pop('dump_mode', None)

        # 2. Profile Scope -> all_entries flag
        data['all_entries'] = self.all_entries

        # 3. Filter fields -> option names & identifier serialization
        # No need to map 'groups' name
        filter_map_to_option = {
            'groups': 'groups',  # Keep mapping for iteration logic
            'user': 'user',
            'codes': 'codes',
            'computers': 'computers',
            'start_date': 'start_date',
            'end_date': 'end_date',
            'past_days': 'past_days',
        }
        orm_fields_map = {'user': 'email', 'computers': 'uuid', 'codes': 'uuid'}

        # Iterate through *potential* output keys, get value from self
        for field_name, option_name in filter_map_to_option.items():
            value = getattr(self, field_name, None)
            if value is not None:
                # Serialize value if needed (dates, ORM objects)
                if isinstance(value, datetime):
                    data[option_name] = value.isoformat()
                elif field_name in orm_fields_map:
                    orm_attr = orm_fields_map[field_name]
                    if isinstance(value, list):  # Handle list of ORM objects
                        serialized_list = [getattr(item, orm_attr, None) for item in value if hasattr(item, orm_attr)]
                        # Only include if list is not empty after serialization
                        if serialized_list:
                            data[option_name] = [item for item in serialized_list if item is not None]
                    elif hasattr(value, orm_attr):  # Handle single ORM object
                        data[option_name] = getattr(value, orm_attr)
                elif isinstance(value, list) and value:  # Handle non-empty basic lists (like groups)
                    data[option_name] = value
                elif not isinstance(value, list):  # Handle other non-list, non-None values
                    data[option_name] = value

            # Clean up empty lists potentially created if ORM serialization failed
            if option_name in data and isinstance(data[option_name], list) and not data[option_name]:
                data.pop(option_name)

        # Remove None values explicitly if they remain
        data = {k: v for k, v in data.items() if v is not None}

        return data


# --- IMPORTANT: Finalize Pydantic Model ---
# Call model_rebuild() after the class definition to resolve forward references
# and build the final schema needed for validation/serialization.
DumpConfig.model_rebuild(force=True)
