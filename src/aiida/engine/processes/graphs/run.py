###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpointable scheduling decisions for static task graphs.

One :class:`GraphProcess` executes the whole graph: nested graphs, branches,
loops, and maps are checkpointable logical scopes inside a single
:class:`GraphRun`, never submitted processes. Only task runs (calcfunctions,
`CalcJob` and `WorkChain` children) and map collectors become child processes,
dispatched directly by the root with hierarchical call labels that preserve
scope and iteration identity.
"""

from __future__ import annotations

import typing as t
from collections.abc import Mapping
from dataclasses import dataclass, field

from aiida.common.exceptions import GraphMaxIterationsError, GraphRuntimeError, GraphValidationError
from aiida.common.links import LinkType
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.graphs.inputs import _at, _drops_none_value, _place, _prepare_graph_inputs
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    Endpoint,
    GraphIR,
    GraphTask,
    LoopControl,
    MapControl,
    OutputTree,
    ProcessTask,
    SubgraphTask,
    TaskIR,
    _input_ports_at,
    _require_version,
)
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape
from aiida.manage import get_manager
from aiida.orm import DataDict, DataList, EnumData, Node, from_aiida_type, load_node, to_aiida_type
from aiida.orm.nodes.data.bool import Bool

__all__ = ('GraphRun',)

_STATE_VERSION = '0.2'
_ROOT_SCOPE: t.Final = 'root'


def _prepared_scope_given(body: GraphIR, raw: dict[str, t.Any]) -> dict[str, t.Any]:
    """Fill a child scope's inputs with defaults and validate them like a nested launch.

    Nested graphs previously launched as child `GraphProcess` nodes, so every boundary ran
    `_prepare_graph_inputs` plus input-namespace and per-consumer validation. Scopes keep the
    same contract: defaults fill here, unknown or mistyped inputs fail loudly on entry, and the
    stored `given` mirrors the root's serialized inputs.
    """
    namespace = body.build_input_namespace()
    prepared = _prepare_graph_inputs(namespace, raw, body.identifier)
    if get_manager().get_profile() is None:
        # Profile-free scheduling probes cannot serialize inputs into ORM nodes.
        return prepared
    serialized = namespace.serialize(prepared)
    if serialized is None:
        msg = 'graph inputs serialized to `None`; expected a mapping.'
        raise GraphValidationError(msg)
    runtime = namespace.prepare(serialized).runtime
    assert isinstance(runtime, Mapping)
    error = namespace.validate(runtime)
    if error is not None:
        raise GraphValidationError(error)
    for name, targets in body.inputs.items():
        try:
            value = _at(serialized, name)
        except KeyError:
            continue
        for task_name, path in targets:
            for port in _input_ports_at(body.task(task_name), path):
                error = port.validate(port.prepare(value).runtime)
                if error is not None:
                    raise GraphValidationError(error)
    assert isinstance(serialized, dict)
    return serialized


def _holds(condition: t.Any) -> bool:
    """Return whether a condition holds, accepting only `bool` and `Bool` values.
    Anything else fails loudly: truthiness coercion would silently treat `Int(0)` as false.
    """
    if isinstance(condition, bool):
        return condition
    if isinstance(condition, Bool):
        return bool(condition.value)
    msg = f'graph condition must be a `bool` or `Bool`, not `{type(condition)}`.'
    raise GraphRuntimeError(msg)


def _missing_declared_outputs(declared: NamespaceShape, node: Node) -> list[str]:
    """Return the declared dynamic outputs a finished task did not produce.

    The process spec leaves these outputs dynamic, so the process itself never enforces them.
    """
    produced = set(node.base.links.get_outgoing().all_link_labels())
    return [name for name, _ in declared.fields if name not in produced]


def _mistyped_declared_outputs(declared: NamespaceShape, node: Node) -> list[str]:
    """Return a message per declared output that a finished task produced with another node type.

    Declared types narrow the process spec, which keeps its broad ports and so accepts the value.
    """
    produced: dict[str, Node] = {
        entry.link_label: entry.node
        for entry in node.base.links.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN)).all()
    }
    messages: list[str] = []
    for name, shape in declared.fields:
        value: Node | None = produced.get(name)
        if value is None or not isinstance(shape, LeafShape) or not shape.types or isinstance(value, shape.types):
            continue
        expected: str = ', '.join(kind.__name__ for kind in shape.types)
        messages.append(f'returned `{type(value).__name__}` for port `{name}`, expected `{expected}`')
    return messages


def _at_or_none(container: t.Any, path: str) -> t.Any:
    """Read a value inside a namespace, or `None` where an optional source left it absent.

    Input filling, loop entry, and output validation reject a missing
    required value earlier, so a missing key marks an absent optional one.
    """
    try:
        return _at(container, path)
    except KeyError:
        return None


def _holds_member(task: BranchControl, condition: t.Any) -> bool:
    """Return whether a condition is the enum member a branch test names."""
    assert task.condition_member is not None
    identifier, name = task.condition_member
    expected = get_object_loader().load_object(identifier).__members__[name]
    actual = from_aiida_type(condition) if isinstance(condition, EnumData) else condition
    return actual is expected


def _error_member(spec: TaskIR, label: str, node: Node) -> t.Any:
    """Return the declared member matching a failed process task's exit status."""
    for identifier in spec.error_enums:
        kind = get_object_loader().load_object(identifier)
        for member in kind:
            if member.value.status == node.exit_status:
                return to_aiida_type(member)
    msg = f'task `{label}` failed with an unmapped exit status {node.exit_status}.'
    raise GraphRuntimeError(msg)


def _regroup_carried_outputs(body_outputs: dict[str, OutputTree], resolved: dict[str, t.Any]) -> dict[str, t.Any]:
    """Rebuild carried loop state with explicit `None` for absent optional leaves.

    Scope outputs omit absent leaves; merging them over the loop inputs would
    keep the stale initial value. Walking the static output tree reintroduces
    each absent leaf as `None`, which input filling resolves per port to
    absent, a default, or a nullable value.
    """
    carried: dict[str, t.Any] = {}
    for name, tree in body_outputs.items():
        if isinstance(tree, dict):
            sub = resolved.get(name)
            carried[name] = _regroup_carried_tree(tree, sub if isinstance(sub, dict) else {})
        else:
            carried[name] = resolved.get(name)
    return carried


