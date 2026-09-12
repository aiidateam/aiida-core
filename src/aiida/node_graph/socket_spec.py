from __future__ import annotations
from dataclasses import dataclass, field, replace, MISSING
from typing import (
    Any,
    Dict,
    Optional,
    Union,
    Iterable,
    Tuple,
    Type,
)
import inspect
from copy import deepcopy
from aiida.node_graph.orm.mapping import type_mapping as DEFAULT_TM
from aiida.node_graph.socket_meta import CallRole, SocketMeta, merge_meta
from aiida.node_graph.utils.struct_utils import structured_type_info
from .socket import TaskSocketNamespace
import ast
import textwrap
import types
from dataclasses import (
    is_dataclass as _is_dc,
    fields as _dc_fields,
    MISSING as _DC_MISSING,
)

from typing import Annotated, get_args, get_origin, get_type_hints

try:
    from typing import Unpack
except ImportError:  # pragma: no cover - Python < 3.11
    from typing_extensions import Unpack
from typing import is_typeddict as _is_typeddict

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

# Cache UnionType if available (3.10+), else None
_UNION_TYPE = getattr(types, "UnionType", None)
NoneType = getattr(types, "NoneType", type(None))

__all__ = [
    # Core datatypes / API
    "SocketMeta",
    "SocketSpecSelect",
    "SocketSpec",
    "SocketView",
    "SocketSpecAPI",
    # Helpers
    "socket",
    "namespace",
    "dynamic",
    "validate_socket_data",
    "infer_specs_from_callable",
    "set_default",
    "unset_default",
    "merge_specs",
    "add_spec_field",
    "remove_spec_field",
    # Pydantic helpers
    "Leaf",
    "from_model",
]


def _is_union_origin(origin: Any) -> bool:
    """True if origin represents a Union across versions (typing.Union or X|Y)."""
    return (origin is Union) or (_UNION_TYPE is not None and origin is _UNION_TYPE)


def _is_annotated_type(tp: Any) -> bool:
    """True if tp is an Annotated[...] wrapper across versions."""
    return get_origin(tp) is Annotated


def _find_first_annotated(tp: Any) -> Optional[Any]:
    """
    Return the first Annotated[...] wrapper found in tp, searching inside Union/Optional.
    (recurse into other generics is not supported.)
    """
    if _is_annotated_type(tp):
        return tp
    origin = get_origin(tp)
    if _is_union_origin(origin):
        for arg in get_args(tp):
            found = _find_first_annotated(arg)
            if found is not None:
                return found
    return None


def _annotated_parts(annot: Any) -> tuple[Any, tuple[Any, ...]]:
    """Given an Annotated wrapper, return (base_type, metadata_tuple)."""
    args = get_args(annot)
    base = args[0] if args else annot
    meta = getattr(annot, "__metadata__", None)
    if meta is None:
        meta = tuple(args[1:]) if len(args) > 1 else ()
    return base, tuple(meta)


def _strip_optional(tp: Any) -> Any:
    """If tp is Optional[T] (or Union[T, None]), return T; else return tp."""
    origin = get_origin(tp)
    if not _is_union_origin(origin):
        return tp
    args = [arg for arg in get_args(tp) if arg is not NoneType]
    if len(args) == 1:
        return args[0]
    return tp


def _unwrap_annotated(tp: Any) -> tuple[Any, Optional["SocketMeta"]]:
    """Return (base_type, SocketMeta|None) for Annotated types (incl. inside Optional/Union)."""
    annot = _find_first_annotated(tp)
    if annot is None:
        return tp, None
    base, metas = _annotated_parts(annot)
    spec_meta = next((m for m in metas if isinstance(m, SocketMeta)), None)
    return base, spec_meta


def _extract_spec_from_annotated(tp: Any) -> Optional["SocketSpec"]:
    """
    Return a SocketSpec from Annotated metadata (preferring SocketView.to_spec()).
    Works when Annotated is nested in Optional/Union.
    """
    annot = _find_first_annotated(tp)
    if annot is None:
        return None
    _, metas = _annotated_parts(annot)
    for m in metas:
        if isinstance(m, SocketView):
            return m.to_spec()
    for m in metas:
        if isinstance(m, SocketSpec):
            return m
    # Pydantic BaseModel subclass or dataclass in metadata
    for m in metas:
        if isinstance(m, type) and _is_struct_model_type(m):
            return SocketSpecAPI.from_model(m)
    return None


@dataclass(frozen=True)
class SocketSpecSelect:
    """
    Selection/transform directives used *only* inside Annotated metadata.

    - include/exclude support dotted paths ("a.b.c"). When `include` is provided,
      unspecified fields are dropped; `exclude` removes the specified fields.
    - include_prefix/exclude_prefix match *top-level* field names only.
    - rename maps top-level child names.
    - prefix prepends a string to all top-level child names.
    """

    include: Optional[Union[str, Iterable[str]]] = None
    exclude: Optional[Union[str, Iterable[str]]] = None
    include_prefix: Optional[Union[str, Iterable[str]]] = None
    exclude_prefix: Optional[Union[str, Iterable[str]]] = None
    rename: Optional[Dict[str, str]] = None
    prefix: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, "include", _normalize_names(self.include))
        object.__setattr__(self, "exclude", _normalize_names(self.exclude))
        object.__setattr__(
            self, "include_prefix", _normalize_names(self.include_prefix)
        )
        object.__setattr__(
            self, "exclude_prefix", _normalize_names(self.exclude_prefix)
        )


def _normalize_names(
    x: Optional[Union[str, Iterable[str]]]
) -> Optional[Tuple[str, ...]]:
    if x is None:
        return None
    if isinstance(x, str):
        return (x,)
    return tuple(x)


