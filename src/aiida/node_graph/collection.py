from __future__ import annotations
from typing import TYPE_CHECKING, List, Union, Optional, Callable, Dict
import difflib
from importlib.metadata import entry_points, EntryPoint
import sys
import logging

if TYPE_CHECKING:
    from aiida.node_graph.task import Task
    from aiida.node_graph.socket import BaseSocket

logger = logging.getLogger(__name__)


def get_entries(entry_point_name: str) -> Dict[str, EntryPoint]:
    """Get entries from the entry point."""
    pool: Dict[str, EntryPoint] = {}
    eps = entry_points()
    if sys.version_info >= (3, 10):
        group = eps.select(group=entry_point_name)
    else:
        group = eps.get(entry_point_name, [])
    for entry_point in group:
        if entry_point.name.upper() not in pool:
            pool[entry_point.name.upper()] = entry_point
        else:
            raise Exception("Entry: {} is already registered.".format(entry_point.name))
    return pool


def get_item_class(
    identifier: EntryPoint | Task,
    pool: Dict[str, EntryPoint],
) -> Task:
    """Get the item class from the identifier."""

    if isinstance(identifier, str):
        if identifier.lower() not in pool:
            items = difflib.get_close_matches(identifier.lower(), pool._keys())
            if len(items) == 0:
                msg = f"Identifier: {identifier} is not defined."
            else:
                msg = f"Identifier: {identifier} is not defined. Did you mean {', '.join(item.lower() for item in items)}?"
            raise ValueError(msg)
        identifier = pool[identifier.lower()].load()
    # to support different versions of entry points
    elif identifier.__class__.__name__ == "EntryPoint":
        identifier = identifier.load()
    return identifier


class Collection:
    """Collection of instances of a property.
    Like an extended list, with the functions: new, find, delete, clear.
    """

    def __init__(
        self,
        parent: Optional[object] = None,
        graph: Optional[object] = None,
        pool: Optional[object] = None,
        entry_point: Optional[str] = None,
        post_creation_hooks: Optional[List[Callable]] = None,
        post_deletion_hooks: Optional[List[Callable]] = None,
    ) -> None:
        """Init a collection instance

        Args:
            parent (object, optional): object this collection belongs to.
        """
        self._items: Dict[str, object] = {}
        self.parent = parent
        self.graph = graph
        # one can specify the pool or entry_point to get the pool
        # if pool is not None, entry_point will be ignored, e.g., Link has no pool
        if pool is not None:
            self.pool = pool
        elif entry_point is not None:
            self.pool = get_entries(entry_point_name=entry_point)
        self.post_creation_hooks = post_creation_hooks or []
        self.post_deletion_hooks = post_deletion_hooks or []

    def __iter__(self) -> object:
        # Iterate over items in insertion order
        return iter(self._items.values())

    def __getitem__(self, index: Union[int, str]) -> object:
        if isinstance(index, int):
            # If indexing by int, convert dict keys to a list and index it
            return self._items[list(self._items.keys())[index]]
        elif isinstance(index, str):
            return self._items[index]

    def __getattr__(self, name: str) -> object:
        """Get item by name

        Args:
            name (str): _description_

        Returns:
            object: _description_
        """
        if name in self._items:
            return self._items[name]
        raise AttributeError(
            f""""{name}" is not in the {self.__class__.__name__}.
Acceptable names are {self._get_keys()}. This collection belongs to {self.parent}."""
        )

    def __dir__(self):
        return sorted(set(self._get_keys()))

    def __contains__(self, name: str) -> bool:
        """Check if an item with the given name exists in the collection.

        Args:
            name (str): The name of the item to check.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        return name in self._items

    def _generate_item_name(self, item_class=None, identifier: str = None) -> str:
        """Generate a new name for the item based on the given name and
        the number of items in the collection.
        """
        if item_class is not None:
            name = item_class._default_spec.identifier.split(".")[-1]
        elif identifier is not None:
            name = identifier.split(".")[-1]
        else:
            name = f"item_{len(self._items) + 1}"
        if name not in self._items:
            return name
        index = 1
        new_name = f"{name}{index}"
        while new_name in self._items:
            index += 1
            new_name = f"{name}{index}"
        return new_name

    def _new(self) -> object:
        """Add new item into this collection."""
        raise NotImplementedError("new method is not implemented.")

    def _append(self, item: object) -> None:
        """Append item into this collection."""
        if item.name in self._items:
            raise Exception(f"{item.name} already exists, please choose another name.")
        self._items[item.name] = item

    def _extend(self, items: List[object]) -> None:
        new_names = set([item.name for item in items])
        conflict_names = set(self._get_keys()).intersection(new_names)
        if len(conflict_names) > 0:
            raise Exception(
                f"{conflict_names} already exist, please choose another names."
            )
        for item in items:
            self._append(item)

    def _get(self, name: str) -> object:
        """Find item by name

        Args:
            name (str): _description_

        Returns:
            object: _description_
        """
        if name in self._items:
            return self._items[name]
        raise AttributeError(
            f""""{name}" is not in the {self.__class__.__name__}.
