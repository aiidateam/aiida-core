from aiida.orm.utils.serialize import (
    _NODE_TAG,
    _COMPUTER_TAG,
    _NODE_LINKS_MANAGER_TAG,
    _GROUP_TAG,
    node_constructor,
    computer_constructor,
    group_constructor,
    node_links_manager_constructor,
)
from typing import Any
import yaml


class AiiDASafeLoader(yaml.SafeLoader):
    """
    A “safe” AiiDA-specific YAML loader.

    Since we are extending SafeLoader, we need to carefully add only those
    constructors we consider safe. Anything we omit will raise an error if
    encountered in the YAML.
    """

    pass


AiiDASafeLoader.add_constructor(_NODE_TAG, node_constructor)
AiiDASafeLoader.add_constructor(_COMPUTER_TAG, computer_constructor)
AiiDASafeLoader.add_constructor(_NODE_LINKS_MANAGER_TAG, node_links_manager_constructor)
AiiDASafeLoader.add_constructor(_GROUP_TAG, group_constructor)


def deserialize_safe(serialized: str) -> Any:
    return yaml.load(serialized, Loader=AiiDASafeLoader)