def _paths_to_tree(names: Iterable[str]) -> Dict[str, Optional[dict]]:
    """
    Convert ["a", "b.c", "b.d.e"] -> {"a": None, "b": {"c": None, "d": {"e": None}}}
    None means "take/remove this entire field".
    If a parent key is already marked None (whole subtree), deeper paths under it are ignored.
    """
    root: Dict[str, Optional[dict]] = {}
    for raw in names or []:
        parts = [p for p in str(raw).split(".") if p]
        if not parts:
            continue
        task: Dict[str, Optional[dict]] = root
        for i, seg in enumerate(parts):
            last = i == len(parts) - 1
            if last:
                # Mark whole field at this level
                task[seg] = None
            else:
                if seg not in task:
                    task[seg] = {}
                else:
                    # If already selecting whole subtree, deeper spec is irrelevant
                    if task[seg] is None:
                        # parent marked as whole selection/removal: stop descending
                        break
                    # if it exists but isn't a dict (shouldn't happen), coerce to dict
                    if not isinstance(task[seg], dict):
                        task[seg] = {}
                # descend
                task = task[seg]
    return root


def _spec_include(spec: "SocketSpec", tree: Dict[str, Optional[dict]]) -> "SocketSpec":
    if not spec.is_namespace():
        return spec
    keep: Dict[str, SocketSpec] = {}
    for k, subtree in tree.items():
        if k not in spec.fields:
            continue
        child = spec.fields[k]
        keep[k] = (
            child
            if subtree is None
            else (_spec_include(child, subtree) if child.is_namespace() else child)
        )
    return replace(spec, fields=keep)


def _spec_exclude(spec: "SocketSpec", tree: Dict[str, Optional[dict]]) -> "SocketSpec":
    if not spec.is_namespace():
        return spec
    new_fields = dict(spec.fields)
    for k, subtree in tree.items():
        if k not in new_fields:
            continue
        if subtree is None:
            new_fields.pop(k, None)
        else:
            child = new_fields[k]
            if child.is_namespace():
                new_fields[k] = _spec_exclude(child, subtree)
    return replace(spec, fields=new_fields)


def _spec_rename(spec: "SocketSpec", mapping: Dict[str, str]) -> "SocketSpec":
    if not spec.is_namespace():
        raise TypeError("rename requires a namespace SocketSpec")
    out: Dict[str, SocketSpec] = {}
    for old, child in spec.fields.items():
        new = mapping.get(old, old)
        if new in out:
            raise ValueError(f"rename collision: '{new}'")
        out[new] = child
    return replace(spec, fields=out)


def _spec_prefix(spec: "SocketSpec", pfx: str) -> "SocketSpec":
    if not spec.is_namespace():
        raise TypeError("prefix requires a namespace SocketSpec")
    return replace(spec, fields={f"{pfx}{k}": v for k, v in spec.fields.items()})


def _expand_prefix_names(
    spec: "SocketSpec", pfxs: Optional[Iterable[str]]
) -> list[str]:
    if not pfxs or not spec.is_namespace():
        return []
    pfxs = list(pfxs)
    return [k for k in spec.fields.keys() if any(k.startswith(p) for p in pfxs)]


def _apply_select_from_annotation(annot_like: Any, spec: "SocketSpec") -> "SocketSpec":
    """Collect & apply all SocketSpecSelect objects found in Annotated metadata."""
    annot = _find_first_annotated(annot_like)
    if annot is None:
        return spec
    _, metas = _annotated_parts(annot)

    s = spec
    for m in metas:
        if not isinstance(m, SocketSpecSelect):
            continue
        inc = list(m.include or [])
        exc = list(m.exclude or [])
        inc += _expand_prefix_names(s, m.include_prefix)
        exc += _expand_prefix_names(s, m.exclude_prefix)
        if inc:
            s = _spec_include(s, _paths_to_tree(inc))
        if exc:
            s = _spec_exclude(s, _paths_to_tree(exc))
        if m.rename:
            s = _spec_rename(s, m.rename)
        if m.prefix:
            s = _spec_prefix(s, m.prefix)
    return s


def _merge_all_meta_from_annotation(
    annot_like: Any, base: "SocketMeta"
) -> "SocketMeta":
    """Overlay every SocketMeta present in Annotated metadata (order-respecting)."""
    annot = _find_first_annotated(annot_like)
    if annot is None:
        return base
    _, metas = _annotated_parts(annot)
    out = base
    for m in metas:
        if isinstance(m, SocketMeta):
            out = merge_meta(out, m)
    return out


@dataclass(frozen=True)
class SocketSpec:
    """
    Immutable socket schema tree (leaf or namespace).

    - identifier: leaf type identifier or "node_graph.namespace"
    - item: schema for each dynamic key (leaf or namespace)
    - fields: fixed fields for namespace (name -> schema)
    - default: leaf-only default value
    - meta: optional metadata (help/required/is_metadata/call_role/...)
    """

    identifier: str
    item: Optional["SocketSpec"] = None
    default: Any = field(default_factory=lambda: MISSING)
    link_limit: Optional[int] = None
    fields: Dict[str, "SocketSpec"] = field(default_factory=dict)
    meta: SocketMeta = field(default_factory=SocketMeta)

    @property
    def dynamic(self) -> bool:
        return bool(self.meta.dynamic)

    # structural predicates
    def is_namespace(self) -> bool:
        return self.identifier.endswith("namespace")

    def has_default(self) -> bool:
        # only check against MISSING, and only for leaves
        return not isinstance(self.default, type(MISSING)) and (not self.is_namespace())

    def to_dict(self) -> Dict[str, Any]:
        meta_payload = self.meta.to_dict()
        dynamic = bool(meta_payload.pop("dynamic", self.dynamic))
        d: Dict[str, Any] = {"identifier": self.identifier, "dynamic": dynamic}
        if self.item is not None:
            d["item"] = self.item.to_dict()
        if self.fields:
            d["fields"] = {k: v.to_dict() for k, v in self.fields.items()}
        # default only for leaves and only if not MISSING
        if not self.is_namespace() and not isinstance(self.default, type(MISSING)):
            d["default"] = deepcopy(self.default)
        if meta_payload:
            d["meta"] = meta_payload
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SocketSpec":
        meta = SocketMeta.from_dict(d.get("meta", {}))
        if "dynamic" in d and not meta.dynamic:
            meta = SocketMeta(
                help=meta.help,
                required=meta.required,
                call_role=meta.call_role,
                is_metadata=meta.is_metadata,
                dynamic=bool(d.get("dynamic", False)),
                child_default_link_limit=meta.child_default_link_limit,
                socket_type=meta.socket_type,
                arg_type=meta.arg_type,
                extras=meta.extras,
            )
        item = cls.from_dict(d["item"]) if "item" in d else None
        fields = {k: cls.from_dict(v) for k, v in d.get("fields", {}).items()}
        default = d.get("default", MISSING)
        return cls(
            identifier=d["identifier"],
            item=item,
            link_limit=d.get("link_limit", None),
            fields=fields,
            default=default,
            meta=meta,
        )


