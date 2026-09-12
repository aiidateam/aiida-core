from aiida.node_graph.property import TaskProperty
from typing import Any


class PropertyAny(TaskProperty):
    """A new class for Any type."""

    identifier: str = "node_graph.any"
    allowed_types = (object,)  # Allow any type


class PropertyInt(TaskProperty):
    """A new class for integer type."""

    identifier: str = "node_graph.int"
    allowed_types = (int, type(None))


class PropertyFloat(TaskProperty):
    """A new class for float type."""

    identifier: str = "node_graph.float"
    allowed_types = (int, float, type(None))


class PropertyBool(TaskProperty):
    """A new class for bool type."""

    identifier: str = "node_graph.bool"
    allowed_types = (bool, int, type(None))


class PropertyString(TaskProperty):
    """A new class for string type."""

    identifier: str = "node_graph.string"
    allowed_types = (str, type(None))


class PropertyEnum(TaskProperty):
    """A new class for enumeration type.

    Each option has:

    - identifier: identifier of the this option.
    - content: The true content of the this option.
    - description: Used for documentation and tooltips.

    >>> from node_graph.properties.built_in import PropertyEnum
    >>> enum = PropertyEnum("node_graph.enum",
                    options=[["add", "test_add", "add function"],
                            "sqrt", "test_sqrt", "sqrt function"],
                            "power", "test_power", "power function"]],
                    update=callback
                )
    >>> enum = "sqrt"
    >>> asset enum.value == "test_sqrt"
    """

    identifier: str = "node_graph.enum"

    def __init__(
        self, name, options=[], description="", default=None, update=None
    ) -> None:
        self._options = options
        # set the default value
        if default is None and None not in options:
            default = options[0][0]
        super().__init__(name, description, default, update)

    @property
    def keys(self):
        return [item[0] for item in self._options]

    @property
    def content(self):
        return self._options[self.keys.index(self._value)][1]

    @property
    def item_description(self):
        return self._options[self.keys.index(self._value)][2]

    def set_value(self, value):
        if value in self.keys:
            self._value = value
            # run the callback function
            if self.update is not None:
                self.update()
        else:
            raise Exception(f"{value} is not in the option list: {self.keys}.")

    def copy(self):
        p = self.__class__(
            self.name, self._options, self.description, self.value, self.update
        )
        p.value = self.value
        return p

    def get_metadata(self):
        metadata = {"default": self.default, "options": self._options}
        return metadata


# ====================================
# Vector
class PropertyVector(TaskProperty):
    """node_graph Vector property"""

    identifier: str = "node_graph.vector"
    allowed_types = (list, tuple, type(None))
    allowed_item_types = (object, type(None))

    def __init__(self, name, description="", size=3, default=None, update=None) -> None:
        self.size = size
        default = [] if default is None else default
        super().__init__(name, description, default, update)

    def validate(self, value: Any) -> None:
        """Validate the given value based on allowed types."""
        seq = self._select_validation_candidate(value)
        if seq is not None:
            if len(seq) != self.size:
                raise ValueError(
                    f"Invalid size: Expected {self.size}, got {len(seq)} instead."
                )
            for v in seq:
                self.validate_item(v)

        return super().validate(value)

    def validate_item(self, value: Any) -> None:
        """Validate the given value based on allowed types."""
        for candidate in self._iter_validation_candidates(value):
            if isinstance(candidate, self.allowed_item_types):
                return
        raise TypeError(
            f"Expected value of type {self.allowed_item_types}, got {type(value).__name__} instead."
        )

    def set_value(self, value: Any) -> None:
        self.validate(value)
        self._value = value
        if self.update:
            self.update()

    def copy(self):
        p = self.__class__(
            self.name, self.description, self.size, self.value, self.update
        )
        p.value = self.value
        return p

    def get_metadata(self):
        metadata = {"default": self.default, "size": self.size}
        return metadata


