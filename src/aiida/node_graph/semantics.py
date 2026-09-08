from __future__ import annotations

"""Semantics helpers shared between graph authoring and engine execution."""

import re
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from aiida.node_graph.socket import BaseSocket, TaggedValue
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.utils.json_utils import json_ready

DEFAULT_NAMESPACE_REGISTRY: Dict[str, str] = {
    "qudt": "http://qudt.org/schema/qudt/",
    "qudt-unit": "http://qudt.org/vocab/unit/",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "https://schema.org/",
}
_NAMESPACE_REGISTRY: Dict[str, str] = dict(DEFAULT_NAMESPACE_REGISTRY)

# Matches "prefix:something" while avoiding URL-like strings containing "://"
_PREFIX_RE = re.compile(r"^(?P<prefix>[A-Za-z][\w\-]*):[^/]")


def register_namespace(prefix: str, iri: str) -> None:
    """
    Register a namespace prefix globally for semantics parsing.

    Any semantics payload that mentions ``<prefix>:...`` will have the
    corresponding ``@context`` entry auto-added unless it is already set on
    that annotation.
    """

    _NAMESPACE_REGISTRY[str(prefix)] = str(iri)


def namespace_registry() -> Dict[str, str]:
    """Return a copy of the global namespace registry."""

    return dict(_NAMESPACE_REGISTRY)