class SocketView:
    """A lightweight, pure view over a SocketSpec for attribute traversal. No mutators."""

    __slots__ = ("_spec",)

    def __init__(self, spec: SocketSpec) -> None:
        object.__setattr__(self, "_spec", spec)

    def to_spec(self) -> SocketSpec:
        return object.__getattribute__(self, "_spec")

    def __getattr__(self, name: str) -> "SocketView":
        spec: SocketSpec = object.__getattribute__(self, "_spec")
        if name == "item":
            if spec.dynamic and spec.item is not None:
                return SocketView(spec.item)
            raise AttributeError("'.item' only valid on dynamic namespace specs")
        if spec.fields and name in spec.fields:
            return SocketView(spec.fields[name])
        raise AttributeError(f"'{name}' not found in namespace spec")

    def __getitem__(self, name: str) -> "SocketView":
        return self.__getattr__(name)


# ---------- Pydantic helpers ----------
class LeafMeta(type):
    pass


class Leaf(metaclass=LeafMeta):
    """Marker generic: Leaf[MyModel] forces a Pydantic model to be treated as a leaf blob."""

    def __class_getitem__(cls, item):
        return Annotated[item, "__leaf_marker__"]


def _is_pydantic_model_type(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, BaseModel)


def _is_dataclass_type(tp: Any) -> bool:
    return isinstance(tp, type) and _is_dc(tp)


def _is_typeddict_type(tp: Any) -> bool:
    try:
        return _is_typeddict(tp)
    except TypeError:
        return False


def _unpack_typeddict_type(ann: Any) -> Optional[type]:
    base, _ = _unwrap_annotated(ann)
    origin = get_origin(base)
    if origin is Unpack:
        args = get_args(base)
        if len(args) == 1 and _is_typeddict_type(args[0]):
            return args[0]
    return None


def _is_struct_model_type(tp: Any) -> bool:
    # “Structured models” are Pydantic models, dataclasses, or TypedDicts
    return (
        _is_pydantic_model_type(tp) or _is_dataclass_type(tp) or _is_typeddict_type(tp)
    )


def _struct_cfg(model_cls: type[Any]) -> dict:
    return getattr(model_cls, "model_config", {}) or {}


def _struct_is_dynamic(model_cls: type[Any]) -> bool:
    return _struct_cfg(model_cls).get("extra", None) == "allow"


def _struct_is_leaf(model_or_ann: Any) -> bool:
    """True if:
    - annotation is Leaf[SomePydModel]   (our explicit per-use leaf marker), or
    - model class has model_config['leaf'] = True
    """
    # Leaf[...] marker on an annotation (we encode it via Annotated[..., '__leaf_marker__'])
    if _annot_is_leaf_marker(model_or_ann) is not None:
        return True

    # Direct Pydantic model class with config leaf = True
    if _is_struct_model_type(model_or_ann):
        return bool(_struct_cfg(model_or_ann).get("leaf", False))

    return False


def _struct_dynamic_item_type(model_cls: type[Any]) -> Any:
    cfg = _struct_cfg(model_cls)
    return cfg.get("item_type")


def _annot_is_leaf_marker(ann_like: Any) -> Optional[Any]:
    """Detect our Leaf[...] synthetic marker which we encoded via Annotated[..., '__leaf_marker__']."""
    annot = _find_first_annotated(ann_like)
    if annot is None:
        return None
    base, metas = _annotated_parts(annot)
    for m in metas:
        if m == "__leaf_marker__":
            return base
    return None


def _normalize_explicit_spec(explicit: Any) -> SocketSpec:
    """Accept SocketSpec | SocketView | BaseModel subclass and return a SocketSpec."""
    if isinstance(explicit, SocketView):
        return explicit.to_spec()
    if isinstance(explicit, SocketSpec):
        return explicit
    if isinstance(explicit, type) and _is_struct_model_type(explicit):
        return SocketSpecAPI.from_model(explicit)
    raise TypeError(
        "Unsupported explicit spec. Use SocketSpec, SocketView, Pydantic BaseModel subclass, dataclass, or TypedDict."
    )