class PropertyIntVector(PropertyVector):
    """A new class for integer vector type."""

    identifier: str = "node_graph.int_vector"
    allowed_item_types = (int, type(None))

    def __init__(self, name, description="", size=3, default=None, update=None) -> None:
        default = [0] * size if default is None else default
        super().__init__(name, description, size, default, update)


class PropertyFloatVector(PropertyVector):
    """A new class for float vector type."""

    identifier: str = "node_graph.float_vector"
    allowed_item_types = (int, float, type(None))

    def __init__(self, name, description="", size=3, default=None, update=None) -> None:
        default = [0.0] * size if default is None else default
        super().__init__(name, description, size, default, update)


class PropertyBoolVector(PropertyVector):
    """A new class for bool vector type."""

    identifier: str = "node_graph.bool_vector"
    allowed_item_types = (int, bool, type(None))

    def __init__(self, name, description="", size=3, default=None, update=None) -> None:
        default = [False] * size if default is None else default
        super().__init__(name, description, size, default, update)


# =======================================
# matrix
class MatrixProperty(TaskProperty):
    """node_graph Matrix property"""

    identifier: str = "node_graph.matrix"
    allowed_item_types = (int, float, type(None))

    def __init__(
        self, name, description="", size=[3, 3], default=None, update=None
    ) -> None:
        self.size = size
        self._value = [] if default is None else default
        super().__init__(name, description, default, update)

    def validate(self, value: Any) -> None:
        """Validate the given value based on allowed types."""
        length = self.size[0] * self.size[1]
        seq = self._select_validation_candidate(value)
        if seq is not None:
            if not (len(seq) == length):
                raise ValueError(
                    f"Invalid size: Expected {length}, got {len(seq)} instead."
                )
            for v in seq:
                self.validate_item(v)

        return super().validate(value)

    def validate_item(self, value: Any) -> None:
        """Validate the given value based on allowed types."""
        for candidate in self._iter_validation_candidates(value):
            if isinstance(candidate, self.allowed_item_types):
                return
        raise TypeError(
            f"Expected value of type {self.allowed_item_types}, got {type(value).__name__} instead."
        )

    def copy(self):
        p = self.__class__(
            self.name, self.description, self.size, self.value, self.update
        )
        p.value = self.value
        return p


class PropertyFloatMatrix(MatrixProperty):
    """A new class for float matrix type."""

    identifier: str = "node_graph.float_matrix"

    def __init__(
        self,
        name,
        description="",
        size=[3, 3],
        default=None,
        update=None,
    ) -> None:
        default = [0.0] * size[0] * size[1] if default is None else default
        super().__init__(name, description, size, default, update)


# =======================================
# dict, tuple, list with base type
def validate_base_type(value):
    if isinstance(value, dict):
        for _, subvalue in value.items():
            validate_base_type(subvalue)
    elif isinstance(value, (list, tuple)):
        for x in value:
            validate_base_type(x)
    else:
        if not isinstance(value, (int, float, str, bool)):
            raise Exception(
                "{} is not a base type (int, flot, str, bool).".format(value)
            )


class PropertyBaseDict(TaskProperty):
    """node_graph BaseDict property.
    All the elements should be a base type (int, float, string, bool).
    """

    identifier: str = "node_graph.base_dict"

    def __init__(self, name, description="", default={}, update=None) -> None:
        default = {} if default is None else default
        super().__init__(name, description, default, update)

    def set_value(self, value):
        if isinstance(value, dict):
            validate_base_type(value)
            self._value = value
            # run the callback function
            if self.update is not None:
                self.update()
        else:
            raise Exception("{} is not a dict.".format(value))


class PropertyBaseList(TaskProperty):
    """node_graph BaseList property.
    All the elements should be a base type (int, float, string, bool).
    """

    identifier: str = "BaseList"

    def __init__(self, name, description="", default=None, update=None) -> None:
        default = [] if default is None else default
        super().__init__(name, description, default, update)

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            validate_base_type(value)
            self._value = value
            # run the callback function
            if self.update is not None:
                self.update()
        else:
            raise Exception(
                f"Set property {self.name} failed. {value} is not a list or tuple."
            )