def _regroup_carried_tree(tree: dict[str, OutputTree], resolved: dict[str, t.Any]) -> dict[str, t.Any]:
    """Rebuild one nested carried output, marking omitted leaves as `None`."""
    regrouped: dict[str, t.Any] = {}
    for name, child in tree.items():
        if isinstance(child, dict):
            sub = resolved.get(name)
            regrouped[name] = _regroup_carried_tree(child, sub if isinstance(sub, dict) else {})
        else:
            regrouped[name] = resolved.get(name)
    return regrouped


@dataclass(frozen=True)
class _Start:
    """A task run to dispatch under an explicit provenance call-link name."""

    instance: str
    task: GraphTask
    inputs: dict[str, t.Any]


def _drops_none(task: GraphTask, path: str) -> bool:
    """Return whether a `None` value leaves an input unwired instead of failing validation."""
    ports = _input_ports_at(task, path)
    return bool(ports) and all(_drops_none_value(port) for port in ports)


@dataclass
class _Step:
    """The dispatches decided by one scheduling step."""

    starts: list[_Start] = field(default_factory=list)

    def begin(self, instance: str, task: GraphTask, inputs: dict[str, t.Any]) -> None:
        """Record the dispatch of one task instance within this step."""
        self.starts.append(_Start(instance=instance, task=task, inputs=inputs))


@dataclass(frozen=True)
class _Failure:
    """One failed placement: a leaf task label, or a map placement aggregating its items."""

    label: str
    items: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    mistyped: tuple[str, ...] = ()


class _ScopeState(t.TypedDict, total=False):
    """The checkpointable scheduling progress of one logical execution scope."""

    parent: str | None
    placement: str
    kind: str
    selector: str
    prefix: str
    given: dict[str, t.Any]
    instances: dict[str, list[str]]
    frames: dict[str, list[str]]
    collectors: dict[str, str]
    passed: dict[str, dict[str, t.Any]]


class _GraphRunState(t.TypedDict, total=False):
    """The checkpointable scheduling progress of a graph run."""

    version: str
    scopes: dict[str, _ScopeState]
    dispatched: dict[str, int]
    done: dict[str, int]


def _new_scope_state(
    *,
    parent: str | None,
    placement: str,
    kind: str,
    selector: str,
    prefix: str,
    given: dict[str, t.Any] | None = None,
) -> _ScopeState:
    """Return a fresh scope record with empty scheduling progress."""
    state: _ScopeState = {
        'parent': parent,
        'placement': placement,
        'kind': kind,
        'selector': selector,
        'prefix': prefix,
        'instances': {},
        'frames': {},
        'collectors': {},
        'passed': {},
    }
    if given is not None:
        state['given'] = given
    return state