class SocketSpecAPI:
    MAP: Dict[Any, str] = DEFAULT_TM
    NAMESPACE: str = "node_graph.namespace"
    DEFAULT: str = "node_graph.any"
    ANNOTATED: str = "node_graph.annotated"

    # convenience re-exports
    SocketSpec = SocketSpec
    SocketMeta = SocketMeta
    SocketSpecSelect = SocketSpecSelect
    SocketView = SocketView
    SocketNamespace = TaskSocketNamespace

    DEFAULT_OUTPUT_KEY: str = "result"  # downstream override allowed

    @classmethod
    def resolve_type(cls, py_type: Any) -> str:
        tm = cls.MAP
        if py_type in tm:
            return tm[py_type]
        origin = get_origin(py_type)
        if origin in (list, tuple, set):
            return tm.get(list, cls.DEFAULT)
        return cls.DEFAULT

    @classmethod
    def resolve_type_name(cls, name: str) -> str:
        return cls.MAP.get(name, cls.DEFAULT)

    @classmethod
    def _ns_identifier(cls) -> str:
        return cls.NAMESPACE

    @classmethod
    def _map_identifier(cls, tp: Any) -> str:
        return cls.resolve_type(tp)

    @staticmethod
    def _py_type_name(tp: Any) -> str:
        module = getattr(tp, "__module__", None)
        qualname = getattr(tp, "__qualname__", None) or getattr(tp, "__name__", None)
        if module and qualname:
            return f"{module}.{qualname}"
        return repr(tp)

    @classmethod
    def socket(cls, T: Any, **meta) -> Any:
        """Wrap a type with optional metadata (help/required/extras/etc.)."""
        return Annotated[T, SocketMeta(**meta)]

    @classmethod
    def namespace(cls, _name: Optional[str] = None, /, **fields) -> SocketSpec:
        spec = SocketSpec(identifier=cls.NAMESPACE)
        new_fields: Dict[str, SocketSpec] = {}

        for name, val in fields.items():
            has_default = isinstance(val, tuple) and len(val) == 2
            T, default_val = val if has_default else (val, MISSING)

            annotated_spec = _extract_spec_from_annotated(T)
            if annotated_spec is not None:
                child = annotated_spec
            else:
                base_T, _ = _unwrap_annotated(T)
                base_T = _strip_optional(base_T)
                # Pydantic model
                leaf_override = _annot_is_leaf_marker(T)
                if leaf_override is not None and _is_struct_model_type(leaf_override):
                    child = cls._leaf_from_type(leaf_override)
                elif _is_struct_model_type(base_T):
                    child = cls.from_model(base_T)
                elif isinstance(base_T, SocketSpec):
                    child = base_T
                elif isinstance(base_T, SocketView):
                    child = base_T.to_spec()
                else:
                    child = cls._leaf_from_type(base_T)

            # overlay all meta from Annotated
            child = replace(child, meta=_merge_all_meta_from_annotation(T, child.meta))
            # selection transforms
            child = _apply_select_from_annotation(T, child)

            # scalar default only on leaves
            if has_default:
                if child.is_namespace():
                    raise TypeError(
                        f"Default provided for namespace field '{name}'. "
                        "Provide a structured default via function signature mapping instead."
                    )
                child = replace(child, default=default_val)

            new_fields[name] = child

        return replace(spec, fields=new_fields)

    @classmethod
    def dynamic(cls, item_type: Any = None, /, **fixed) -> SocketSpec:
        base = cls.namespace(**fixed)
        base = replace(base, meta=replace(base.meta, dynamic=True))

        if item_type is None:
            return base

        T, spec_meta = _unwrap_annotated(item_type)
        T = _strip_optional(T)
        # Pydantic model
        leaf_override = _annot_is_leaf_marker(item_type)
        if leaf_override is not None and _is_struct_model_type(leaf_override):
            item_spec = cls._leaf_from_type(leaf_override)
        elif _is_struct_model_type(T):
            item_spec = cls.from_model(T)
        else:
            if isinstance(T, SocketSpec):
                item_spec = T
            else:
                item_spec = cls._leaf_from_type(T)
                if spec_meta is not None:
                    item_spec = replace(
                        item_spec, meta=merge_meta(item_spec.meta, spec_meta)
                    )

        return replace(base, item=item_spec)

    @classmethod
    def validate_socket_data(
        cls, data: SocketSpec | SocketView | list | Type[BaseModel] | None
    ) -> SocketSpec | None:
        """Validate socket data and convert it to a dictionary."""
        if data is None or isinstance(data, SocketSpec):
            return data
        elif isinstance(data, SocketView):
            return data.to_spec()
        elif isinstance(data, list):
            if not all(isinstance(d, str) for d in data):
                raise TypeError("All elements in the list must be strings")
            return cls.namespace(**{d: Any for d in data})
        elif isinstance(data, type) and _is_struct_model_type(data):
            return cls.from_model(data)
        else:
            raise TypeError(
                f"Unsupported spec input type: {type(data).__name__}."
                " Expected list of str, BaseModel subclass, SocketSpec, SocketView or None"
            )

    @classmethod
    def from_model(cls, model_cls: Type[Any]) -> SocketSpec:
        """
        Expand a structured type (Pydantic BaseModel subclass, dataclass, or TypedDict)
        into a namespace spec.

        Honors `model_config` for both kinds:
        - extra='allow'  -> dynamic namespace
        - item_type      -> dynamic item type (default Any)
        - leaf=True      -> force leaf blob (dict)
        """

        # Leaf override (config or Leaf[...] handled earlier)
        if _struct_is_leaf(model_cls):
            leaf_target = _annot_is_leaf_marker(model_cls)
            return cls._leaf_from_type(leaf_target or model_cls)

        # Build fields + defaults via a unified path
        if _is_pydantic_model_type(model_cls):
            # ---------- Pydantic ----------
            if _struct_is_dynamic(model_cls):
                ns = SocketSpec(
                    identifier=cls._ns_identifier(),
                    fields={},
                    meta=SocketMeta(dynamic=True),
                )
                for name, model_field in model_cls.model_fields.items():  # type: ignore[attr-defined]
                    child = cls._child_spec_from_type(model_field.annotation or Any)
                    if (
                        getattr(model_field, "default", PydanticUndefined)
                        is not PydanticUndefined
                        and not child.is_namespace()
                    ):
                        child = replace(child, default=getattr(model_field, "default"))
                    ns.fields[name] = child
                item_t = _struct_dynamic_item_type(model_cls)
                ns = replace(
                    ns, item=cls._child_spec_from_type(item_t) if item_t else None
                )
                return ns

            # regular Pydantic (non-dynamic)
            ns = SocketSpec(identifier=cls._ns_identifier(), fields={})
            for name, model_field in model_cls.model_fields.items():  # type: ignore[attr-defined]
                child = cls._child_spec_from_type(model_field.annotation or Any)
                if (
                    getattr(model_field, "default", PydanticUndefined)
                    is not PydanticUndefined
                    and not child.is_namespace()
                ):
                    child = replace(child, default=getattr(model_field, "default"))
                ns.fields[name] = child
            return ns

        elif _is_dataclass_type(model_cls):
            # ---------- Dataclass ----------
            # Resolve type hints once (supports Annotated and forward refs similar to Pydantic)
            hints = get_type_hints(model_cls, include_extras=True)

            if _struct_is_dynamic(model_cls):
                ns = SocketSpec(
                    identifier=cls._ns_identifier(),
                    fields={},
                    meta=SocketMeta(dynamic=True),
                )
                for f in _dc_fields(model_cls):
                    ann = hints.get(f.name, f.type)
                    child = cls._child_spec_from_type(ann)

                    # Apply scalar defaults (ignore default_factory to avoid unintended calls)
                    if f.default is not _DC_MISSING and not child.is_namespace():
                        child = replace(child, default=f.default)

                    ns.fields[f.name] = child

                item_t = _struct_dynamic_item_type(model_cls)
                ns = replace(
                    ns, item=cls._child_spec_from_type(item_t) if item_t else None
                )
                return ns

            # regular dataclass (non-dynamic)
            ns = SocketSpec(identifier=cls._ns_identifier(), fields={})
            for f in _dc_fields(model_cls):
                ann = hints.get(f.name, f.type)
                child = cls._child_spec_from_type(ann)
                if f.default is not _DC_MISSING and not child.is_namespace():
                    child = replace(child, default=f.default)
                ns.fields[f.name] = child
            return ns

        elif _is_typeddict_type(model_cls):
            # ---------- TypedDict ----------
            hints = get_type_hints(model_cls, include_extras=True)
            required_keys = getattr(model_cls, "__required_keys__", None)
            if required_keys is None:
                total = getattr(model_cls, "__total__", True)
                required_keys = set(hints.keys()) if total else set()
            else:
                required_keys = set(required_keys)

            ns = SocketSpec(identifier=cls._ns_identifier(), fields={})
            for name, ann in hints.items():
                child = cls._child_spec_from_type(ann)
                child = replace(
                    child, meta=replace(child.meta, required=name in required_keys)
                )
                ns.fields[name] = child
            return ns

        else:
            raise TypeError(
                "from_model expects a Pydantic BaseModel subclass, dataclass, or TypedDict."
            )

    @classmethod
    def _leaf_from_type(cls, T: Any) -> SocketSpec:
        if T is Any or T is inspect._empty or T is object:
            return SocketSpec(identifier=cls.DEFAULT, meta=SocketMeta())

        if _is_typeddict_type(T):
            return cls._leaf_from_type(dict)

        origin = get_origin(T)
        if _is_union_origin(origin):
            args = []
            for arg in get_args(T):
                if arg is NoneType:
                    continue
                if _is_union_origin(get_origin(arg)):
                    args.extend(get_args(arg))
                else:
                    args.append(arg)
            if not args:
                return SocketSpec(identifier=cls.DEFAULT, meta=SocketMeta())
            if len(args) == 1:
                return cls._leaf_from_type(args[0])

            entries: list[dict[str, Any]] = []
            seen: set[tuple[str, Optional[str]]] = set()
            for arg in args:
                member = cls._leaf_from_type(arg)
                entry: dict[str, Any] = {"identifier": member.identifier}
                if member.identifier == cls.ANNOTATED:
                    py = member.meta.extras.get("py_type")
                    if py:
                        entry["py_type"] = py
                key = (entry["identifier"].lower(), entry.get("py_type"))
                if key in seen:
                    continue
                seen.add(key)
                entries.append(entry)
            meta = SocketMeta(
                extras={"py_type": cls._py_type_name(T), "union": entries}
            )
            return SocketSpec(identifier=cls.ANNOTATED, meta=meta)
        if origin in (list, tuple, set):
            T = list
        elif origin in (dict,):
            T = dict

        identifier = cls._map_identifier(T)
        if identifier != cls.DEFAULT:
            return SocketSpec(identifier=identifier, meta=SocketMeta())

        if T in (list, dict, tuple, set):
            return SocketSpec(identifier=cls.DEFAULT, meta=SocketMeta())

        meta = SocketMeta(extras={"py_type": cls._py_type_name(T)})
        return SocketSpec(identifier=cls.ANNOTATED, meta=meta)

    @classmethod
    def _child_spec_from_type(cls, ann: Any) -> SocketSpec:
        # Leaf[...] override
        leaf_target = _annot_is_leaf_marker(ann)
        if leaf_target is not None:
            return cls._leaf_from_type(leaf_target)

        base_T, _ = _unwrap_annotated(ann)
        base_T = _strip_optional(base_T)

        # embedded SocketSpec/SocketView
        if isinstance(base_T, SocketSpec):
            return base_T
        if isinstance(base_T, SocketView):
            return base_T.to_spec()

        # Pydantic model types
        if _is_struct_model_type(base_T):
            return cls.from_model(base_T)

        # sequences -> map to list identifier (leaf)
        origin = get_origin(base_T)
        if origin in (list, tuple, set):
            return cls._leaf_from_type(list)

        # dict/Mapping -> leaf dict (no implicit dynamic unless user chose pydantic dynamic)
        if origin in (dict,):
            return cls._leaf_from_type(dict)

        # primitives / anything else -> leaf
        return cls._leaf_from_type(base_T)

    @staticmethod
    def _safe_type_hints(func):
        return get_type_hints(func, include_extras=True)

    @classmethod
    def _apply_structured_defaults_to_leaves(
        cls, ns_spec: SocketSpec, dv: dict[str, Any]
    ) -> SocketSpec:
        """Recursively apply dict defaults by setting defaults on leaf specs only."""
        if not ns_spec.is_namespace():
            return ns_spec
        new_fields: dict[str, SocketSpec] = {}
        for k, child in (ns_spec.fields or {}).items():
            if k not in dv:
                new_fields[k] = child
                continue
            val = dv[k]
            if isinstance(val, dict) and child.is_namespace():
                new_fields[k] = cls._apply_structured_defaults_to_leaves(child, val)
            else:
                if child.is_namespace():
                    raise TypeError(
                        f"Default for '{k}' is scalar, but the field is a namespace."
                    )
                new_fields[k] = replace(child, default=val)
        return replace(ns_spec, fields=new_fields)

    @classmethod
    def _spec_from_annotation(cls, T: Any) -> SocketSpec:
        """Only returns a leaf (or passes through explicit SocketSpec/.to_spec())."""
        # prefer explicit spec in Annotated
        if hasattr(T, "to_spec") and callable(getattr(T, "to_spec")):
            return T.to_spec()

        base_T, _meta_ignored = _unwrap_annotated(T)
        base_T = _strip_optional(base_T)
        # Already a SocketSpec
        if isinstance(base_T, SocketSpec):
            return base_T

        # Pydantic model?
        leaf_override = _annot_is_leaf_marker(T)
        if leaf_override is not None and _is_struct_model_type(leaf_override):
            return cls._leaf_from_type(leaf_override)
        if _is_struct_model_type(base_T):
            return cls.from_model(base_T)

        return cls._leaf_from_type(base_T)

    @classmethod
    def build_inputs_from_signature(
        cls, func, explicit: SocketSpec | SocketView | type[BaseModel] | None = None
    ) -> SocketSpec:
        """Always return a NAMESPACE spec (possibly empty).
        - POSITIONAL_ONLY -> call_role="args"
        - POSITIONAL_OR_KEYWORD / KEYWORD_ONLY -> call_role="kwargs"
        - *args -> dynamic namespace of item T, call_role="var_args"
        - **kwargs -> dynamic namespace of item T, call_role="var_kwargs"
        """
        if explicit is not None:
            spec = _normalize_explicit_spec(explicit)
            # Inputs must be a namespace — if user forces a leaf (e.g., leaf=True model), we disallow:
            if not spec.is_namespace():
                raise TypeError(
                    "Explicit inputs must be a namespace. "
                    "If you're passing a Pydantic model or dataclass, avoid `model_config={'leaf': True}` for inputs."
                )
            # ensure top-level call_role=kwargs
            return replace(spec, meta=replace(spec.meta, call_role=CallRole.KWARGS))

        sig = inspect.signature(func)
        ann_map = cls._safe_type_hints(func)

        fields: dict[str, SocketSpec] = {}
        is_dyn: bool = False

        for name, param in sig.parameters.items():
            T = ann_map.get(name, param.annotation)
            base_T, _ = _unwrap_annotated(T)
            base_T = _strip_optional(base_T)
            unpack_td = _unpack_typeddict_type(T)

            # Determine call_role
            if param.kind is inspect.Parameter.POSITIONAL_ONLY:
                call_role = CallRole.ARGS
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                call_role = CallRole.VAR_ARGS
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                call_role = CallRole.VAR_KWARGS
            else:
                call_role = CallRole.KWARGS

            # Determine required
            is_required = not (
                param.default is not inspect._empty
                or param.kind
                in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            )

            # Prefer spec from Annotated metadata if present
            annotated_spec = _extract_spec_from_annotated(T)
            if annotated_spec is not None:
                spec = annotated_spec
            else:
                # Pydantic-aware leaf override?
                leaf_override = _annot_is_leaf_marker(T)
                if leaf_override is not None and _is_struct_model_type(leaf_override):
                    spec = cls._leaf_from_type(leaf_override)
                # Pydantic model?
                elif _is_struct_model_type(base_T):
                    spec = cls.from_model(base_T)
                elif unpack_td is not None:
                    spec = cls.from_model(unpack_td)
                else:
                    spec = cls._spec_from_annotation(base_T)

            # Merge meta from annotation onto required/call_role defaults
            merged_meta = _merge_all_meta_from_annotation(
                T,
                SocketMeta(
                    required=is_required,
                    call_role=call_role,
                ),
            )
            spec = replace(spec, meta=merge_meta(spec.meta, merged_meta))

            # Unpack[TypedDict] on **kwargs -> expand into top-level kwargs
            if param.kind is inspect.Parameter.VAR_KEYWORD and unpack_td is not None:
                if not spec.is_namespace():
                    raise TypeError(
                        "Unpack[TypedDict] must resolve to a namespace spec."
                    )
                group_meta = _merge_all_meta_from_annotation(
                    T, SocketMeta(required=None, call_role=CallRole.KWARGS)
                )
                for child_name, child_spec in (spec.fields or {}).items():
                    if child_name in fields:
                        raise ValueError(
                            f"Unpack[TypedDict] field '{child_name}' conflicts with existing "
                            f"parameter '{child_name}'."
                        )
                    child_spec = replace(
                        child_spec, meta=merge_meta(child_spec.meta, group_meta)
                    )
                    fields[child_name] = child_spec
                continue

            # varargs/kwargs become dynamic namespaces
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                is_dyn = True
                item_T, _ = _unwrap_annotated(T)
                item_T = _strip_optional(item_T)
                item_spec = cls._spec_from_annotation(
                    item_T if item_T is not inspect._empty else Any
                )
                spec = SocketSpec(
                    identifier=cls._ns_identifier(),
                    item=item_spec,
                    meta=replace(spec.meta, dynamic=True),
                )
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                if unpack_td is None:
                    is_dyn = True
                    item_T, _ = _unwrap_annotated(T)
                    item_T = _strip_optional(item_T)
                    # try Mapping[str, T] -> T else Any
                    origin = get_origin(item_T)
                    if origin in (dict,):
                        args = get_args(item_T)
                        if args and len(args) == 2 and (args[0] in (str, Any)):
                            item_T = args[1]
                    else:
                        item_T = Any if item_T is inspect._empty else item_T
                    item_spec = cls._spec_from_annotation(item_T)
                    spec = SocketSpec(
                        identifier=cls._ns_identifier(),
                        item=item_spec,
                        meta=replace(spec.meta, dynamic=True),
                    )

            # Apply selection/transform directives from Annotated
            spec = _apply_select_from_annotation(T, spec)

            if (
                _is_struct_model_type(base_T)
                and _annot_is_leaf_marker(T) is None
                and not _struct_is_leaf(base_T)
            ):
                info = structured_type_info(base_T)
                if info is not None and "structured_type" not in spec.meta.extras:
                    spec = replace(
                        spec,
                        meta=merge_meta(
                            spec.meta, SocketMeta(extras={"structured_type": info})
                        ),
                    )

            # Defaults: scalar -> leaf default; dict -> traverse into leaves
            if param.default is not inspect._empty and param.default is not None:
                if isinstance(param.default, dict) and spec.is_namespace():
                    spec = cls._apply_structured_defaults_to_leaves(spec, param.default)
                else:
                    if spec.is_namespace():
                        raise TypeError(
                            f"Scalar default provided for namespace parameter '{name}'. "
                            "Use a structured mapping of defaults."
                        )
                    spec = replace(spec, default=param.default)

            fields[name] = spec

        # Always return a namespace, even if empty
        return SocketSpec(
            identifier=cls._ns_identifier(),
            fields=fields,
            meta=SocketMeta(call_role=CallRole.KWARGS, dynamic=is_dyn),
        )

    @classmethod
    def _wrap_leaf_as_ns(cls, leaf: SocketSpec) -> SocketSpec:
        return SocketSpec(
            identifier=cls._ns_identifier(),
            fields={cls.DEFAULT_OUTPUT_KEY: leaf},
            meta=SocketMeta(call_role=CallRole.RETURN),
        )

    @classmethod
    def build_outputs_from_signature(
        cls, func, explicit: SocketSpec | SocketView | type[BaseModel] | None
    ) -> SocketSpec:
        """Always return a NAMESPACE spec, with selection/meta applied.
        - If the function body never does `return <value>`, return an EMPTY namespace,
        regardless of annotations.
        - Otherwise, honor explicit, Annotated, or wrap leaf under DEFAULT_OUTPUT_KEY.
        """

        # explicit override (now supports BaseModel & SocketView)
        if explicit is not None:
            spec = _normalize_explicit_spec(explicit)
            if spec.is_namespace():
                return replace(spec, meta=replace(spec.meta, call_role=CallRole.RETURN))
            # leaf -> wrap under DEFAULT_OUTPUT_KEY
            return cls._wrap_leaf_as_ns(spec)

        # If function body never returns a value -> EMPTY namespace
        if not _function_returns_value(func):
            return SocketSpec(
                identifier=cls._ns_identifier(),
                fields={},
                meta=SocketMeta(call_role=CallRole.RETURN),
            )

        # Otherwise, infer from return annotation / metadata
        ann_map = cls._safe_type_hints(func)
        ret = ann_map.get("return", None)

        # Explicit spec from metadata
        spec_from_meta = _extract_spec_from_annotated(ret)
        if spec_from_meta is not None:
            spec_from_meta = _apply_select_from_annotation(ret, spec_from_meta)
            spec_from_meta = replace(
                spec_from_meta,
                meta=_merge_all_meta_from_annotation(ret, spec_from_meta.meta),
            )
            return replace(
                spec_from_meta,
                meta=replace(spec_from_meta.meta, call_role=CallRole.RETURN),
            )

        # to_spec() on annotation object
        if hasattr(ret, "to_spec") and callable(getattr(ret, "to_spec")):
            base_spec = ret.to_spec()
            base_spec = _apply_select_from_annotation(ret, base_spec)
            base_spec = replace(
                base_spec, meta=_merge_all_meta_from_annotation(ret, base_spec.meta)
            )
            return replace(
                base_spec, meta=replace(base_spec.meta, call_role=CallRole.RETURN)
            )

        # Leaf override for Pydantic
        leaf_override = _annot_is_leaf_marker(ret)
        if leaf_override is not None and _is_struct_model_type(leaf_override):
            return cls._wrap_leaf_as_ns(cls._leaf_from_type(leaf_override))

        # Fallbacks
        if ret is None or ret is inspect._empty:
            leaf = cls._leaf_from_type(Any)
            return cls._wrap_leaf_as_ns(leaf)

        base_T, _ = _unwrap_annotated(ret)
        base_T = _strip_optional(base_T)

        if isinstance(base_T, SocketSpec):
            base_T = _apply_select_from_annotation(ret, base_T)
            base_T = replace(
                base_T, meta=_merge_all_meta_from_annotation(ret, base_T.meta)
            )
            return replace(base_T, meta=replace(base_T.meta, call_role=CallRole.RETURN))

        # Pydantic model?
        if _is_struct_model_type(base_T):
            leaf = cls.from_model(base_T)
            leaf = _apply_select_from_annotation(ret, leaf)
            leaf = replace(leaf, meta=_merge_all_meta_from_annotation(ret, leaf.meta))
            if leaf.is_namespace():
                return replace(leaf, meta=replace(leaf.meta, call_role=CallRole.RETURN))
            return cls._wrap_leaf_as_ns(leaf)

        leaf = cls._leaf_from_type(base_T)
        leaf = _apply_select_from_annotation(ret, leaf)
        leaf = replace(leaf, meta=_merge_all_meta_from_annotation(ret, leaf.meta))
        return cls._wrap_leaf_as_ns(leaf)

    @classmethod
    def infer_specs_from_callable(
        cls,
        callable_obj,
        inputs: SocketSpec | None,
        outputs: SocketSpec | None,
    ) -> tuple[SocketSpec | None, SocketSpec | None]:
        in_spec = cls.build_inputs_from_signature(callable_obj, inputs)
        out_spec = cls.build_outputs_from_signature(callable_obj, outputs)
        return in_spec, out_spec