class OntologyEnum(str, Enum):
    """String-valued enum that preserves the ontology CURIE."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def _stringify(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


class SemanticTag(BaseModel):
    """
    Typed semantics payload for authoring convenience.

    This is a thin Pydantic wrapper over the SemanticsAnnotation fields; it
    exists solely to offer IDE autocomplete/validation before the values are
    normalised into a SemanticsAnnotation. Field meanings:
      - ``iri`` / ``rdf_types`` describe the subject itself; ``rdf_types`` maps
        to ``rdf:type`` triples, so keep it top-level (not under ``attributes``).
      - ``attributes`` is for literal predicate/value pairs (units, numbers,
        DOIs). Values may be scalars or iterables.
      - ``relations`` is for references to other resources/sockets (values may
        be CURIEs, IRIs, or socket refs).
    """

    model_config = ConfigDict(extra="allow")

    label: Optional[str] = None
    iri: Optional[Union[str, OntologyEnum]] = None
    rdf_types: Tuple[Union[str, OntologyEnum], ...] = ()
    context: Dict[str, str] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relations: Dict[str, Any] = Field(default_factory=dict)

    def to_semantics_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

    def to_annotation(self) -> "SemanticsAnnotation":
        return SemanticsAnnotation.from_raw(self)


def _json_ready(value: Any) -> Any:
    """Convert semantics payloads into JSON-serialisable structures."""

    return json_ready(value)


def _detect_prefixes(value: Any) -> Set[str]:
    """Return namespace prefixes found in strings within ``value``."""

    prefixes: Set[str] = set()
    if isinstance(value, BaseModel):
        prefixes.update(_detect_prefixes(value.model_dump(exclude_none=True)))
        return prefixes
    if isinstance(value, Enum):
        prefixes.update(_detect_prefixes(value.value))
        return prefixes
    if isinstance(value, str):
        match = _PREFIX_RE.match(value)
        if match and "://" not in value.split(":")[0]:
            prefixes.add(match.group("prefix"))
        return prefixes
    if isinstance(value, Mapping):
        for key, nested in value.items():
            prefixes.update(_detect_prefixes(key))
            prefixes.update(_detect_prefixes(nested))
        return prefixes
    if isinstance(value, (list, tuple, set)):
        for item in value:
            prefixes.update(_detect_prefixes(item))
    return prefixes


def _inject_namespaces(context: Mapping[str, str], *values: Any) -> Dict[str, str]:
    """Merge default namespaces when values reference known prefixes."""

    merged: Dict[str, str] = dict(context or {})
    prefixes: Set[str] = set()
    for value in values:
        prefixes.update(_detect_prefixes(value))
    for prefix in sorted(prefixes):
        if prefix in merged:
            continue
        if prefix in _NAMESPACE_REGISTRY:
            merged[prefix] = _NAMESPACE_REGISTRY[prefix]
    return merged


@dataclass(frozen=True)
class SemanticsAnnotation:
    """Normalized ontology annotation extracted from socket metadata."""

    label: Optional[str] = None
    iri: Optional[str] = None
    rdf_types: Tuple[str, ...] = ()
    context: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        context = _inject_namespaces(
            self.context, self.iri, self.rdf_types, self.attributes, self.relations
        )
        object.__setattr__(self, "context", context)

    @classmethod
    def from_raw(
        cls, raw: Optional[Mapping[str, Any]]
    ) -> Optional["SemanticsAnnotation"]:
        if not raw:
            return None
        payload: Mapping[str, Any] = raw
        if hasattr(raw, "to_semantics_dict"):
            try:
                payload = raw.to_semantics_dict()
            except Exception:
                payload = getattr(raw, "to_semantics_dict")()
        elif isinstance(raw, BaseModel):
            payload = raw.model_dump(exclude_none=True)
        elif hasattr(raw, "to_semantics"):
            payload = raw.to_semantics()
        elif hasattr(raw, "dict") and not isinstance(raw, Mapping):
            payload = raw.dict()  # type: ignore[assignment]
        elif is_dataclass(raw):
            payload = asdict(raw)  # type: ignore[assignment]
        return cls(
            label=payload.get("label"),
            iri=_stringify(payload.get("iri")),
            rdf_types=tuple(_stringify(v) for v in payload.get("rdf_types", []) or ()),
            context=dict(payload.get("context", {}) or {}),
            attributes=dict(payload.get("attributes", {}) or {}),
            relations=dict(payload.get("relations", {}) or {}),
        )

    @staticmethod
    def combine(
        annotations: Iterable[Optional["SemanticsAnnotation"]],
    ) -> Optional["SemanticsAnnotation"]:
        combined: Optional[SemanticsAnnotation] = None
        for annotation in annotations:
            if annotation is None or annotation.is_empty:
                continue
            if combined is None:
                combined = annotation
            else:
                combined = combined.merge(annotation)
        return combined

    @property
    def is_empty(self) -> bool:
        return (
            self.label is None
            and self.iri is None
            and not self.rdf_types
            and not self.context
            and not self.attributes
            and not self.relations
        )

    def merge(self, other: "SemanticsAnnotation") -> "SemanticsAnnotation":
        if other is None or other.is_empty:
            return self
        label = other.label if other.label is not None else self.label
        iri = other.iri if other.iri is not None else self.iri
        rdf_types: Tuple[str, ...]
        if self.rdf_types or other.rdf_types:
            rdf_types = tuple(dict.fromkeys((*self.rdf_types, *other.rdf_types)))
        else:
            rdf_types = ()
        context = dict(self.context)
        context.update(other.context)
        attributes = dict(self.attributes)
        attributes.update(other.attributes)
        relations = dict(self.relations)
        relations.update(other.relations)
        return SemanticsAnnotation(
            label=label,
            iri=iri,
            rdf_types=rdf_types,
            context=context,
            attributes=attributes,
            relations=relations,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.label is not None:
            payload["label"] = self.label
        if self.iri is not None:
            payload["iri"] = self.iri
        if self.rdf_types:
            payload["rdf_types"] = list(self.rdf_types)
        if self.context:
            payload["context"] = dict(self.context)
        if self.attributes:
            payload["attributes"] = dict(self.attributes)
        if self.relations:
            payload["relations"] = dict(self.relations)
        return payload

    def to_jsonld(self) -> Dict[str, Any]:
        jsonld: Dict[str, Any] = {}
        if self.context:
            jsonld["@context"] = dict(self.context)
        if self.iri is not None:
            jsonld["@id"] = self.iri
        if self.rdf_types:
            jsonld["@type"] = list(self.rdf_types)
        if self.label is not None:
            jsonld["label"] = self.label
        for predicate, value in self.attributes.items():
            jsonld[predicate] = value
        for predicate, value in self.relations.items():
            jsonld[predicate] = value
        return jsonld


@dataclass(frozen=True)
class SemanticsTree:
    """Tree representation mirroring the socket spec semantics."""

    annotation: Optional[SemanticsAnnotation] = None
    children: Dict[str, "SemanticsTree"] = field(default_factory=dict)
    dynamic: Optional["SemanticsTree"] = None

    @classmethod
    def from_spec(cls, spec: Optional[SocketSpec]) -> Optional["SemanticsTree"]:
        if spec is None:
            return None
        annotation = SemanticsAnnotation.from_raw(getattr(spec.meta, "semantics", None))
        children: Dict[str, SemanticsTree] = {}
        dynamic: Optional[SemanticsTree] = None
        if spec.is_namespace():
            for name, child in spec.fields.items():
                child_tree = cls.from_spec(child)
                if child_tree is not None:
                    children[name] = child_tree
            if spec.meta.dynamic:
                dynamic = cls.from_spec(spec.item)
        if annotation is None and not children and dynamic is None:
            return None
        return cls(annotation=annotation, children=children, dynamic=dynamic)

    @classmethod
    def from_dict(cls, raw: Optional[Mapping[str, Any]]) -> Optional["SemanticsTree"]:
        if not raw:
            return None
        annotation = SemanticsAnnotation.from_raw(raw.get("annotation"))
        children_payload = raw.get("children", {}) or {}
        children: Dict[str, SemanticsTree] = {}
        for name, payload in children_payload.items():
            child_tree = cls.from_dict(payload)
            if child_tree is not None:
                children[name] = child_tree
        dynamic = cls.from_dict(raw.get("dynamic"))
        if annotation is None and not children and dynamic is None:
            return None
        return cls(annotation=annotation, children=children, dynamic=dynamic)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.annotation is not None and not self.annotation.is_empty:
            payload["annotation"] = self.annotation.to_payload()
        if self.children:
            payload["children"] = {k: v.to_dict() for k, v in self.children.items()}
        if self.dynamic is not None:
            payload["dynamic"] = self.dynamic.to_dict()
        return payload

    def resolve(self, path: str) -> Optional[SemanticsAnnotation]:
        if path == "":
            return self.annotation
        normalized = path.replace(".", "__")
        segments = [segment for segment in normalized.split("__") if segment]
        task: Optional[SemanticsTree] = self
        annotations: List[SemanticsAnnotation] = []
        for segment in segments:
            if task is None:
                return None
            if task.annotation is not None:
                annotations.append(task.annotation)
            next_task = task.children.get(segment)
            if next_task is None and task.dynamic is not None:
                next_task = task.dynamic
            if next_task is None:
                return None
            task = next_task
        if task is not None and task.annotation is not None:
            annotations.append(task.annotation)
        return SemanticsAnnotation.combine(annotations)


@dataclass(frozen=True)
class TaskSemantics:
    """Aggregated semantics for a task's inputs and outputs."""

    inputs: Optional[SemanticsTree] = None
    outputs: Optional[SemanticsTree] = None

    @classmethod
    def from_specs(
        cls,
        inputs_spec: Optional[SocketSpec],
        outputs_spec: Optional[SocketSpec],
    ) -> Optional["TaskSemantics"]:
        inputs_tree = SemanticsTree.from_spec(inputs_spec)
        outputs_tree = SemanticsTree.from_spec(outputs_spec)
        if inputs_tree is None and outputs_tree is None:
            return None
        return cls(inputs=inputs_tree, outputs=outputs_tree)

    @classmethod
    def from_dict(cls, raw: Optional[Mapping[str, Any]]) -> Optional["TaskSemantics"]:
        if not raw:
            return None
        inputs_tree = SemanticsTree.from_dict(raw.get("inputs"))
        outputs_tree = SemanticsTree.from_dict(raw.get("outputs"))
        if inputs_tree is None and outputs_tree is None:
            return None
        return cls(inputs=inputs_tree, outputs=outputs_tree)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.inputs is not None:
            payload["inputs"] = self.inputs.to_dict()
        if self.outputs is not None:
            payload["outputs"] = self.outputs.to_dict()
        return payload

    def resolve_input(self, socket_path: str) -> Optional[SemanticsAnnotation]:
        if self.inputs is None:
            return None
        return self.inputs.resolve(socket_path)

    def resolve_output(self, socket_path: str) -> Optional[SemanticsAnnotation]:
        if self.outputs is None:
            return None
        return self.outputs.resolve(socket_path)


