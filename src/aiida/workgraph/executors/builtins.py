import logging
from typing import Any
from aiida import orm

LOGGER = logging.getLogger(__name__)


def UnavailableExecutor(*args, **kwargs):
    raise RuntimeError('This executor was defined dynamically and is not available from the database snapshot.')


def get_context(context: dict, key: str) -> Any:
    """Get the context value."""
    key = key.value if isinstance(key, orm.Str) else key
    results = {'result': context._task_results['graph_ctx'].get(key)}
    return results


def update_ctx(context: dict, key: str, value: Any) -> None:
    """Set the context value."""
    key = key.value if isinstance(key, orm.Str) else key
    context._task_results['graph_ctx'][key] = value


def select(condition, true=None, false=None):
    """Select the data based on the condition."""
    if condition:
        return true
    return false


def get_item(data: dict, key: str) -> Any:
    """Get an item from a dictionary."""
    return data.get(key, None)


def return_input(**kwargs: Any) -> dict:
    """Return the input"""
    return kwargs


def load_node(pk: int = None, uuid: str = None) -> orm.Node:
    """Load an AiiDA node by its primary key or UUID."""
    if uuid is not None:
        pk = uuid.value if isinstance(uuid, orm.Str) else uuid
    else:
        pk = pk.value if isinstance(pk, orm.Int) else pk
    return orm.load_node(pk)


def load_code(pk: int = None, uuid: str = None, label: str = None) -> orm.Code:
    """Load an AiiDA code by its primary key or UUID."""
    if uuid is not None:
        pk = uuid.value if isinstance(uuid, orm.Str) else uuid
    elif label is not None:
        pk = label.value if isinstance(label, orm.Str) else label
    else:
        pk = pk.value if isinstance(pk, orm.Int) else pk
    LOGGER.info('Loading code with pk: %s', pk)
    return orm.load_code(pk)