def merge_specs(ns: SocketSpec, additions: SocketSpec) -> SocketSpec:
    """
    Merge two namespace specs, giving precedence to the fields in `additions`.
    """
    if not ns.is_namespace() or not additions.is_namespace():
        raise TypeError("merge_specs expects two namespace SocketSpecs.")
    new_fields = dict(ns.fields or {})
    new_fields.update(additions.fields or {})
    return replace(ns, fields=new_fields)


def add_spec_field(
    ns: SocketSpec, name: str, spec: SocketSpec, *, create_missing: bool = False
) -> SocketSpec:
    """
    Add a field at a (possibly nested) name path like "a.b.c".
    If create_missing=True, auto-creates intermediate namespaces with the same
    namespace identifier as `ns`. Otherwise, raises when an intermediate is missing
    or is not a namespace. Raises if the final field already exists.
    """
    if not ns.is_namespace():
        raise TypeError("add_spec_field expects a namespace SocketSpec at the root.")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Field name must be a non-empty string.")

    path = [seg for seg in name.split(".") if seg]
    if not path:
        raise ValueError("Empty field path.")

    def _ensure_ns(identifier: str) -> SocketSpec:
        # create an empty namespace with the same identifier family as `ns`
        return SocketSpec(identifier=identifier, fields={})

    def _recur(cur: SocketSpec, parts: list[str]) -> SocketSpec:
        head, *rest = parts
        fields = dict(cur.fields or {})

        if not rest:
            if head in fields:
                raise ValueError(f"Field '{name}' already exists.")
            fields[head] = spec
            return replace(cur, fields=fields)

        # need to descend
        child = fields.get(head)
        if child is None:
            if not create_missing:
                raise ValueError(
                    f"Cannot add '{name}': missing intermediate namespace '{head}'."
                )
            child = _ensure_ns(ns.identifier)  # inherit the namespace identifier
        if not child.is_namespace():
            raise TypeError(
                f"Cannot descend into non-namespace field '{head}' while adding '{name}'."
            )

        new_child = _recur(child, rest)
        if new_child is child:
            return cur
        fields[head] = new_child
        return replace(cur, fields=fields)

    return _recur(ns, path)