@dataclass(frozen=True)
class _SocketRef:
    """Lightweight pointer to a graph socket for deferred semantics resolution."""

    graph_uuid: str
    task_name: str
    socket_path: str
    kind: str  # "input" or "output"


@dataclass(frozen=True)
class SemanticsRelation:
    predicate: str
    subject: _SocketRef
    values: Tuple[Any, ...]
    label: Optional[str]
    context: Optional[Mapping[str, Any]]
    socket_label: Optional[str]


@dataclass(frozen=True)
class SemanticsPayload:
    subject: _SocketRef
    semantics: Mapping[str, Any] | SemanticsAnnotation
    socket_label: Optional[str]


def _socket_from_value(value: Any) -> Optional[BaseSocket]:
    """Return a ``BaseSocket`` from a raw value or TaggedValue proxy."""

    if isinstance(value, BaseSocket):
        return value
    if isinstance(value, TaggedValue):
        wrapped = value._socket
        return wrapped if isinstance(wrapped, BaseSocket) else None
    return None


def _socket_ref_from_value(value: Any) -> Optional[_SocketRef]:
    socket = _socket_from_value(value)
    if socket is None:
        return None
    task = getattr(socket, "_task", None)
    graph = getattr(socket, "_graph", None) or getattr(task, "graph", None)
    if task is None or graph is None:
        return None
    kind = getattr(getattr(socket, "_metadata", None), "socket_type", None)
    kind_normalized = str(kind).lower() if kind else "output"
    kind_normalized = "input" if "input" in kind_normalized else "output"
    socket_path = getattr(socket, "_scoped_name", None) or getattr(
        socket, "_name", None
    )
    if socket_path is None:
        return None
    return _SocketRef(
        graph_uuid=getattr(graph, "uuid", "<graph>"),
        task_name=getattr(task, "name", ""),
        socket_path=str(socket_path),
        kind=kind_normalized,
    )


