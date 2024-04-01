"""Module with utilities."""

from collections.abc import Mapping

from aiida.orm import Node


def prune_mapping(value):
    """Prune a nested mapping from all mappings that are completely empty.

    .. note:: A nested mapping that is completely empty means it contains at most other empty mappings. Other null
        values, such as `None` or empty lists, should not be pruned.

    :param value: A nested mapping of port values.
    :return: The same mapping but without any nested namespace that is completely empty.
    """
    if isinstance(value, Mapping) and not isinstance(value, Node):  # type: ignore[unreachable]
        result = {}
        for key, sub_value in value.items():
            pruned = prune_mapping(sub_value)
            # If `pruned` is an "empty'ish" mapping and not an instance of `Node`, skip it, otherwise keep it.
            if not (
                isinstance(pruned, Mapping) and not pruned and not isinstance(pruned, Node)  # type: ignore[unreachable]
            ):
                result[key] = pruned
        return result

    return value
