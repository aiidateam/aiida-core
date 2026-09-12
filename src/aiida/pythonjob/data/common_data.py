import datetime

from aiida import orm
from aiida.orm import Data


class NoneData(orm.Data):
    """
    A Data node that explicitly represents a Python `None`.

    - Has no repository content and (by default) no attributes.
    - All instances have identical content hash, which is desirable here:
      "None" is a single value.
    """

    # Convenience aliases to mirror simple-* nodes (Int, Bool, etc.)
    @property
    def value(self):
        return None

    @property
    def obj(self):
        return None

    def __repr__(self) -> str:
        return "NoneData()"

    def __str__(self) -> str:
        return "NoneData()"


class DateTimeData(Data):
    """AiiDA node to store a datetime.datetime object."""

    def __init__(self, value: datetime.datetime, **kwargs):
        if not isinstance(value, datetime.datetime):
            raise TypeError(f"Expected datetime.datetime, got {type(value)}")
        super().__init__(**kwargs)
        # Store as ISO string for portability
        self.base.attributes.set("datetime", value.isoformat())

    @property
    def value(self) -> datetime.datetime:
        """Return the stored datetime as a datetime object."""
        return datetime.datetime.fromisoformat(self.base.attributes.get("datetime"))

    def __str__(self):
        return str(self.value)


class FunctionData(Data):
    """AiiDA node to store a Python function path."""

    def __init__(self, value, **kwargs):
        module = getattr(value, "__module__", None)
        qualname = getattr(value, "__qualname__", None) or getattr(value, "__name__", None)
        if not module or not qualname:
            raise TypeError(f"Expected a function-like object, got {type(value)}")
        super().__init__(**kwargs)
        self.base.attributes.set("module_path", module)
        self.base.attributes.set("qualname", qualname)

    @property
    def module_path(self) -> str:
        return self.base.attributes.get("module_path")

    @property
    def qualname(self) -> str:
        return self.base.attributes.get("qualname")

    @property
    def path(self) -> str:
        return f"{self.module_path}:{self.qualname}"

    @property
    def value(self):
        from importlib import import_module

        try:
            module = import_module(self.module_path)
        except Exception as exc:
            raise ImportError(
                f"Failed to import function module '{self.module_path}' for FunctionData '{self.path}': {exc}"
            ) from exc

        obj = module
        try:
            for part in self.qualname.split("."):
                obj = getattr(obj, part)
        except AttributeError as exc:
            raise ImportError(f"Failed to resolve function '{self.path}': attribute '{part}' not found.") from exc

        return obj

    def __str__(self) -> str:
        return self.path