def _graph_from_socket_value(value: Any) -> Any:
    """Return the graph object backing a socket-like value, if present."""

    socket_obj = _socket_from_value(value)
    if socket_obj is None:
        return None
    return getattr(socket_obj, "_graph", None) or getattr(
        getattr(socket_obj, "_task", None), "graph", None
    )


def _rehydrate_attachment_value(value: Any) -> Any:
    """Restore captured attachment values from serialized payloads."""

    if isinstance(value, _SocketRef):
        return value
    if isinstance(value, dict) and {
        "graph_uuid",
        "task_name",
        "socket_path",
    }.issubset(value.keys()):
        return _SocketRef(
            graph_uuid=str(value.get("graph_uuid") or "<graph>"),
            task_name=str(value.get("task_name") or ""),
            socket_path=str(value.get("socket_path") or ""),
            kind=str(value.get("kind") or "output"),
        )
    if isinstance(value, dict):
        return {k: _rehydrate_attachment_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_rehydrate_attachment_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_rehydrate_attachment_value(v) for v in value)
    return value


def _normalize_semantics_buffer(raw: Any) -> Dict[str, List[Any]]:
    """Coerce persisted semantics attachments into runtime dataclasses."""

    if not isinstance(raw, dict):
        return {"relations": [], "payloads": []}

    normalized: Dict[str, List[Any]] = {"relations": [], "payloads": []}

    for entry in raw.get("relations", []) or []:
        if isinstance(entry, SemanticsRelation):
            normalized["relations"].append(entry)
            continue
        if not isinstance(entry, dict):
            continue
        values_raw = entry.get("values", ())
        if isinstance(values_raw, (list, tuple)):
            values: Tuple[Any, ...] = tuple(
                _rehydrate_attachment_value(v) for v in values_raw
            )
        else:
            values = (_rehydrate_attachment_value(values_raw),)
        normalized["relations"].append(
            SemanticsRelation(
                predicate=str(entry.get("predicate", "")),
                subject=_rehydrate_attachment_value(entry.get("subject")),
                values=values,
                label=entry.get("label"),
                context=entry.get("context"),
                socket_label=entry.get("socket_label"),
            )
        )

    for entry in raw.get("payloads", []) or []:
        if isinstance(entry, SemanticsPayload):
            normalized["payloads"].append(entry)
            continue
        if not isinstance(entry, dict):
            continue
        semantics_entry = entry.get("semantics")
        normalized["payloads"].append(
            SemanticsPayload(
                subject=_rehydrate_attachment_value(entry.get("subject")),
                semantics=_rehydrate_attachment_value(semantics_entry),
                socket_label=entry.get("socket_label"),
            )
        )

    return normalized


ATTR_REF_KEY = "__ng_attr_ref__"