@dataclass
class GraphRun:
    """How far a graph has progressed; dispatch itself belongs to GraphProcess."""

    graph: GraphIR
    given: dict[str, t.Any] = field(default_factory=dict)
    scopes: dict[str, _ScopeState] = field(default_factory=dict)
    dispatched: dict[str, int] = field(default_factory=dict)
    done: dict[str, int] = field(default_factory=dict)
    _ok: dict[int, bool] = field(default_factory=dict, repr=False, compare=False)
    _nodes: dict[int, Node] = field(default_factory=dict, repr=False, compare=False)
    _templates: dict[str, GraphIR] = field(default_factory=dict, repr=False, compare=False)
    _memo_outputs: dict[str, dict[str, t.Any]] = field(default_factory=dict, repr=False, compare=False)
    _memo_placements: dict[tuple[str, str], t.Any] = field(default_factory=dict, repr=False, compare=False)
    _memo_problems: dict[str, tuple[list[str], list[str]]] = field(default_factory=dict, repr=False, compare=False)
    _memo_maps: dict[tuple[str, str], tuple[list[str], list[str]]] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Ensure the root scope exists; its inputs live on the run, like the stored graph inputs."""
        if _ROOT_SCOPE not in self.scopes:
            self.scopes[_ROOT_SCOPE] = _new_scope_state(parent=None, placement='', kind='root', selector='', prefix='')
        else:
            root = self.scopes[_ROOT_SCOPE]
            root.setdefault('instances', {})
            root.setdefault('frames', {})
            root.setdefault('collectors', {})
            root.setdefault('passed', {})

    @property
    def instances(self) -> dict[str, list[str]]:
        """Return the task labels dispatched in the root scope, keyed by placement name."""
        return self.scopes[_ROOT_SCOPE]['instances']

    @property
    def passed(self) -> dict[str, dict[str, t.Any]]:
        """Return the settled loop state of the root scope, keyed by placement name."""
        return self.scopes[_ROOT_SCOPE]['passed']

    @property
    def pending(self) -> dict[str, int]:
        """Return the dispatched task runs that have not completed yet."""
        return {label: pk for label, pk in self.dispatched.items() if label not in self.done}

    def _scope_given(self, key: str) -> dict[str, t.Any]:
        """Return the input values one scope was entered with."""
        if key == _ROOT_SCOPE:
            return self.given
        return self.scopes[key].get('given', {})

    def _template_of(self, key: str) -> GraphIR:
        """Return the static template one scope executes, resolved through its lineage.

        Templates are not checkpointed: every nested body is reachable from the stored root
        graph through the recorded placement lineage, so restores rebuild the same objects.
        """
        if key not in self._templates:
            scope = self.scopes[key]
            if key == _ROOT_SCOPE:
                self._templates[key] = self.graph
            else:
                parent_template = self._template_of(t.cast(str, scope['parent']))
                task = parent_template.task(scope['placement'])
                selector = scope['selector']
                if isinstance(task, SubgraphTask):
                    template = task.body
                elif isinstance(task, BranchControl):
                    template = task.body if selector == 'taken' else task.otherwise
                elif isinstance(task, LoopControl):
                    template = task.body
                elif isinstance(task, MapControl):
                    if task.body is None:
                        msg = f'map `{task.name}` scope resolves a nested graph but carries a task spec.'
                        raise GraphRuntimeError(msg)
                    template = task.body
                else:
                    msg = f'scope `{key}` descends from task `{task.name}`, which holds no nested graph.'
                    raise GraphRuntimeError(msg)
                self._templates[key] = template
        return self._templates[key]

    def _node(self, pk: int) -> Node:
        """Return the stored node of one finished task run, caching it per run."""
        if pk not in self._nodes:
            self._nodes[pk] = load_node(pk)
        return self._nodes[pk]

    def _is_finished_ok(self, pk: int) -> bool:
        """Return whether a finished node succeeded, caching the answer per node."""
        if pk not in self._ok:
            self._ok[pk] = self._node(pk).is_finished_ok
        return self._ok[pk]

    def _used_labels(self) -> set[str]:
        """Return every task label claimed so far, across all scopes."""
        used = set(self.dispatched) | set(self.done)
        for scope in self.scopes.values():
            for labels in scope.get('instances', {}).values():
                used.update(labels)
        return used

    def _claim(self, base: str) -> str:
        """Return a task label unused anywhere in the run, suffixing only on collision.

        Scope prefixes already separate ordinary placements; the suffix only guards
        pathological placement names containing the `__` scope separator.
        """
        used = self._used_labels()
        candidate = base
        count = 2
        while candidate in used:
            candidate = f'{base}_{count}'
            count += 1
        return candidate

    def _collect_base(self, template: GraphIR, name: str) -> str:
        """Return the collector label base of one map, avoiding placement names.

        Ordinary placements claim `name`, `name_2`, and any explicit function name, so the
        default `name_collect` can collide with them (e.g. a task function literally named
        `map_increment_collect`). Suffixing with `_map` until the label leaves every
        placement name free keeps the derivation static, so checkpoints rebuild the same labels.
        """
        taken = set(template.task_names)
        candidate = f'{name}_collect'
        while candidate in taken:
            candidate = f'{candidate}_map'
        return candidate

    def _item_base(self, template: GraphIR, name: str, index: int) -> str:
        """Return one map item label base, avoiding placement names and every map collector."""
        taken = set(template.task_names)
        collects = {self._collect_base(template, task.name) for task in template.tasks if isinstance(task, MapControl)}
        candidate = f'{name}_{index}'
        while candidate in taken or candidate in collects:
            candidate = f'{candidate}_map'
        return candidate

    def _collect_label(self, scope_key: str, name: str) -> str:
        """Return the collector label of one map, deriving and claiming it on first use."""
        scope = self.scopes[scope_key]
        collectors = scope.setdefault('collectors', {})
        if name not in collectors:
            collectors[name] = self._claim(scope['prefix'] + self._collect_base(self._template_of(scope_key), name))
        return collectors[name]

    def _collect_instance(self, name: str) -> str:
        """Return the aggregator label collecting one root map's item outputs."""
        return self._collect_base(self.graph, name)

    def _item_instance(self, name: str, index: int) -> str:
        """Return one root map item label, avoiding placement names and every map collector."""
        return self._item_base(self.graph, name, index)

    def _map_items(self, scope_key: str, name: str) -> list[str]:
        """Return the item task labels of one task-mapped map, excluding its collector."""
        collect = self.scopes[scope_key].get('collectors', {}).get(name)
        return [label for label in self.scopes[scope_key].get('instances', {}).get(name, []) if label != collect]

    def _invalidate(self) -> None:
        """Drop memoized outputs and declared-output problems after scope progress changes."""
        self._memo_outputs = {}
        self._memo_placements = {}
        self._memo_problems = {}
        self._memo_maps = {}

    def _new_scope(
        self,
        *,
        parent: str,
        placement: str,
        kind: str,
        selector: str,
        given: dict[str, t.Any],
        prefix: str,
    ) -> str:
        """Create one child scope and return its key, deterministic in its lineage."""
        sibling = sum(
            1 for scope in self.scopes.values() if scope.get('parent') == parent and scope.get('placement') == placement
        )
        key = (
            f'{parent}/{placement}'
            if sibling == 0 and kind in ('subgraph', 'branch')
            else f'{parent}/{placement}#{sibling}'
        )
        self.scopes[key] = _new_scope_state(
            parent=parent, placement=placement, kind=kind, selector=selector, prefix=prefix, given=given
        )
        self._invalidate()
        return key

    def _label_ok(self, label: str) -> bool:
        """Return whether one dispatched task run finished successfully."""
        return label in self.done and self._is_finished_ok(self.done[label])

    def _has_declared_result(self, spec: t.Any, label: str) -> bool:
        """Return whether a finished run failed with a declared outcome.

        Function tasks store the declared member on an `error` output; process
        tasks with an `errors=` mapping match the child exit status alone and the
        member is synthesized when the arm is read. Only a matching declaration
        counts: unexpected failures stay failures and never unblock dependents.
        """
        if label not in self.done or not isinstance(spec, TaskIR):
            return False
        if not spec.exit_codes:
            return False
        node = self._node(self.done[label])
        if node.is_finished_ok or not node.is_failed:
            return False
        if 'error' in node.outputs:
            error = node.outputs['error']
            if not isinstance(error, EnumData):
                return False
            value: ExitCode = error.get_member().value
            return value in spec.exit_codes.values() and value.status == node.exit_status
        return bool(spec.error_enums) and node.exit_status in {code.status for code in spec.exit_codes.values()}

    def _label_completed(self, spec: t.Any, label: str) -> bool:
        """Return whether a run finished ok or with a declared failure."""
        return self._label_ok(label) or self._has_declared_result(spec, label)

    def _is_mapped_failure(self, spec: TaskIR, label: str) -> bool:
        """Return whether a run failed with a declared error mapping.

        The success arms of such a failure are absent by design, like the missing
        arm of a `Result` task, so they read as `None` downstream.
        """
        if label not in self.done:
            return False
        if not spec.exit_codes:
            return False
        return self._has_declared_result(spec, label)

    def _label_problems(self, spec: t.Any, label: str) -> tuple[list[str], list[str]]:
        """Return the missing and mistyped declared outputs of one finished task run.

        A mapped failure carries its outcome on the `error` arm; its absent
        success arms are not missing outputs.
        """
        if label in self._memo_problems:
            return self._memo_problems[label]
        declared: NamespaceShape | None = spec.declared_outputs if isinstance(spec, TaskIR) else None
        if label not in self.done or declared is None or not declared.fields:
            return [], []
        if self._is_mapped_failure(spec, label):
            return [], []
        node = self._node(self.done[label])
        problems = (_missing_declared_outputs(declared, node), _mistyped_declared_outputs(declared, node))
        self._memo_problems[label] = problems
        return problems

    def _map_declared_problems(self, scope_key: str, task: MapControl) -> tuple[list[str], list[str]]:
        """Return the aggregated declared-output problems of one task-mapped map's items."""
        key = (scope_key, task.name)
        if key not in self._memo_maps:
            self._memo_maps[key] = self._resolve_map_declared_problems(scope_key, task)
        return self._memo_maps[key]

    def _resolve_map_declared_problems(self, scope_key: str, task: MapControl) -> tuple[list[str], list[str]]:
        if task.spec is None or not task.spec.declared_outputs.fields:
            return [], []
        missing: list[str] = []
        mistyped: list[str] = []
        for label in self._map_items(scope_key, task.name):
            if label not in self.done:
                continue
            if self._is_mapped_failure(task.spec, label):
                # Absent success arms of a mapped failure are not missing outputs.
                continue
            node = self._node(self.done[label])
            for port in _missing_declared_outputs(task.spec.declared_outputs, node):
                if port not in missing:
                    missing.append(port)
            for message in _mistyped_declared_outputs(task.spec.declared_outputs, node):
                if message not in mistyped:
                    mistyped.append(message)
        return missing, mistyped

    def _placement_ok(self, scope_key: str, name: str) -> bool:
        """Return whether a placement finished successfully with nothing left to run."""
        scope = self.scopes[scope_key]
        task = self._template_of(scope_key).task(name)
        if isinstance(task, ProcessTask):
            labels = scope.get('instances', {}).get(name, [])
            return (
                bool(labels)
                and all(self._label_completed(task.spec, label) for label in labels)
                and all(not any(self._label_problems(task.spec, label)) for label in labels)
            )
        if isinstance(task, MapControl):
            if task.spec is not None:
                items = self._map_items(scope_key, name)
                collect = scope.get('collectors', {}).get(name)
                if not items:
                    return collect is not None and self._label_ok(collect)
                if any(label not in self.done for label in items):
                    return False
                if any(not self._label_ok(label) for label in items):
                    return False
                if any(self._map_declared_problems(scope_key, task)):
                    return False
                return collect is not None and self._label_ok(collect)
            children = scope.get('frames', {}).get(name, [])
            collect = scope.get('collectors', {}).get(name)
            if not children:
                return collect is not None and self._label_ok(collect)
            return (
                all(self._scope_complete(child) and self._scope_ok(child) for child in children)
                and collect is not None
                and self._label_ok(collect)
            )
        if isinstance(task, (SubgraphTask, BranchControl)):
            children = scope.get('frames', {}).get(name, [])
            return len(children) == 1 and self._scope_complete(children[0]) and self._scope_ok(children[0])
        if isinstance(task, LoopControl):
            if name in scope.get('passed', {}):
                return True
            children = scope.get('frames', {}).get(name, [])
            if not children or not self._scope_complete(children[-1]) or not self._scope_ok(children[-1]):
                return False
            return not self._loop_holds(scope_key, task)
        msg = f'unsupported task `{task.name}`.'
        raise GraphRuntimeError(msg)

    def _placement_complete(self, scope_key: str, name: str) -> bool:
        """Return whether a placement has nothing left to run, successfully or not."""
        scope = self.scopes[scope_key]
        task = self._template_of(scope_key).task(name)
        if isinstance(task, ProcessTask):
            labels = scope.get('instances', {}).get(name, [])
            return bool(labels) and all(label in self.done for label in labels)
        if isinstance(task, MapControl):
            if task.spec is not None:
                items = self._map_items(scope_key, name)
                collect = scope.get('collectors', {}).get(name)
                if not items:
                    return collect is not None and collect in self.done
                if any(label not in self.done for label in items):
                    return False
                if collect is None:
                    return self._map_terminal(scope_key, task)
                return collect in self.done
            children = scope.get('frames', {}).get(name, [])
            collect = scope.get('collectors', {}).get(name)
            if not children:
                return collect is not None and collect in self.done
            if any(not self._scope_complete(child) for child in children):
                return False
            if any(not self._scope_ok(child) for child in children):
                return True
            if collect is None:
                return False
            return collect in self.done
        if isinstance(task, (SubgraphTask, BranchControl)):
            children = scope.get('frames', {}).get(name, [])
            return len(children) == 1 and self._scope_complete(children[0])
        if isinstance(task, LoopControl):
            if name in scope.get('passed', {}):
                return True
            children = scope.get('frames', {}).get(name, [])
            if not children or not self._scope_complete(children[-1]):
                return False
            if not self._scope_ok(children[-1]):
                return True
            return not self._loop_holds(scope_key, task)
        msg = f'unsupported task `{task.name}`.'
        raise GraphRuntimeError(msg)

    def _map_terminal(self, scope_key: str, task: MapControl) -> bool:
        """Return whether a task-mapped map can never collect: an item failed or broke its contract."""
        for label in self._map_items(scope_key, task.name):
            if not self._label_ok(label):
                return True
        missing, mistyped = self._map_declared_problems(scope_key, task)
        return bool(missing or mistyped)

    def _loop_holds(self, scope_key: str, task: LoopControl) -> bool:
        """Return whether a loop with a finished last iteration runs again, naming a missing condition."""
        scope = self.scopes[scope_key]
        children = scope.get('frames', {}).get(task.name, [])
        outputs = self._scope_outputs(children[-1])
        if task.condition_port not in outputs:
            msg = f'loop `{task.name}` is missing its condition port `{task.condition_port}`.'
            raise GraphRuntimeError(msg)
        return _holds(outputs[task.condition_port])

    def _scope_complete(self, key: str) -> bool:
        """Return whether a scope has nothing left to run, successfully or not."""
        scope = self.scopes[key]
        begun = set(scope.get('instances', {})) | set(scope.get('frames', {})) | set(scope.get('passed', {}))
        return not self._ready(key) and all(self._placement_complete(key, name) for name in begun)

    def _scope_ok(self, key: str) -> bool:
        """Return whether a scope finished successfully with nothing left to run."""
        if not self._scope_complete(key):
            return False
        template = self._template_of(key)
        scope = self.scopes[key]
        for task in template.tasks:
            if isinstance(task, ProcessTask):
                for label in scope.get('instances', {}).get(task.name, []):
                    if not self._label_completed(task.spec, label) or any(self._label_problems(task.spec, label)):
                        return False
            elif isinstance(task, MapControl):
                if not self._placement_ok(key, task.name):
                    return False
            elif isinstance(task, (SubgraphTask, BranchControl)):
                children = scope.get('frames', {}).get(task.name, [])
                if len(children) != 1 or not self._scope_ok(children[0]):
                    return False
            elif isinstance(task, LoopControl):
                if task.name in scope.get('passed', {}):
                    continue
                children = scope.get('frames', {}).get(task.name, [])
                if not children or not self._scope_ok(children[-1]):
                    return False
            else:
                msg = f'unsupported task `{task.name}`.'
                raise GraphRuntimeError(msg)
        return True

    def _placement_outputs(self, scope_key: str, name: str) -> t.Any:
        """Return the output mapping produced by one successfully completed placement."""
        key = (scope_key, name)
        if key not in self._memo_placements:
            self._memo_placements[key] = self._resolve_placement_outputs(scope_key, name)
        return self._memo_placements[key]

    def _resolve_placement_outputs(self, scope_key: str, name: str) -> t.Any:
        scope = self.scopes[scope_key]
        task = self._template_of(scope_key).task(name)
        if isinstance(task, ProcessTask):
            node = self._node(self.done[scope['instances'][name][-1]])
            if 'error' not in node.outputs and self._is_mapped_failure(task.spec, scope['instances'][name][-1]):
                # A mapped failure synthesizes its member from the child exit status;
                # absent success arms read as `None` downstream like a `Result` arm.
                return {'error': _error_member(task.spec, scope['instances'][name][-1], node)}
            return node.outputs
        if isinstance(task, MapControl):
            return self._node(self.done[scope['collectors'][name]]).outputs
        if isinstance(task, (SubgraphTask, BranchControl)):
            return self._scope_outputs(scope['frames'][name][-1])
        if isinstance(task, LoopControl):
            if name in scope.get('passed', {}):
                return scope['passed'][name]
            return self._scope_outputs(scope['frames'][name][-1])
        msg = f'unsupported task `{task.name}`.'
        raise GraphRuntimeError(msg)

    def _scope_outputs(self, key: str) -> dict[str, t.Any]:
        """Collect one scope's outputs from passthrough inputs and placement results."""
        if key not in self._memo_outputs:
            self._memo_outputs[key] = self._resolve_scope_outputs(key)
        return self._memo_outputs[key]

    def _resolve_scope_outputs(self, key: str) -> dict[str, t.Any]:
        return self._resolve_output_tree(key, self._template_of(key).outputs)

    def failures(self) -> list[_Failure]:
        """Return the failed placements in scope creation and graph order."""
        found: list[_Failure] = []
        for key in self.scopes:
            scope = self.scopes[key]
            template = self._template_of(key)
            for task in template.tasks:
                if isinstance(task, ProcessTask):
                    for label in scope.get('instances', {}).get(task.name, []):
                        if label not in self.done:
                            continue
                        if self._has_declared_result(task.spec, label):
                            # A declared `Result`/`errors=` failure is handled downstream.
                            continue
                        missing, mistyped = self._label_problems(task.spec, label)
                        if not self._label_ok(label) or missing or mistyped:
                            found.append(_Failure(label, missing=tuple(missing), mistyped=tuple(mistyped)))
                elif isinstance(task, MapControl):
                    if task.spec is not None:
                        items = tuple(
                            label
                            for label in self._map_items(key, task.name)
                            if label in self.done and not self._label_ok(label)
                        )
                        missing, mistyped = self._map_declared_problems(key, task)
                        collect = scope.get('collectors', {}).get(task.name)
                        collector_failed = collect is not None and collect in self.done and not self._label_ok(collect)
                        if items or missing or mistyped or collector_failed:
                            found.append(
                                _Failure(
                                    scope['prefix'] + task.name,
                                    items=items,
                                    missing=tuple(missing),
                                    mistyped=tuple(mistyped),
                                )
                            )
                    else:
                        children = scope.get('frames', {}).get(task.name, [])
                        failed_children = tuple(
                            child for child in children if self._scope_complete(child) and not self._scope_ok(child)
                        )
                        collect = scope.get('collectors', {}).get(task.name)
                        collector_failed = collect is not None and collect in self.done and not self._label_ok(collect)
                        if failed_children or collector_failed:
                            found.append(
                                _Failure(
                                    scope['prefix'] + task.name,
                                    items=tuple(self.scopes[child]['prefix'].rstrip('_') for child in failed_children),
                                    missing=(),
                                    mistyped=(),
                                )
                            )
        return found

    @property
    def failed(self) -> list[str]:
        """Return the failed placements, in scope creation and graph order."""
        return [failure.label for failure in self.failures()]

    def step(self) -> _Step:
        """Advance scheduling until synchronous control flow settles, then return dispatches."""
        result = _Step()
        # Dispatches never change within a step, so outputs and declared-output
        # problems memoize for the call; scope progress invalidates them each round.
        self._invalidate()
        try:
            while True:
                self._invalidate()
                scopes_before = len(self.scopes)
                starts_before = len(result.starts)
                passed_before = sum(len(scope.get('passed', {})) for scope in self.scopes.values())
                instances_before = sum(
                    len(labels) for scope in self.scopes.values() for labels in scope.get('instances', {}).values()
                )
                for key in list(self.scopes):
                    scope = self.scopes[key]
                    template = self._template_of(key)
                    for task in template.tasks:
                        if isinstance(task, LoopControl) and task.name in scope.get('frames', {}):
                            self._continue_loop(key, task)
                        elif isinstance(task, MapControl) and (
                            task.name in scope.get('instances', {}) or task.name in scope.get('frames', {})
                        ):
                            self._continue_map(key, task, result)
                self._invalidate()
                for key in list(self.scopes):
                    for name in self._ready(key):
                        self._begin(key, name, result)
                scopes_after = len(self.scopes)
                passed_after = sum(len(scope.get('passed', {})) for scope in self.scopes.values())
                instances_after = sum(
                    len(labels) for scope in self.scopes.values() for labels in scope.get('instances', {}).values()
                )
                if scopes_after == scopes_before and len(result.starts) == starts_before:
                    if passed_after == passed_before and instances_after == instances_before:
                        break
            return result
        finally:
            self._invalidate()

    def _ready(self, scope_key: str) -> list[str]:
        """Return the undispatched placements of one scope whose predecessors all succeeded."""
        template = self._template_of(scope_key)
        scope = self.scopes[scope_key]
        begun = set(scope.get('instances', {})) | set(scope.get('frames', {})) | set(scope.get('passed', {}))
        succeeded = {name for name in template.task_names if self._placement_ok(scope_key, name)}
        return [name for name in template.task_names if name not in begun and template.predecessors(name) <= succeeded]

    def started(self, instance: str, pk: int) -> None:
        """Record the node dispatched for one task label."""
        self.dispatched[instance] = pk

    def completed(self, instance: str, pk: int) -> None:
        """Record the node produced by one task label."""
        self.done[instance] = pk

    def outputs(self) -> dict[str, t.Any]:
        """Collect the graph outputs from passthrough inputs and task results."""
        return self._resolve_output_tree(_ROOT_SCOPE, self.graph.outputs)

    def _resolve_output_tree(self, scope_key: str, tree: OutputTree) -> t.Any:
        """Resolve one output leaf or nested mapping to its stored nodes.

        Leaves without a node stay out of the emitted outputs; a `None` value
        means the source was legitimately absent, never a stored node.
        """
        if isinstance(tree, dict):
            regrouped = {}
            for name, child in tree.items():
                resolved = self._resolve_output_tree(scope_key, child)
                if resolved is not None:
                    regrouped[name] = resolved
            return regrouped
        assert isinstance(tree, Endpoint)
        if tree.task is None:
            return _at_or_none(self._scope_given(scope_key), tree.port)
        scope = self.scopes[scope_key]
        if tree.task in scope.get('passed', {}):
            return _at_or_none(scope['passed'][tree.task], tree.port)
        return self._placement_value(scope_key, tree.task, tree.port)

    def to_dict(self) -> _GraphRunState:
        """Return the checkpointable scheduling progress, without the graph or its inputs."""
        return {
            'version': _STATE_VERSION,
            'scopes': {
                key: {
                    'parent': scope.get('parent'),
                    'placement': scope.get('placement', ''),
                    'kind': scope.get('kind', ''),
                    'selector': scope.get('selector', ''),
                    'prefix': scope.get('prefix', ''),
                    **({'given': scope['given']} if 'given' in scope else {}),
                    'instances': {name: list(labels) for name, labels in scope.get('instances', {}).items()},
                    'frames': {name: list(keys) for name, keys in scope.get('frames', {}).items()},
                    'collectors': dict(scope.get('collectors', {})),
                    'passed': {name: dict(outputs) for name, outputs in scope.get('passed', {}).items()},
                }
                for key, scope in self.scopes.items()
            },
            'dispatched': dict(self.dispatched),
            'done': dict(self.done),
        }

    @classmethod
    def from_dict(cls, graph: GraphIR, given: dict[str, t.Any], data: Mapping[str, t.Any]) -> GraphRun:
        """Rebuild the scheduling progress from a checkpoint."""
        _require_version(data.get('version', _STATE_VERSION), _STATE_VERSION, 'graph run')
        scopes: dict[str, _ScopeState] = {}
        for key, saved in data.get('scopes', {}).items():
            state = _new_scope_state(
                parent=saved.get('parent'),
                placement=saved.get('placement', ''),
                kind=saved.get('kind', ''),
                selector=saved.get('selector', ''),
                prefix=saved.get('prefix', ''),
            )
            if 'given' in saved:
                state['given'] = dict(saved['given'])
            state['instances'] = {name: list(labels) for name, labels in saved.get('instances', {}).items()}
            state['frames'] = {name: list(keys) for name, keys in saved.get('frames', {}).items()}
            state['collectors'] = dict(saved.get('collectors', {}))
            state['passed'] = {name: dict(outputs) for name, outputs in saved.get('passed', {}).items()}
            scopes[key] = state
        # Checkpoints before scopes existed cannot resume; the version gate rejects them loudly.
        if not scopes:
            scopes[_ROOT_SCOPE] = _new_scope_state(parent=None, placement='', kind='root', selector='', prefix='')
        return cls(
            graph=graph,
            given=given,
            scopes=scopes,
            dispatched=dict(data.get('dispatched', {})),
            done=dict(data.get('done', {})),
        )

    def _begin(self, scope_key: str, name: str, step: _Step) -> None:
        """Dispatch one ready placement of one scope."""
        scope = self.scopes[scope_key]
        task = self._template_of(scope_key).task(name)
        inputs = self._inputs_for(scope_key, task)
        if isinstance(task, SubgraphTask):
            self._begin_subgraph(scope_key, task, inputs)
        elif isinstance(task, BranchControl):
            self._begin_branch(scope_key, task, inputs)
        elif isinstance(task, LoopControl):
            self._begin_loop(scope_key, task, inputs)
        elif isinstance(task, MapControl):
            self._begin_map(scope_key, task, inputs, step)
        else:
            label = self._claim(scope['prefix'] + name)
            scope.setdefault('instances', {}).setdefault(name, []).append(label)
            step.begin(label, task, inputs)
        self._invalidate()

    def _begin_subgraph(self, scope_key: str, task: SubgraphTask, inputs: dict[str, t.Any]) -> None:
        """Enter one nested graph as a child scope; its tasks dispatch like any scope."""
        scope = self.scopes[scope_key]
        raw = {key: value for key, value in inputs.items() if key in task.body.inputs}
        child = self._new_scope(
            parent=scope_key,
            placement=task.name,
            kind='subgraph',
            selector='',
            given=_prepared_scope_given(task.body, raw),
            prefix=f'{scope["prefix"]}{task.name}__',
        )
        scope.setdefault('frames', {}).setdefault(task.name, []).append(child)
        self._invalidate()

    def _begin_branch(self, scope_key: str, task: BranchControl, inputs: dict[str, t.Any]) -> None:
        """Enter the taken side of a branch as one child scope; empty sides settle at once.

        `condition_test` decides selection without truthiness coercion: `is_none` and
        `is_not_none` test arm presence for `Result`/`errors=` outcomes, while `is_member`
        and `is_not_member` compare an error arm against one declared enum member.
        """
        scope = self.scopes[scope_key]
        condition = inputs.pop(task.condition_port, None)
        test = task.condition_test
        if test == 'is_none':
            selected = condition is None
        elif test == 'is_not_none':
            selected = condition is not None
        elif test in ('is_member', 'is_not_member'):
            matched = _holds_member(task, condition)
            selected = matched if test == 'is_member' else not matched
        else:
            selected = _holds(condition)
        taken = task.body if selected else task.otherwise
        selector = 'taken' if taken is task.body else 'otherwise'
        raw = {key: value for key, value in inputs.items() if key in taken.inputs}
        child = self._new_scope(
            parent=scope_key,
            placement=task.name,
            kind='branch',
            selector=selector,
            given=_prepared_scope_given(taken, raw),
            prefix=f'{scope["prefix"]}{task.name}__',
        )
        scope.setdefault('frames', {}).setdefault(task.name, []).append(child)
        self._invalidate()

    def _begin_loop(self, scope_key: str, task: LoopControl, inputs: dict[str, t.Any]) -> None:
        """Start iterating a loop, or settle a never-entered loop with its initial state."""
        if task.condition_port not in inputs:
            msg = f'loop `{task.name}` is missing its condition port `{task.condition_port}`.'
            raise GraphRuntimeError(msg)
        if not _holds(inputs[task.condition_port]):
            raw = {key: value for key, value in inputs.items() if key in task.body.inputs}
            filled = _prepared_scope_given(task.body, raw)
            self.scopes[scope_key].setdefault('passed', {})[task.name] = {
                name: filled[name] for name in task.body.outputs if name in filled
            }
            self._invalidate()
            return
        self._begin_iteration(scope_key, task, inputs)

    def _continue_loop(self, scope_key: str, task: LoopControl) -> None:
        """Dispatch the next iteration once the previous scope finished successfully."""
        children = self.scopes[scope_key].get('frames', {}).get(task.name, [])
        if not children:
            return
        last = children[-1]
        if not self._scope_complete(last):
            return
        if not self._scope_ok(last):
            return
        outputs = self._scope_outputs(last)
        if task.condition_port not in outputs:
            msg = f'loop `{task.name}` is missing its condition port `{task.condition_port}`.'
            raise GraphRuntimeError(msg)
        if not _holds(outputs[task.condition_port]):
            return
        if len(children) >= task.max_iterations:
            msg = f'loop `{task.name}` exceeded {task.max_iterations} iterations; check that its condition terminates.'
            raise GraphMaxIterationsError(msg)
        carried = _regroup_carried_outputs(task.body.outputs, outputs)
        self._begin_iteration(scope_key, task, {**self._inputs_for(scope_key, task), **outputs, **carried})

    def _map_collection(self, scope_key: str, task: MapControl, inputs: dict[str, t.Any]) -> DataList | DataDict:
        """Return the owned container one map iterates, failing loudly on anything else."""
        collection = inputs.get('collection')
        if not isinstance(collection, (DataList, DataDict)):
            msg = (
                f'map `{task.name}` iterates an owned container, but received '
                f'`{type(collection).__name__}`; pass a `DataList` or `DataDict` instead.'
            )
            raise GraphRuntimeError(msg)
        actual = 'list' if isinstance(collection, DataList) else 'dict'
        if actual != task.container:
            msg = (
                f'map `{task.name}` was lowered for `{task.container}` collections but received `{actual}`; '
                'annotate the collection as the matching container instead.'
            )
            raise GraphRuntimeError(msg)
        return collection

    def _begin_map(self, scope_key: str, task: MapControl, inputs: dict[str, t.Any], step: _Step) -> None:
        """Dispatch one task run per element in a single step, collecting empty maps at once.

        Task-mapped items run directly as child processes; graph-mapped elements run as
        child scopes whose tasks the scheduler dispatches with hierarchical labels.
        """
        scope = self.scopes[scope_key]
        collection = self._map_collection(scope_key, task, inputs)
        if isinstance(collection, DataList):
            elements = list(collection)
        else:
            elements = [collection[key] for key in collection]
        item_input = task.mapped_inputs.fields[0][0]
        template = self._template_of(scope_key)
        for index, element in enumerate(elements):
            base = self._item_base(template, task.name, index)
            item_inputs = {item_input: element}
            if task.spec is not None:
                label = self._claim(scope['prefix'] + base)
                scope.setdefault('instances', {}).setdefault(task.name, []).append(label)
                step.begin(label, ProcessTask(name=label, inputs={}, spec=task.spec), item_inputs)
            else:
                assert task.body is not None
                child = self._new_scope(
                    parent=scope_key,
                    placement=task.name,
                    kind='map',
                    selector=f'elem:{index}',
                    given=_prepared_scope_given(task.body, item_inputs),
                    prefix=f'{scope["prefix"]}{base}__',
                )
                scope.setdefault('frames', {}).setdefault(task.name, []).append(child)
        if not elements:
            self._begin_collect(scope_key, task, inputs, step)
        self._invalidate()

    def _begin_collect(self, scope_key: str, task: MapControl, inputs: dict[str, t.Any], step: _Step) -> None:
        """Dispatch the collector creating the result container from every item output."""
        scope = self.scopes[scope_key]
        result_port = task.mapped_result_port
        collected: dict[str, t.Any] = {}
        if task.spec is not None:
            items = self._map_items(scope_key, task.name)
        else:
            items = scope.get('frames', {}).get(task.name, [])
        for index, item in enumerate(items):
            if task.spec is not None:
                collected[f'item_{index}'] = _at(self._node(self.done[item]).outputs, result_port)
            else:
                collected[f'item_{index}'] = _at(self._scope_outputs(item), result_port)
        if task.container == 'dict':
            keys = list(self._map_collection(scope_key, task, inputs))
            if len(keys) != len(items):
                msg = f'map `{task.name}` collected {len(items)} outputs for {len(keys)} keys.'
                raise GraphRuntimeError(msg)
            collected['keys'] = keys
        collect = self._collect_label(scope_key, task.name)
        scope.setdefault('instances', {}).setdefault(task.name, []).append(collect)
        step.begin(collect, task, collected)
        self._invalidate()

    def _continue_map(self, scope_key: str, task: MapControl, step: _Step) -> None:
        """Dispatch the collector once every item finished successfully."""
        scope = self.scopes[scope_key]
        if task.name in scope.get('collectors', {}):
            return
        if task.spec is not None:
            items = self._map_items(scope_key, task.name)
            if any(item not in self.done for item in items):
                return
            if any(not self._label_ok(item) for item in items):
                # A failed item fails the map; the collector never runs.
                return
            if any(self._map_declared_problems(scope_key, task)):
                # Declared-output problems fail the map like an unsuccessful item.
                return
        else:
            children = scope.get('frames', {}).get(task.name, [])
            if any(not self._scope_complete(child) for child in children):
                return
            if any(not self._scope_ok(child) for child in children):
                return
        self._begin_collect(scope_key, task, self._inputs_for(scope_key, task), step)

    def _begin_iteration(self, scope_key: str, task: LoopControl, inputs: dict[str, t.Any]) -> None:
        """Enter one numbered loop iteration as a child scope; its tasks dispatch like any scope."""
        scope = self.scopes[scope_key]
        children = scope.setdefault('frames', {}).setdefault(task.name, [])
        index = len(children)
        raw = {name: value for name, value in inputs.items() if name in task.body.inputs}
        child = self._new_scope(
            parent=scope_key,
            placement=task.name,
            kind='loop',
            selector=f'iter:{index}',
            given=_prepared_scope_given(task.body, raw),
            prefix=f'{scope["prefix"]}{task.name}_iteration_{index}__',
        )
        children.append(child)
        self._invalidate()

    def _inputs_for(self, scope_key: str, task: GraphTask) -> dict[str, t.Any]:
        """Wire scope inputs and dependency outputs into one task's declared inputs."""

        # Namespace dictionaries are mutable during wiring; never mutate the saved declaration.
        def copy(value: t.Any) -> t.Any:
            return {name: copy(item) for name, item in value.items()} if isinstance(value, dict) else value

        template = self._template_of(scope_key)
        inputs = copy(task.inputs)
        for name, targets in template.inputs.items():
            try:
                value = _at(self._scope_given(scope_key), name)
            except KeyError:
                continue
            for target, port in targets:
                if target == task.name:
                    if value is None and _drops_none(task, port):
                        # An explicit `None` on an optional input leaves the input unwired.
                        continue
                    _place(inputs, port, value)
        for edge in template.dependencies:
            if edge.target == task.name and edge.carried_between is not None:
                source, target = edge.carried_between
                scope = self.scopes[scope_key]
                if edge.source in scope.get('passed', {}):
                    value = _at_or_none(scope['passed'][edge.source], source)
                else:
                    value = self._placement_value(scope_key, edge.source, source)
                if value is None and _drops_none(task, target):
                    # An absent arm on an optional input means the input is unwired.
                    continue
                _place(inputs, target, value)
        return inputs

    def _placement_value(self, scope_key: str, name: str, path: str) -> t.Any:
        """Return the value one placement produced at a path, or `None` for an omitted output.

        An empty path names the whole declared outputs namespace, resolved to
        a plain mapping so region inputs receive values instead of a link
        manager. Undeclared outputs of a dynamic namespace stay behind, since
        validation checked the edge against the declared ports only. Process
        tasks declare no error output, so a mapped failure synthesizes its
        member from the child exit status. Absent success arms read as `None`,
        like the missing arm of a `Result` task.
        """
        outputs = self._placement_outputs(scope_key, name)
        if not path:
            if isinstance(outputs, dict):
                return dict(outputs)
            declared = self._template_of(scope_key).task(name).output_ports()
            return {key: outputs[key] for key in outputs if key in declared}
        return _at_or_none(outputs, path)
