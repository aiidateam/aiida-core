from __future__ import annotations

from aiida.node_graph.config import INPUT_SOCKET_NAME


TYPE_PROMOTIONS: set[tuple[str, str]] = {
    ("node_graph.bool", "node_graph.int"),
    ("node_graph.bool", "node_graph.float"),
    ("node_graph.int", "node_graph.float"),
}


class TaskLink:
    """Link connect two sockets."""

    def __init__(self, from_socket: "Socket", to_socket: "Socket") -> None:
        """init a instance of Link

        Args:
            from_socket (Socket): The socket where the link originates from.
            to_socket (Socket): The socket where the link connects to.
        """
        self.from_socket = from_socket
        self.from_task = from_socket._task
        self.to_socket = to_socket
        self.to_task = to_socket._task
        self.check_socket_match()
        self.mount()

    @property
    def name(self) -> str:
        return "{}.{} -> {}.{}".format(
            self.from_task.name,
            self.from_socket._scoped_name,
            self.to_task.name,
            self.to_socket._scoped_name,
        )

    def _lower_id(self, sock: "Socket") -> str:
        return sock._identifier.lower()

    def _id_tail(self, sock: "Socket") -> str:
        return self._lower_id(sock).split(".")[-1]

    def _is_any(self, sock: "Socket") -> bool:
        return self._id_tail(sock) == "any"

    def _is_namespace(self, sock: "Socket") -> bool:
        return self._id_tail(sock) == "namespace"

    def _is_annotated(self, sock: "Socket") -> bool:
        return self._id_tail(sock) == "annotated"

    def _annotated_union(self, sock: "Socket") -> list[dict] | None:
        extras = getattr(getattr(sock, "_metadata", None), "extras", {}) or {}
        union = extras.get("union")
        return union if isinstance(union, list) else None

    def _annotated_py_type(self, sock: "Socket") -> str | None:
        extras = getattr(getattr(sock, "_metadata", None), "extras", {}) or {}
        return extras.get("py_type")

    def _format_union(self, union: list[dict]) -> str:
        parts: list[str] = []
        seen: set[str] = set()
        for entry in union:
            ident = str(entry.get("identifier", "")).lower()
            if not ident:
                continue
            tail = ident.split(".")[-1]
            if tail == "annotated":
                py = entry.get("py_type")
                label = str(py) if py else tail
            else:
                label = tail
            if label in seen:
                continue
            seen.add(label)
            parts.append(label)
        return " | ".join(parts) if parts else "union"

    def _annotated_type(self, sock: "Socket") -> str | None:
        union = self._annotated_union(sock)
        if union:
            return self._format_union(union)
        return self._annotated_py_type(sock)

    def _namespace_item(self, sock: "Socket") -> dict | None:
        extras = getattr(getattr(sock, "_metadata", None), "extras", {}) or {}
        item = extras.get("item")
        return item if isinstance(item, dict) else None

    def _format_socket_id(self, sock: "Socket") -> str:
        identifier = self._lower_id(sock)
        if self._is_annotated(sock):
            ann = self._annotated_type(sock)
            if ann:
                return f"{identifier}<{ann}>"
        return identifier

    def _graph_type_promotions(self) -> set[tuple[str, str]]:
        """Optional, user-registered identifier-level promotions on the graph."""
        return getattr(self.from_task.graph, "type_promotions", set())

    def _union_allows_socket(
        self, union: list[dict], other: "Socket", *, union_is_source: bool
    ) -> bool:
        other_id = self._lower_id(other)
        other_union = self._annotated_union(other)
        if other_union:
            for left in union:
                left_id = str(left.get("identifier", "")).lower()
                left_py = left.get("py_type")
                for right in other_union:
                    right_id = str(right.get("identifier", "")).lower()
                    right_py = right.get("py_type")
                    if left_id and right_id and left_id == right_id:
                        return True
                    if (
                        left_id.endswith("annotated")
                        and right_id.endswith("annotated")
                        and left_py
                        and right_py
                        and left_py == right_py
                    ):
                        return True
                    if union_is_source:
                        if (left_id, right_id) in self._graph_type_promotions():
                            return True
                    else:
                        if (right_id, left_id) in self._graph_type_promotions():
                            return True
            return False

        other_py = self._annotated_py_type(other) if self._is_annotated(other) else None
        for entry in union:
            entry_id = str(entry.get("identifier", "")).lower()
            if not entry_id:
                continue
            if entry_id.split(".")[-1] == "any":
                return True
            if other_id == entry_id:
                return True
            if (
                self._is_annotated(other)
                and entry_id.endswith("annotated")
                and entry.get("py_type")
                and entry.get("py_type") == other_py
            ):
                return True
            if union_is_source:
                if (entry_id, other_id) in self._graph_type_promotions():
                    return True
            else:
                if (other_id, entry_id) in self._graph_type_promotions():
                    return True
        return False

    def check_socket_match(self) -> None:
        """Check if the socket type match, and belong to the same task graph."""
        if self.from_task.graph != self.to_task.graph:
            raise Exception(
                "Can not link sockets from different graphs. {} and {}".format(
                    self.from_task.graph,
                    self.to_task.graph,
                )
            )

        from_id = self._lower_id(self.from_socket)
        to_id = self._lower_id(self.to_socket)

        # "any" accepts anything
        if self._is_any(self.from_socket) or self._is_any(self.to_socket):
            return

        if self._is_namespace(self.from_socket) ^ self._is_namespace(self.to_socket):
            from_is_ns = self._is_namespace(self.from_socket)
            ns_socket = self.from_socket if from_is_ns else self.to_socket
            leaf_socket = (
                self.to_socket if ns_socket is self.from_socket else self.from_socket
            )

            if from_is_ns:
                src = f"{self.from_task.name}.{self.from_socket._scoped_name}"
                dst = f"{self.to_task.name}.{self.to_socket._scoped_name}"
                lines = [
                    "Namespace to leaf link is not allowed:",
                    f"  {src} [{self._format_socket_id(self.from_socket)}] ->"
                    f" {dst} [{self._format_socket_id(self.to_socket)}] is not allowed.",
                    "",
                    "Why this matters:",
                    "  • Namespace sockets carry dict-like values; leaf sockets expect a single item.",
                    "  • Python could pass a dict here, but we block this to keep strict data provenance.",
                    "",
                    "Suggestions:",
                    "  • Link a specific item socket from the namespace",
                    "  • Or gather leaf sockets into a namespace input",
                ]
                raise TypeError("\n".join(lines))

            item = self._namespace_item(ns_socket)
            if item is None:
                return
            item_id = str(item.get("identifier", "")).lower()
            item_tail = item_id.split(".")[-1] if item_id else ""
            if item_tail == "any":
                return

            leaf_id = self._lower_id(leaf_socket)
            if item_tail == "annotated":
                item_meta = (
                    item.get("meta", {})
                    if isinstance(item.get("meta", {}), dict)
                    else {}
                )
                item_py = (
                    item_meta.get("extras", {}).get("py_type")
                    if isinstance(item_meta.get("extras", {}), dict)
                    else None
                )
                leaf_py = self._annotated_type(leaf_socket)
                if item_py and leaf_py and item_py == leaf_py:
                    return
            if leaf_id == item_id:
                return
            if (leaf_id, item_id) in self._graph_type_promotions():
                return

            src = f"{self.from_task.name}.{self.from_socket._scoped_name}"
            dst = f"{self.to_task.name}.{self.to_socket._scoped_name}"
            lines = [
                "Namespace item type mismatch:",
                f"  {src} [{self._format_socket_id(self.from_socket)}] ->"
                f" {dst} [{self._format_socket_id(self.to_socket)}] is not allowed.",
                f"  Expected namespace item type: {item_id or '<unknown>'}",
                "",
                "Suggestions:",
                "  • Link a socket matching the namespace item type",
                "  • Add a type mapping or promotion if this is intentional",
            ]
            raise TypeError("\n".join(lines))

        if self._is_annotated(self.from_socket):
            union = self._annotated_union(self.from_socket)
            if union and self._union_allows_socket(
                union, self.to_socket, union_is_source=True
            ):
                return

        if self._is_annotated(self.to_socket):
            union = self._annotated_union(self.to_socket)
            if union and self._union_allows_socket(
                union, self.from_socket, union_is_source=False
            ):
                return

        if self._is_annotated(self.from_socket) and self._is_annotated(self.to_socket):
            from_type = self._annotated_py_type(self.from_socket)
            to_type = self._annotated_py_type(self.to_socket)
            if from_type and to_type and from_type != to_type:
                src = f"{self.from_task.name}.{self.from_socket._scoped_name}"
                dst = f"{self.to_task.name}.{self.to_socket._scoped_name}"
                lines = [
                    "Socket annotated type mismatch:",
                    f"  {src} [{from_id}<{from_type}>] -> {dst} [{to_id}<{to_type}>] is not allowed.",
                    "",
                    "Suggestions:",
                    "  • Add a type mapping if these should be treated as the same socket type",
                    "  • Insert an explicit conversion task",
                ]
                raise TypeError("\n".join(lines))

        # exact match
        if from_id == to_id:
            return

        # graph-level promotions (identifier-level)
        if (from_id, to_id) in self._graph_type_promotions():
            return

        src = f"{self.from_task.name}.{self.from_socket._scoped_name}"
        dst = f"{self.to_task.name}.{self.to_socket._scoped_name}"

        lines = [
            "Socket type mismatch:",
            f"  {src} [{self._format_socket_id(self.from_socket)}] -> {dst} "
            f"[{self._format_socket_id(self.to_socket)}] is not allowed.",
            "",
            "Suggestions:",
            "  • Double-check you are linking the intended sockets \n"
            "  • If this conversion is intentional, register an identifier-level promotion \n",
        ]

        raise TypeError("\n".join(lines))

    def mount(self) -> None:
        """Create a link trigger the update action for the sockets."""
        self.from_socket._links.append(self)
        if len(self.to_socket._links) < self.to_socket._link_limit:
            self.to_socket._links.append(self)
        else:
            # handle multi-link here
            raise Exception(
                "Socket {}: number of links {} larger than the link limit {}.".format(
                    self.to_socket._full_name_with_task,
                    len(self.to_socket._links) + 1,
                    self.to_socket._link_limit,
                )
            )

    def unmount(self) -> None:
        """unmount link from task"""
        i = 0
        for link in self.from_socket._links:
            if (
                link.from_task.name == self.from_task.name
                and link.from_socket._name == self.from_socket._name
                and link.to_task.name == self.to_task.name
                and link.to_socket._name == self.to_socket._name
            ):
                break
            i += 1
        del self.from_socket._links[i]
        #
        i = 0
        for link in self.to_socket._links:
            if (
                link.from_task.name == self.from_task.name
                and link.from_socket._name == self.from_socket._name
                and link.to_task.name == self.to_task.name
                and link.to_socket._name == self.to_socket._name
            ):
                break
            i += 1
        del self.to_socket._links[i]

    def to_dict(self) -> dict:
        """Data to be saved to database"""
        from_socket_name = self.from_socket._scoped_name
        to_socket_name = self.to_socket._scoped_name
        if (
            to_socket_name == "inputs"
            and getattr(self.to_socket, "_parent", None) is None
        ):
            to_socket_name = INPUT_SOCKET_NAME
        dbdata = {
            "from_socket": from_socket_name,
            "from_task": self.from_task.name,
            "to_socket": to_socket_name,
            "to_task": self.to_task.name,
        }
        return dbdata

    def copy(self) -> None:
        """We can not simply copy the link, because the link is related to the task."""
        pass

    def __repr__(self) -> str:
        s = ""
        s += 'TaskLink(from="{}.{}", to="{}.{}")'.format(
            self.from_task.name,
            self.from_socket._scoped_name,
            self.to_task.name,
            self.to_socket._scoped_name,
        )
        return s