def attribute_ref(
    key: str,
    socket: Any = None,
    *,
    source: str = "attributes",
) -> Dict[str, Any]:
    """
    Declare that an attribute should be pulled from a concrete node later.

    Provide ``key`` and an optional ``socket`` to resolve against another
    socket's node; omit ``socket`` to reference the subject node being
    annotated. ``source`` selects ``node.base.attributes`` (default) or
    ``node.base.extras``.

    This keeps graph authoring declarative without forcing access to future
    values during build-time.
    """

    return {ATTR_REF_KEY: {"socket": socket, "key": key, "source": source}}


def _capture_semantics_value(value: Any) -> Any:
    """Replace sockets/TaggedValues with ``_SocketRef`` markers for later resolution."""

    ref = _socket_ref_from_value(value)
    if ref is not None:
        return ref
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _capture_semantics_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        captured = [_capture_semantics_value(v) for v in value]
        return captured if isinstance(value, list) else tuple(captured)
    return value


def _iterify(value: Any) -> Tuple[Any, ...]:
    """Coerce ``value`` into a tuple for relation objects."""

    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, set):
        return tuple(value)
    return (value,)


def attach_semantics(
    subject: Any,
    objects: Any = None,
    semantics: Mapping[str, Any] | SemanticsAnnotation | None = None,
    predicate: Optional[str] = None,
    socket_label: Optional[str] = None,
    label: Optional[str] = None,
    context: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Record runtime semantics attachments or relations (subject-first API).

    - Relations: ``attach_semantics(subject, objects, predicate="emmo:hasProperty", ...)``
    - Annotations: ``attach_semantics(subject, semantics={"label": ...}, socket_label=...)``
    """

    if predicate is not None:
        if subject is None:
            return
        relation_values: Tuple[Any, ...] = _iterify(objects)
        socket_ref = _socket_ref_from_value(subject)
        if socket_ref is not None:
            graph = _graph_from_socket_value(subject)
            knowledge_graph = getattr(graph, "knowledge_graph", None)
            if knowledge_graph is None:
                return
            captured_values = tuple(
                _capture_semantics_value(val) for val in relation_values
            )
            has_relations = len(captured_values) > 0
            # If semantics are provided, record a payload with relations + annotation;
            # otherwise store a direct relation attachment.
            if semantics is not None:
                if isinstance(semantics, SemanticsAnnotation):
                    sem_payload: Dict[str, Any] = semantics.to_payload()
                elif hasattr(semantics, "to_semantics_dict"):
                    try:
                        sem_payload = semantics.to_semantics_dict()
                    except Exception:
                        sem_payload = getattr(semantics, "to_semantics_dict")()
                elif hasattr(semantics, "model_dump"):
                    sem_payload = semantics.model_dump(exclude_none=True)
                else:
                    sem_payload = dict(semantics)
                relations = dict(sem_payload.get("relations") or {})
                if has_relations:
                    relations.setdefault(
                        predicate,
                        captured_values
                        if len(captured_values) > 1
                        else captured_values[0],
                    )
                sem_payload["relations"] = relations
                if label and "label" not in sem_payload:
                    sem_payload["label"] = label
                if context:
                    merged_ctx = dict(sem_payload.get("context") or {})
                    merged_ctx.update(context)
                    sem_payload["context"] = merged_ctx
                knowledge_graph.add_payload(
                    SemanticsPayload(
                        subject=socket_ref,
                        semantics=_capture_semantics_value(sem_payload),
                        socket_label=socket_label,
                    )
                )
            elif has_relations:
                knowledge_graph.add_relation(
                    SemanticsRelation(
                        predicate=predicate,
                        subject=socket_ref,
                        values=captured_values,
                        label=label,
                        context=context,
                        socket_label=socket_label,
                    )
                )
        return

    if subject is None or semantics is None:
        return

    socket_ref = _socket_ref_from_value(subject)
    if socket_ref is not None:
        graph = _graph_from_socket_value(subject)
        knowledge_graph = (
            getattr(graph, "knowledge_graph", None) if graph is not None else None
        )
        if knowledge_graph is not None:
            knowledge_graph.add_payload(
                SemanticsPayload(
                    subject=socket_ref,
                    semantics=_capture_semantics_value(semantics),
                    socket_label=socket_label,
                )
            )
            return


__all__ = [
    "SemanticTag",
    "OntologyEnum",
    "register_namespace",
    "namespace_registry",
    "SemanticsAnnotation",
    "SemanticsTree",
    "TaskSemantics",
    "SemanticsPayload",
    "SemanticsRelation",
    "attach_semantics",
    "ATTR_REF_KEY",
    "attribute_ref",
]
