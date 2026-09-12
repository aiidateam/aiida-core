from __future__ import annotations
from dataclasses import dataclass, field
from importlib.metadata import entry_points, EntryPoint
from functools import lru_cache
from typing import Dict, Set, Tuple, Any


TypePromotionPair = Tuple[str, str]


@lru_cache(maxsize=None)
def _ep_group(group: str) -> tuple[EntryPoint, ...]:
    """Load an entry-point group once (cached)."""
    eps = entry_points()
    res = eps.select(group=group)
    # cache wants hashable; callers can iterate the tuple
    return tuple(res)


class Namespace:
    """A simple recursive namespace that allows attribute-based access to nested dictionaries, with tab completion."""

    def __init__(self, name: str = "Namespace"):
        self._name = name
        self._data = {}

    def __getattr__(self, name: str) -> EntryPoint:
        if name in super().__getattribute__("_data"):
            return super().__getattribute__("_data")[name]
        raise AttributeError(f"Namespace {self._name} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Namespace | EntryPoint) -> None:
        if name in ["_data", "_name"]:
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __dir__(self):
        """Enable tab completion by returning all available attributes."""
        return list(self._data.keys())

    def __repr__(self):
        return f"Namespace({self._data})"

    def __contains__(self, key: str) -> bool:
        """Allow checking if a key exists, including nested keys."""
        parts = key.split(".")
        current = self
        for part in parts:
            if part in current._data:
                current = current._data[part]
            else:
                return False
        return True

    def __iter__(self):
        """Allow iteration over stored items."""
        return iter(self._data.items())

    def __getitem__(self, key: str) -> EntryPoint | Namespace:
        """Allow dictionary-like access and support nested keys."""
        parts = key.split(".")
        current = self
        for part in parts:
            if part in current._data:
                current = current._data[part]
            else:
                raise KeyError(
                    f"Key {key!r} not found in Namespace {self._name}. "
                    f"Available keys are: {list(self._keys())}"
                )
        return current

    def __setitem__(self, key: str, value: EntryPoint | Namespace) -> None:
        """Allow dictionary-like setting and support nested keys."""
        parts = key.split(".")
        current = self
        for part in parts[:-1]:
            if part not in current._data:
                current._data[part] = Namespace(name=part)
            current = current._data[part]
        current._data[parts[-1]] = value

    def _keys(self, prefix="") -> list[str]:
        """Return all keys, including nested keys, using dot notation."""
        all_keys = []
        for key, value in self._data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            all_keys.append(full_key)
            if isinstance(value, Namespace):
                all_keys.extend(value._keys(prefix=full_key))
        return all_keys


class EntryPointPool:
    """
    Hierarchical namespace that loads entry points and supports tab completion.
    """

    def __init__(self, entry_point_group: str, name: str = "EntryPointPool") -> None:
        self._items = Namespace(name=name)
        self._is_loaded = False
        self._load_items(entry_point_group)

    def _load_items(self, entry_point_group: str) -> None:
        """Loads nodes into the internal hierarchical dictionary, if not already loaded."""
        if self._is_loaded:
            return
        for ep in _ep_group(entry_point_group):
            key_parts = ep.name.lower().split(".")
            current_level = self._items
            for part in key_parts[:-1]:
                if not hasattr(current_level, part):
                    setattr(current_level, part, Namespace(name=part))
                current_level = getattr(current_level, part)
            final_key = key_parts[-1]
            if hasattr(current_level, final_key):
                raise Exception(f"Duplicate entry point name detected: {ep.name!r}")
            setattr(current_level, final_key, ep)
        self._is_loaded = True

    def __getattr__(self, name: str) -> EntryPoint:
        """Allow direct access to nodes via instance attributes."""
        return getattr(super().__getattribute__("_items"), name)

    def __dir__(self):
        """Enable tab completion for the task pool instance."""
        return dir(self._items)

    def __repr__(self):
        return f"EntryPointPool({self._items})"

    def __contains__(self, key: str) -> bool:
        return key in self._items

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key: str) -> EntryPoint:
        return self._items[key]

    def __setitem__(self, key: str, value: EntryPoint | Namespace) -> None:
        self._items[key] = value

    def _keys(self) -> list[str]:
        return self._items._keys()


@dataclass
class RegistryHub:
    """Aggregates entry-point pools, a type-mapping, and identifier-level promotions."""

    task_pool: Any
    socket_pool: Any
    property_pool: Any
    type_mapping: Dict[Any, str]
    type_promotion: Set[TypePromotionPair] = field(
        default_factory=set
    )  # identifier-level

    def resolve(self, tp: type) -> str:
        return self.type_mapping.get(tp, self.type_mapping.get("default"))

    @classmethod
    def from_prefix(
        cls,
        task_group: str = "node_graph.task",
        socket_group: str = "node_graph.socket",
        property_group: str = "node_graph.property",
        type_mapping_group: str = "node_graph.type_mapping",
        type_promotion_group: str = "node_graph.type_promotion",
        identifier_prefix: str = "node_graph",
    ) -> "RegistryHub":
        task_pool = EntryPointPool(entry_point_group=task_group, name="TaskPool")
        task_pool["graph_level"] = task_pool[f"{identifier_prefix}.graph_level"]

        socket_pool = EntryPointPool(entry_point_group=socket_group, name="SocketPool")
        socket_pool["any"] = socket_pool[f"{identifier_prefix}.any"]
        socket_pool["namespace"] = socket_pool[f"{identifier_prefix}.namespace"]

        property_pool = EntryPointPool(
            entry_point_group=property_group, name="PropertyPool"
        )
        property_pool["any"] = property_pool[f"{identifier_prefix}.any"]

        # Merge type mappings from EP providers
        tm: dict = {}
        for ep in _ep_group(type_mapping_group):
            try:
                d = ep.load()
                if isinstance(d, dict):
                    tm.update(d)
            except Exception:
                pass
        tm.setdefault("default", f"{identifier_prefix}.any")
        tm.setdefault("namespace", f"{identifier_prefix}.namespace")

        # Identifier-level promotions (pairs of socket identifiers)
        tp: Set[TypePromotionPair] = set()
        for ep in _ep_group(type_promotion_group):
            try:
                seq = ep.load()  # iterable of (src_id, dst_id)
                for p in seq:
                    if isinstance(p, (list, tuple)) and len(p) == 2:
                        tp.add((str(p[0]).lower(), str(p[1]).lower()))
            except Exception:
                pass

        return cls(task_pool, socket_pool, property_pool, tm, tp)


registry_hub = RegistryHub.from_prefix()