def remove_spec_field(ns: SocketSpec, names: Union[str, Iterable[str]]) -> SocketSpec:
    """
    Remove one or more fields by dotted path, e.g. "a.b.c" or ["x", "y.z"].
    Missing paths are ignored (idempotent).
    """
    if not ns.is_namespace():
        raise TypeError("remove_spec_field expects a namespace SocketSpec at the root.")
    if isinstance(names, str):
        names = [names]
    names = [n for n in names if isinstance(n, str) and n.strip()]
    if not names:
        return ns
    tree = _paths_to_tree(names)
    return _spec_exclude(ns, tree)


def _function_returns_value(func) -> bool:
    """
    True iff the *top-level* function body contains `return <non-None>`.

    Conservative defaults:
    - If source is unavailable, or AST parse fails, or the function task can't be found,
      return True (assume it returns a value).
    """
    try:
        src = inspect.getsource(func)
    except (OSError, TypeError):
        # No source (e.g., builtins). Be conservative: assume it DOES return a value
        return True
    src = textwrap.dedent(src)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        # Be conservative: assume it DOES return a value
        return True

    # Find the outer function by name
    target_fn = None
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func.__name__
        ):
            target_fn = node
            break
    if target_fn is None:
        # Conservative: assume it DOES return a value
        return True

    class _TopLevelReturnVisitor(ast.NodeVisitor):
        def __init__(self):
            self.returns_value = False

        def visit_FunctionDef(self, node):  # skip nested
            pass

        def visit_AsyncFunctionDef(self, node):
            pass

        def visit_ClassDef(self, node):
            pass

        def visit_Return(self, node: ast.Return):
            # `return` (no value) or `return None` -> does NOT produce an output value
            if node.value is None:
                return
            if isinstance(node.value, ast.Constant) and node.value.value is None:
                return
            self.returns_value = True

    v = _TopLevelReturnVisitor()
    for stmt in target_fn.body:
        v.visit(stmt)
        if v.returns_value:
            return True
    return False