Acceptable names are {self._get_keys()}. This collection belongs to {self._parent}."""
        )

    def _get_by_uuid(self, uuid: str) -> Optional[object]:
        """Find item by uuid

        Args:
            uuid (str): _description_

        Returns:
            object: _description_
        """
        for item in self._items.values():
            if item.uuid == uuid:
                return item
        return None

    def _get_keys(self) -> List[str]:
        return list(self._items.keys())

    def _clear(self) -> None:
        """Remove all items from this collection."""
        self._items = {}

    def __delitem__(self, index: Union[int, List[int], str]) -> None:
        # If index is int, convert _items to a list and remove by index
        if isinstance(index, str):
            self._items.pop(index)
        elif isinstance(index, int):
            key = list(self._items.keys())[index]
            self._items.pop(key)
        elif isinstance(index, list):
            keys = list(self._items.keys())
            for i in sorted(index, reverse=True):
                key = keys[i]
                self._items.pop(key)
        else:
            raise ValueError(
                f"Invalid index type for __delitem__: {index}, expected int or str, or list of int."
            )

    def _pop(self, index: Union[int, str]) -> object:
        if isinstance(index, int):
            key = list(self._items.keys())[index]
            return self._items.pop(key)
        return self._items.pop(index)

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        s = ""
        s += "Collection()\n"
        return s

    def _copy(self, parent: Optional[object] = None) -> object:
        coll = self.__class__(parent=parent)
        coll._items = {key: item.copy() for key, item in self._items.items()}
        return coll

    def _execute_post_creation_hooks(self, item: object) -> None:
        """Execute all functions in post_creation_hooks with the given item."""
        for func in self.post_creation_hooks:
            func(self, item)

    def _execute_post_deletion_hooks(self, item: object) -> None:
        """Execute all functions in post_deletion_hooks with the given item."""
        for func in self.post_deletion_hooks:
            func(self, item)


class DependencyCollection:
    """
    A collection that can be used to create dependencies between multiple nodes/sockets.

    This does not inherit from `Collection`, as it is a simple wrapper around items
    strictly for creating/chaining dependencies.
    """

    def __init__(self, *items: Task | BaseSocket) -> None:
        self.items = list(items)

    def __rshift__(
        self,
        other: Task | BaseSocket | "DependencyCollection",
    ) -> Task | BaseSocket | "DependencyCollection":
        for item in self.items:
            item >> other
        return other

    def __lshift__(
        self,
        other: Task | BaseSocket | "DependencyCollection",
    ) -> Task | BaseSocket | "DependencyCollection":
        for item in self.items:
            item << other
        return other


def group(*items):
    """Create a dependency collection of items (nodes/sockets)."""
    return DependencyCollection(*items)


def decorator_check_identifier_name(func: Callable) -> Callable:
    """Check identifier and name exist or not.

    Args:
        func (_type_): _description_
    """

    def wrapper_func(*args, **kwargs):
        from aiida.node_graph.utils import valid_name_string

        identifier = args[1]
        if isinstance(identifier, str) and identifier.lower() not in args[0].pool:
            items = difflib.get_close_matches(identifier.lower(), args[0].pool._keys())
            if len(items) == 0:
                msg = f"Identifier: {identifier} is not defined."
            else:
                msg = f"Identifier: {identifier} is not defined. Did you mean {', '.join(item.lower() for item in items)}?"
            raise ValueError(msg)
        name = None
        if len(args) > 2:
            name = args[2]
        if kwargs.get("name", None):
            name = kwargs.get("name")
        if name is not None:
            valid_name_string(name)
            if name in args[0]._get_keys():
                raise ValueError(f"{name} already exists, please choose another name.")
        item = func(*args, **kwargs)
        return item

    return wrapper_func


class TaskCollection(Collection):
    """Task collection"""

    def __init__(
        self,
        graph: Optional[object] = None,
        pool: Optional[object] = None,
        entry_point: Optional[str] = "node_graph.task",
        post_creation_hooks: Optional[List[Callable]] = None,
    ) -> None:
        super().__init__(
            parent=graph,
            graph=graph,
            pool=pool,
            entry_point=entry_point,
            post_creation_hooks=post_creation_hooks,
        )

    @decorator_check_identifier_name
    def _new(
        self,
        identifier: Union[str, type],
        name: Optional[str] = None,
        uuid: Optional[str] = None,
        _metadata: Optional[dict] = None,
        **kwargs,
    ) -> Task:
        from aiida.node_graph.task import Task
        from aiida.node_graph.task_spec import TaskSpec, BaseHandle

        if isinstance(identifier, Task):
            task = identifier
            task.name = self._generate_item_name(identifier=name)
        elif isinstance(identifier, TaskSpec):
            name = name or self._generate_item_name(identifier=identifier.identifier)
            task = identifier.to_task(name=name, graph=self.graph)
        elif isinstance(identifier, BaseHandle):
            name = name or self._generate_item_name(identifier=identifier.identifier)
            task = identifier._spec.to_task(name=name, graph=self.graph)
        else:
            ItemClass = get_item_class(identifier, self.pool)
            if isinstance(ItemClass, BaseHandle):
                name = name or self._generate_item_name(identifier=ItemClass.identifier)
                task = ItemClass._spec.to_task(name=name, graph=self.graph)
            else:
                name = name or self._generate_item_name(ItemClass)
                task = ItemClass(
                    name=name,
                    uuid=uuid,
                    graph=self.graph,
                    metadata=_metadata,
                )
        self._append(task)
        task.set_inputs(kwargs)
        logger.debug(f"Created new task '{task.name}' with identifier={identifier}.")
        # Execute post creation hooks
        self._execute_post_creation_hooks(task)
        return task

    def _append(self, item: object) -> None:
        """Append item into this collection."""
        super()._append(item)
        if item.graph is not None and item.graph is not self.graph:
            raise Exception(f"This item is already part of a graph: {item.graph}")
        item.graph = self.graph

    def _copy(self, graph: Optional[object] = None) -> object:
        coll = self.__class__(graph=graph)
        for key, item in self._items.items():
            coll._append(item.copy(graph=graph))
        return coll

    def __repr__(self) -> str:
        s = ""
        parent_name = self.parent.name if self.parent else ""
        s += f'TaskCollection(parent = "{parent_name}", tasks = ['
        s += ", ".join([f'"{x}"' for x in self._get_keys()])
        s += "])"
        return s


class PropertyCollection(Collection):
    """Property colleciton"""

    def __init__(
        self,
        parent: Optional[object] = None,
        pool: Optional[object] = None,
        entry_point: Optional[str] = "node_graph.property",
    ) -> None:
        super().__init__(parent, pool=pool, entry_point=entry_point)

    @decorator_check_identifier_name
    def _new(
        self, identifier: Union[str, type], name: Optional[str] = None, **kwargs
    ) -> object:

        ItemClass = get_item_class(identifier, self.pool)
        item = ItemClass(name, **kwargs)
        self._append(item)
        return item

    def __repr__(self) -> str:
        s = ""
        task_name = self.parent.name if self.parent else ""
        s += f'PropertyCollection(task = "{task_name}", properties = ['
        s += ", ".join([f'"{x}"' for x in self._get_keys()])
        s += "])"
        return s


class LinkCollection(Collection):
    """Link colleciton"""

    def __init__(self, graph: object) -> None:
        super().__init__(graph=graph, parent=graph)

    def _new(self, input: object, output: object, type: int = 1) -> object:
        from aiida.node_graph.link import TaskLink

        item = TaskLink(input, output)
        self._append(item)
        # Execute post creation hooks
        self._execute_post_creation_hooks(item)
        return item

    def __delitem__(self, index: Union[int, List[int], str]) -> None:
        # If index is int, convert _items to a list and remove by index
        if isinstance(index, str):
            self._items[index].unmount()
            self._items.pop(index)
        elif isinstance(index, int):
            key = list(self._items.keys())[index]
            self._items[key].unmount()
            self._items.pop(key)
        elif isinstance(index, list):
            keys = list(self._items.keys())
            for i in sorted(index, reverse=True):
                key = keys[i]
                self._items[key].unmount()
                self._items.pop(key)
        else:
            raise ValueError(
                f"Invalid index type for __delitem__: {index}, expected int or str, or list of int."
            )

    def clear(self) -> None:
        """Remove all links from this collection.
        And remove the link in the nodes.
        """
        for item in self._items.values():
            item.unmount()
        self._items = {}

    def __repr__(self) -> str:
        s = ""
        s += "LinkCollection({} links)\n".format(len(self))
        return s
