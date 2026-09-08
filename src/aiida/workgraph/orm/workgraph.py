"""Module with `Node` sub class for work processes."""

from typing import Optional, Tuple
import logging
from aiida.common.lang import classproperty

from aiida.orm.nodes.process.workflow.workchain import WorkChainNode

__all__ = ('WorkGraphNode',)


def make_dict_property(attribute_key: str, default=None):
    """
    Return a property object that gets/sets a dict attribute from `self.base.attributes`.

    :param attribute_key: the key in `self.base.attributes` for this dict
    :param default: default value to return if nothing is set
    """

    def getter(self):
        return self.base.attributes.get(attribute_key, default)

    def setter(self, value):
        self.base.attributes.set(attribute_key, value)

    return property(getter, setter)


def get_item_from_dict(base, attribute_key: str, item_key: str, default=None):
    """
    Get one value from a dict attribute (by item_key).
    """
    dct = base.attributes.get(attribute_key, {})
    return dct.get(item_key, default)


def set_item_in_dict(base, attribute_key: str, item_key: str, value):
    """
    Set one value in a dict attribute (by item_key).
    """
    dct = base.attributes.get(attribute_key, {})
    dct[item_key] = value
    base.attributes.set(attribute_key, dct)


class WorkGraphNode(WorkChainNode):
    """ORM class for all nodes representing the execution of a WorkGraph."""

    TASK_STATES_KEY = 'task_states'
    TASK_PROCESSES_KEY = 'task_processes'
    TASK_ACTIONS_KEY = 'task_actions'
    TASK_EXECUTORS_KEY = 'task_executors'
    TASK_ERROR_HANDLERS_KEY = 'task_error_handlers'
    TASK_EXECUTION_COUNTS_KEY = 'task_execution_counts'
    TASK_MAP_INFO_KEY = 'task_map_info'
    TASK_INPUTS_KEY = 'task_inputs'
    WORKGRAPH_DATA_KEY = 'workgraph_data'
    WORKGRAPH_DATA_SHORT_KEY = 'workgraph_data_short'
    WORKGRAPH_ERROR_HANDLERS_KEY = 'workgraph_error_handlers'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the same logger as WorkChainNode, this ensures the log level is set correctly
        self._logger = logging.getLogger('aiida.orm.nodes.process.workflow.workchain.WorkChainNode')

    @classproperty
    def _updatable_attributes(cls) -> Tuple[str, ...]:  # type: ignore
        # pylint: disable=no-self-argument
        return super()._updatable_attributes + (
            cls.WORKGRAPH_DATA_KEY,
            cls.TASK_INPUTS_KEY,
            cls.WORKGRAPH_DATA_SHORT_KEY,
            cls.WORKGRAPH_ERROR_HANDLERS_KEY,
            cls.TASK_STATES_KEY,
            cls.TASK_PROCESSES_KEY,
            cls.TASK_ACTIONS_KEY,
            cls.TASK_EXECUTORS_KEY,
            cls.TASK_ERROR_HANDLERS_KEY,
            cls.TASK_EXECUTION_COUNTS_KEY,
            cls.TASK_MAP_INFO_KEY,
        )

    task_states = make_dict_property(TASK_STATES_KEY, default={})
    task_processes = make_dict_property(TASK_PROCESSES_KEY, default={})
    task_actions = make_dict_property(TASK_ACTIONS_KEY, default={})
    task_executors = make_dict_property(TASK_EXECUTORS_KEY, default={})
    task_error_handlers = make_dict_property(TASK_ERROR_HANDLERS_KEY, default={})
    task_execution_counts = make_dict_property(TASK_EXECUTION_COUNTS_KEY, default={})
    task_map_info = make_dict_property(TASK_MAP_INFO_KEY, default={})
    workgraph_data = make_dict_property(WORKGRAPH_DATA_KEY, default=None)
    task_inputs = make_dict_property(TASK_INPUTS_KEY, default=None)
    workgraph_data_short = make_dict_property(WORKGRAPH_DATA_SHORT_KEY, default=None)
    workgraph_error_handlers = make_dict_property(WORKGRAPH_ERROR_HANDLERS_KEY, default=None)

    def get_task_state(self, task_name: str) -> Optional[str]:
        """Return the state of a single task."""
        return get_item_from_dict(self.base, self.TASK_STATES_KEY, task_name, default='')

    def set_task_state(self, task_name: str, task_state: str) -> None:
        """Set the state of a single task."""
        set_item_in_dict(self.base, self.TASK_STATES_KEY, task_name, task_state)

    def get_task_process(self, task_name: str) -> Optional[str]:
        """Return the process info of a single task."""
        return get_item_from_dict(self.base, self.TASK_PROCESSES_KEY, task_name, default=None)

    def set_task_process(self, task_name: str, task_process: str) -> None:
        """Set the process info of a single task."""
        set_item_in_dict(self.base, self.TASK_PROCESSES_KEY, task_name, task_process)

    def get_task_action(self, task_name: str) -> Optional[str]:
        """Return the action info of a single task."""
        return get_item_from_dict(self.base, self.TASK_ACTIONS_KEY, task_name, default='')

    def set_task_action(self, task_name: str, task_action: str) -> None:
        """Set the action info of a single task."""
        set_item_in_dict(self.base, self.TASK_ACTIONS_KEY, task_name, task_action)

    def get_task_execution_count(self, task_name: str) -> int:
        """Return the execution count of a single task."""
        return get_item_from_dict(self.base, self.TASK_EXECUTION_COUNTS_KEY, task_name, default=0)

    def set_task_execution_count(self, task_name: str, count: int) -> None:
        """Set the execution count of a single task."""
        set_item_in_dict(self.base, self.TASK_EXECUTION_COUNTS_KEY, task_name, count)

    def get_task_map_info(self, task_name: str) -> Optional[str]:
        """Return the map info of a single task."""
        return get_item_from_dict(self.base, self.TASK_MAP_INFO_KEY, task_name, default='')

    def set_task_map_info(self, task_name: str, task_map_info: str) -> None:
        """Set the map info of a single task."""
        set_item_in_dict(self.base, self.TASK_MAP_INFO_KEY, task_name, task_map_info)