def _set_leaf_default(ns: SocketSpec, path: tuple[str, ...], value: Any) -> SocketSpec:
    head, *rest = path
    child = ns.fields[head]
    if rest:
        if not child.is_namespace():
            raise TypeError("Path passes through a leaf.")
        return replace(
            ns, fields={**ns.fields, head: _set_leaf_default(child, tuple(rest), value)}
        )
    if child.is_namespace():
        raise TypeError("Cannot set default on a namespace.")
    return replace(ns, fields={**ns.fields, head: replace(child, default=value)})


def set_default(spec: SocketSpec | SocketView, dotted: str, value: Any) -> SocketSpec:
    root = spec.to_spec() if hasattr(spec, "to_spec") else spec
    return _set_leaf_default(root, tuple(dotted.split(".")), value)


def unset_default(spec: SocketSpec | SocketView, dotted: str) -> SocketSpec:
    root = spec.to_spec() if hasattr(spec, "to_spec") else spec
    return _set_leaf_default(root, tuple(dotted.split(".")), MISSING)


# ---------- module-level convenience exports ----------
socket = SocketSpecAPI.socket
namespace = SocketSpecAPI.namespace
dynamic = SocketSpecAPI.dynamic
validate_socket_data = SocketSpecAPI.validate_socket_data
infer_specs_from_callable = SocketSpecAPI.infer_specs_from_callable
from_model = SocketSpecAPI.from_model
# shorter aliases
select = SocketSpecSelect
meta = SocketMeta
