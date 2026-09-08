from typing import Optional, Callable, Dict, Any, Union, ClassVar, Iterable


class TaskProperty:
    """Base class for Task properties.

    A property holds data that can be displayed or modified in a GUI, with an optional update callback.
    """

    property_entry: str = "node_graph.property"
    identifier: str = "TaskProperty"
    allowed_types = (object,)  # Allow any type
    NOT_ADAPTED: ClassVar[object] = object()
    _validation_adapters: ClassVar[list[Callable[[Any], Any]]] = []

    @classmethod
    def register_validation_adapter(cls, adapter: Callable[[Any], Any]) -> None:
        """Register a validation adapter used when `allowed_types` checks fail.

        The adapter is called as `adapter(value)` and should return either:
        - `TaskProperty.NOT_ADAPTED` if it cannot adapt the value
        - an adapted value that can be validated against `allowed_types`
        """
        if adapter not in cls._validation_adapters:
            cls._validation_adapters.append(adapter)

    @classmethod
    def unregister_validation_adapter(cls, adapter: Callable[[Any], Any]) -> None:
        """Unregister a previously registered validation adapter."""
        try:
            cls._validation_adapters.remove(adapter)
        except ValueError:
            return

    def __init__(
        self,
        name: str,
        description: str = "",
        default: Any = None,
        update: Optional[Callable[[], None]] = None,
        arg_type: Optional[str] = "kwargs",
        value: Any = None,
        **kwargs,
    ) -> None:
        """
        Initialize a TaskProperty.

        Args:
            name (str): The name of the property.
            description (str, optional): A description of the property. Defaults to "".
            default (Any, optional): The default value of the property. Defaults to None.
            update (Callable[[], None], optional): Callback to invoke when the value changes. Defaults to None.
        """
        self.name = name
        self.description = description
        self.default = default
        self.update = update
        self.arg_type = arg_type
        self._value = default
        if value is not None:
            self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the property to a dictionary for database storage."""
        from aiida.node_graph.socket import TaggedValue

        data = {
            "value": self.value.__wrapped__
            if isinstance(self.value, TaggedValue)
            else self.value,
            "name": self.name,
            "identifier": self.identifier,
            "default": self.default,
            "metadata": self.get_metadata(),
            "arg_type": self.arg_type,
        }
        # Conditionally add serializer/deserializer if they are defined
        if hasattr(self, "get_serialize") and callable(self.get_serialize):
            data["serialize"] = self.get_serialize()

        if hasattr(self, "get_deserialize") and callable(self.get_deserialize):
            data["deserialize"] = self.get_deserialize()

        return data

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata related to this property."""
        return {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskProperty":
        """Create a TaskProperty from a serialized dictionary."""
        prop = cls(
            name=data["name"],
            description=data.get("description", ""),
            default=data.get("default"),
        )
        prop.identifier = data["identifier"]
        prop.value = data["value"]
        return prop

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update the property from a dictionary."""
        self.value = data["value"]

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self.set_value(value)

    def set_value(self, value: Any) -> None:
        """Set the value and invoke the update callback if present."""
        self.validate(value)
        self._value = value
        if self.update:
            self.update()

    def _iter_validation_candidates(self, value: Any) -> Iterable[Any]:
        yield value

        for adapter in type(self)._validation_adapters:
            try:
                adapted = adapter(value)
            except Exception:
                continue
            if adapted is self.NOT_ADAPTED:
                continue
            yield adapted

    def _select_validation_candidate(
        self, value: Any, allowed_types: Optional[tuple[type, ...]] = None
    ) -> Any:
        """Select the first candidate matching `allowed_types` (or `self.allowed_types`)."""
        allowed = self.allowed_types if allowed_types is None else allowed_types
        for candidate in self._iter_validation_candidates(value):
            if isinstance(candidate, allowed):
                return candidate
        return value

    def validate(self, value: Any) -> None:
        """Validate the given value based on allowed types."""
        for candidate in self._iter_validation_candidates(value):
            if isinstance(candidate, self.allowed_types):
                return

        raise TypeError(
            f"Invalid value for property '{self.name}': "
            f"expected {self.allowed_types}, but got {type(value).__name__} "
            f"(value={value!r})."
        )

    def copy(self) -> "TaskProperty":
        """Create a shallow copy of the property."""
        return self.__class__(
            name=self.name,
            description=self.description,
            default=self._value,
            update=self.update,
        )

    @classmethod
    def new(
        cls,
        identifier: Union[str, type],
        name: str = None,
        PropertyPool: Dict[str, "TaskProperty"] = None,
        **kwargs,
    ) -> "TaskProperty":
        """Create a new property from an identifier."""
        from aiida.node_graph.collection import get_item_class

        if PropertyPool is None:
            from aiida.node_graph.properties import PropertyPool

        ItemClass = get_item_class(identifier, PropertyPool)
        return ItemClass(name=name, **kwargs)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}", value={self._value})'

    def __repr__(self) -> str:
        return self.__str__()
