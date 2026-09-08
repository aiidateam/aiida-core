"""Shared socket metadata structures used by specs and runtime sockets."""

from __future__ import annotations

from collections.abc import Mapping as AbcMapping, Sequence, Set
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional

UPDATABLE_SOCKET_META_FIELDS = {"value_source"}


class CallRole(str, Enum):
    """Defines how a socket's value is used in a function call."""

    ARGS = "args"
    KWARGS = "kwargs"
    VAR_ARGS = "var_args"
    VAR_KWARGS = "var_kwargs"
    RETURN = "return"


@dataclass()
class SocketMeta:
    """Metadata describing a socket at authoring or runtime."""

    help: Optional[str] = None
    required: Optional[bool] = True
    call_role: Optional[CallRole] = None
    is_metadata: bool = False
    dynamic: bool = False
    child_default_link_limit: Optional[int] = 1
    socket_type: Optional[str] = None
    arg_type: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)
    semantics: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        # Always operate on a shallow copy so callers can mutate extras freely.
        self.extras = dict(self.extras)
        if self.semantics is not None:
            self.semantics = dict(self.semantics)

    def __hash__(self) -> int:
        """Freezing nested extras into stable, hashable tuples so Annotated
        metadata remains compatible with PEP 604 unions on Python 3.10."""

        return hash(
            (
                self.help,
                self.required,
                self.call_role,
                self.is_metadata,
                self.dynamic,
                self.child_default_link_limit,
                self.socket_type,
                self.arg_type,
                self._freeze_extras(self.extras),
                self._freeze_value(self.semantics)
                if self.semantics is not None
                else None,
            )
        )

    @classmethod
    def _freeze_extras(cls, extras: Dict[str, Any]) -> tuple[Any, ...]:
        if not extras:
            return ()
        return tuple(
            sorted((key, cls._freeze_value(value)) for key, value in extras.items())
        )

    @classmethod
    def _freeze_value(cls, value: Any) -> Any:
        if isinstance(value, AbcMapping):
            return tuple(sorted((k, cls._freeze_value(v)) for k, v in value.items()))
        if isinstance(value, (list, tuple, Sequence)) and not isinstance(
            value, (str, bytes, bytearray, memoryview)
        ):
            return tuple(cls._freeze_value(v) for v in value)
        if isinstance(value, (set, frozenset, Set)):
            return tuple(sorted(cls._freeze_value(v) for v in value))
        if isinstance(value, Enum):
            return value.value
        try:
            hash(value)
        except TypeError:
            return repr(value)
        return value

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.help is not None:
            data["help"] = self.help
        if self.required is not None:
            data["required"] = self.required
        if self.call_role is not None:
            data["call_role"] = self.call_role
        if self.is_metadata:
            data["is_metadata"] = True
        if self.dynamic:
            data["dynamic"] = True
        if self.child_default_link_limit is not None:
            data["child_default_link_limit"] = self.child_default_link_limit
        if self.socket_type is not None:
            data["socket_type"] = self.socket_type
        if self.arg_type is not None:
            data["arg_type"] = self.arg_type
        if self.extras:
            data["extras"] = deepcopy(self.extras)
        if self.semantics is not None:
            data["semantics"] = deepcopy(self.semantics)
        return data

    @classmethod
    def from_dict(cls, raw: Optional[Mapping[str, Any]]) -> "SocketMeta":
        if raw is None:
            return cls()

        if isinstance(raw, cls):
            return raw

        payload: Dict[str, Any] = dict(raw)

        if "meta" in payload:
            # legacy shape emitted by older runtimes
            meta_section = dict(payload.pop("meta") or {})
            for key in ("dynamic", "required", "is_metadata", "is_metadata"):
                if key in payload and key not in meta_section:
                    meta_section[key] = payload[key]
            if (
                "child_default_link_limit" not in meta_section
                and "child_default_link_limit" in payload
            ):
                meta_section["child_default_link_limit"] = payload[
                    "child_default_link_limit"
                ]
            extras = dict(meta_section.get("extras", {}))
            extras.update(payload.pop("extras", {}))
            for legacy_flag in ("builtin_socket", "function_socket"):
                if legacy_flag in payload:
                    extras.setdefault(legacy_flag, payload[legacy_flag])
            meta_section["extras"] = extras
            payload.update(meta_section)

        extras = dict(payload.pop("extras", {}))
        semantics = payload.pop("semantics", None)
        if semantics is None and "semantics" in extras:
            semantics = extras.pop("semantics")
        if semantics is not None:
            semantics = dict(semantics)
        if "builtin_socket" in payload:
            extras.setdefault("builtin_socket", payload.pop("builtin_socket"))
        if "function_socket" in payload:
            extras.setdefault("function_socket", payload.pop("function_socket"))

        if "is_metadata" in payload and "is_metadata" not in payload:
            payload["is_metadata"] = payload.pop("is_metadata")
        if (
            "child_default_link_limit" not in payload
            and "child_default_link_limit" in payload
        ):
            payload["child_default_link_limit"] = payload.pop(
                "child_default_link_limit"
            )

        call_role = payload.get("call_role")
        if call_role is not None and not isinstance(call_role, CallRole):
            try:
                payload["call_role"] = CallRole(call_role)
            except ValueError:
                payload["call_role"] = None

        payload["extras"] = extras
        payload["semantics"] = semantics

        return cls(**payload)


def merge_meta(base: SocketMeta, overlay: SocketMeta) -> SocketMeta:
    """Overlay non-default values from ``overlay`` onto ``base``."""

    extras: Dict[str, Any] = dict(base.extras)
    extras.update(overlay.extras)
    if overlay.semantics is not None:
        semantics: Optional[Dict[str, Any]] = dict(overlay.semantics)
    elif base.semantics is not None:
        semantics = dict(base.semantics)
    else:
        semantics = None
    return SocketMeta(
        help=overlay.help if overlay.help is not None else base.help,
        required=overlay.required if overlay.required is not None else base.required,
        call_role=overlay.call_role
        if overlay.call_role is not None
        else base.call_role,
        is_metadata=overlay.is_metadata or base.is_metadata,
        dynamic=overlay.dynamic or base.dynamic,
        child_default_link_limit=(
            overlay.child_default_link_limit
            if overlay.child_default_link_limit is not None
            else base.child_default_link_limit
        ),
        socket_type=overlay.socket_type or base.socket_type,
        arg_type=overlay.arg_type or base.arg_type,
        extras=extras,
        semantics=semantics,
    )
