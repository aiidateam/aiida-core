###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic helpers used by the WorkGraph runtime.

These are the node-graph-free, plugin-free utilities the engine relies on: dotted-key access into nested
dictionaries, and resolving AiiDA ``NodeLinksManager`` structures into plain dictionaries.
"""

from __future__ import annotations

from typing import Any

from aiida.orm.utils.managers import NodeLinksManager

__all__ = (
    'get_nested_dict',
    'resolve_node_link_managers',
    'update_nested_dict',
    'update_nested_dict_with_special_keys',
)


def get_nested_dict(d: Any, name: str, **kwargs: Any) -> Any:
    """Get the value from a nested dictionary.

    ``d`` is deliberately ``Any``: the traversal descends through both plain dicts and AiiDA
    ``NodeLinksManager`` containers, whose values are heterogeneous.

    If default is provided, return the default value if the key is not found.
    Otherwise, raise ValueError.
    For example:
    d = {"base": {"pw": {"parameters": 2}}}
    name = "base.pw.parameters"
    """
    keys = name.split('.')
    current = d
    for key in keys:
        if key not in current:
            if 'default' in kwargs:
                return kwargs.get('default')
            if isinstance(current, dict):
                avaiable_keys = list(current.keys())
            elif isinstance(current, NodeLinksManager):
                avaiable_keys = list(current._get_keys())
            else:
                avaiable_keys = []
            raise ValueError(f'{name} not exist. Available keys: {avaiable_keys}')
        current = current[key]
    return current


def merge_dicts(dict1: Any, dict2: Any) -> Any:
    """Recursively merges two dictionaries."""
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            dict1[key] = merge_dicts(dict1[key], value)
        else:
            # Overwrite or add the key
            dict1[key] = value
    return dict1


def update_nested_dict(base: dict[str, Any] | None, key_path: str, value: Any) -> dict[str, Any]:
    """
    Update or create a nested dictionary structure based on a dotted key path.

    This function allows updating a nested dictionary or creating one if `d` is `None`.
    Given a dictionary and a key path (e.g., "base.pw.parameters"), it will traverse
    or create the necessary nested structure to set the provided value at the specified
    key location. If intermediate dictionaries do not exist, they will be created.
    If the resulting dictionary is empty, it is set to `None`.

    Args:
        base (Dict[str, Any] | None): The dictionary to update, which can be `None`.
                                   If `None`, an empty dictionary will be created.
        key (str): A dotted key path string representing the nested structure.
        value (Any): The value to set at the specified key.

    Example:
        base = None
        key = "scf.pw.parameters"
        value = 2
        After running:
            update_nested_dict(d, key, value)
        The result will be:
            base = {"scf": {"pw": {"parameters": 2}}}

    Edge Case:
        If the resulting dictionary is empty after the update, it will be set to `None`.

    """
    if base is None:
        base = {}
    keys = key_path.split('.')
    current_key = keys[0]
    if len(keys) == 1:
        # Base case: Merge dictionaries or set the value directly.
        if isinstance(base.get(current_key), dict) and isinstance(value, dict):
            base[current_key] = merge_dicts(base[current_key], value)
        else:
            base[current_key] = value
    else:
        # Recursive case: Ensure the key exists and is a dictionary, then recurse.
        if current_key not in base or not isinstance(base[current_key], dict):
            base[current_key] = {}
        base[current_key] = update_nested_dict(base[current_key], '.'.join(keys[1:]), value)

    return base


def update_nested_dict_with_special_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Update the nested dictionary with special keys like "base.pw.parameters"."""
    # Remove None
    data = {k: v for k, v in data.items() if v is not None}
    special_keys = [k for k in data.keys() if '.' in k]
    for key in special_keys:
        value = data.pop(key)
        update_nested_dict(data, key, value)
    return data


def resolve_node_link_managers(data: Any) -> Any:
    """Recursively resolve all NodeLinksManagers either in a dictionary or a NodeLinksManager."""
    if isinstance(data, dict):
        return {key: resolve_node_link_managers(value) for key, value in data.items()}
    if isinstance(data, NodeLinksManager):
        return convert_node_link_manager_to_dict(data)
    return data


def convert_node_link_manager_to_dict(node_link_manager: NodeLinksManager) -> dict[str, Any]:
    """Recursively convert a NodeLinksManager to a dictionary representation."""
    data = {}
    for name in node_link_manager._get_keys():
        item = node_link_manager._get_node_by_link_label(name)
        if isinstance(item, NodeLinksManager):
            data[name] = convert_node_link_manager_to_dict(item)
        else:
            data[name] = item
    return data
