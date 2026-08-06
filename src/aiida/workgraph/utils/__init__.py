###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""WorkGraph runtime and authoring helpers (relocated from aiida-workgraph)."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from copy import deepcopy
from typing import Any, Literal, TypeAlias

import yaml
from node_graph.socket import TaggedValue
from node_graph.socket_spec import SocketSpec

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.links import validate_link_label
from aiida.engine import CalcJob, WorkChain
from aiida.engine.processes import Process
from aiida.engine.runners import Runner
from aiida.orm.utils.serialize import serialize
from aiida.workgraph.config import task_types
from aiida.workgraph.orm.utils import deserialize_safe

LOGGER = logging.getLogger(__name__)


# A task name is set through three mechanisms; each gets the fix hint for *that* mechanism,
# looked up by ``source`` rather than branched on (see ``_validate_task_name``):
#
# * ``'explicit_name'``: an explicit ``name=`` passed to :meth:`WorkGraph.add_task`. Only the
#   low-level API can set it, so the hint may safely point at ``WorkGraph.add_task``.
# * ``'derived_name'``: a name derived from the callable when no explicit name is given. This
#   is the usual high-level case (a task called inside ``@task.graph``, which never touches
#   ``add_task`` itself) and also low-level ``add_task(callable)`` without a ``name=``. The
#   only fix common to both is to rename the callable, so the hint must not mention ``name=``
#   (wrong for the high-level user) nor ``call_link_label`` (wrong for the low-level one).
# * ``'call_link_label'``: the ``metadata={'call_link_label': ...}`` override applied in
#   :meth:`TaskHandle.__call__`, which renames the task *after* ``add_task`` ran (high-level).
TaskNameSource: TypeAlias = Literal['explicit_name', 'derived_name', 'call_link_label']

_TASK_NAME_FIX_HINTS: dict[TaskNameSource, str] = {
    'explicit_name': (
        'How to fix: pass a valid `name=...` to `WorkGraph.add_task`, or omit it and rename '
        'the function/callable the task is built from.'
    ),
    'derived_name': (
        'How to fix: rename the function/callable the task is built from so its name is a valid link label.'
    ),
    'call_link_label': (
        "How to fix: choose a valid `call_link_label` (e.g. `metadata={'call_link_label': '<name>'}`), or "
        'omit it and rename the function/callable the task is built from.'
    ),
}


def _validate_task_name(name: str, *, source: TaskNameSource) -> None:
    """Validate that a task name can be used as an AiiDA provenance link label.

    A task's name becomes the ``call_link_label`` of the process it launches, so it has to
    satisfy AiiDA's link-label rules: a valid Python identifier, containing only letters,
    digits and underscores, that does not start or end with an underscore. This is stricter
    than ``node_graph``'s own name check, and it is enforced at build time so that an invalid
    name fails fast instead of silently producing no output when the task runs.

    :param name: the task name to validate.
    :param source: which mechanism set the name; selects the API-appropriate fix hint in the
        error message (see :data:`_TASK_NAME_FIX_HINTS`).
    :raises ValueError: if ``name`` cannot be used as a link label, with guidance on how to
        fix it.
    """
    try:
        validate_link_label(name)
    except ValueError as exc:
        msg = (
            f"Invalid task name '{name}': {exc}.\n"
            'A task name is used as the AiiDA provenance link label of the process it '
            'launches, so it must be a valid Python identifier containing only letters, '
            f'digits and underscores, and may not start or end with an underscore.\n'
            f'{_TASK_NAME_FIX_HINTS[source]}'
        )
        raise ValueError(msg) from exc


def inspect_aiida_component_type(executor: Callable) -> str:
    task_type = None
    if isinstance(executor, type):
        # Lazy plugin imports so that ``import aiida.workgraph`` never pulls a downstream plugin.
        # TODO: invert onto a ``_workgraph_task_type`` marker declared by each plugin process.
        try:
            from aiida_pythonjob import PythonJob
            from aiida_pythonjob.calculations.pyfunction import PyFunction
        except ImportError:
            PythonJob = PyFunction = None
        try:
            from aiida_shell.calculations.shell import ShellJob
        except ImportError:
            ShellJob = None
        if PythonJob is not None and executor == PythonJob:
            task_type = 'PYTHONJOB'
        elif PyFunction is not None and executor == PyFunction:
            task_type = 'PYFUNCTION'
        elif ShellJob is not None and executor == ShellJob:
            task_type = 'SHELLJOB'
        elif issubclass(executor, CalcJob):
            task_type = task_types[CalcJob]
        elif issubclass(executor, WorkChain):
            task_type = task_types[WorkChain]
    elif inspect.isfunction(executor):
        if getattr(executor, 'node_class', False):
            task_type = task_types[executor.node_class]
    return task_type


def generate_provenance_graph(pk: int, output: str | None = None, width: str = '100%', height: str = '600px') -> Any:
    """Generate the node graph for the given node pk.
    If in Jupyter, return the graphviz object.
    Otherwise, save the graph to an HTML file.
    """

    import pathlib

    from IPython.display import IFrame

    from aiida import orm
    from aiida.tools.visualization import Graph

    from .svg_to_html import svg_to_html

    in_jupyter = False
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            in_jupyter = True
    except NameError:
        pass

    graph = Graph()
    calc_node = orm.load_node(pk)
    graph.recurse_ancestors(calc_node, annotate_links='both')
    graph.recurse_descendants(calc_node, annotate_links='both')
    g = graph.graphviz
    if not in_jupyter:
        html_content = svg_to_html(g._repr_image_svg_xml(), width, height)
        if output is None:
            pathlib.Path('html').mkdir(exist_ok=True)
            output = f'html/node_graph_{pk}.html'
        with open(output, 'w') as f:
            f.write(html_content)
        return IFrame(output, width=width, height=height)
    return g


def get_dict_from_builder(builder: Any) -> dict:
    """Transform builder to pure dict."""
    from aiida.engine.processes.builder import ProcessBuilderNamespace

    if isinstance(builder, ProcessBuilderNamespace):
        return {k: get_dict_from_builder(v) for k, v in builder.items()}
    else:
        return builder


def clean_pickled_task_executor(tdata: dict[str, Any]) -> None:
    """Clean the pickled executor in the task data."""
    from node_graph.executor import RuntimeExecutor

    from aiida.workgraph.executors.builtins import UnavailableExecutor

    # spec
    if 'spec' in tdata:
        executor = tdata['spec'].get('executor', {})
        if executor.get('mode', '') == 'pickled_callable':
            tdata['spec']['executor'] = RuntimeExecutor.from_callable(UnavailableExecutor).to_dict()
        if executor.get('mode', '') == 'graph':
            wgdata = executor['graph_data']
            for task in wgdata['tasks'].values():
                clean_pickled_task_executor(task)
    # error handler
    for name, handler in tdata.get('error_handlers', {}).items():
        if handler.get('mode', '') == 'pickled_callable':
            tdata['error_handlers'][name] = RuntimeExecutor.from_callable(UnavailableExecutor).to_dict()


def save_workgraph_data(node: int | orm.Node, inputs: dict[str, Any]) -> None:
    from aiida.workgraph.engine.process import WorkGraphSpec

    inputs = shallow_copy_nested_dict(inputs)
    wgdata = inputs.pop(WorkGraphSpec.WORKGRAPH_DATA_KEY, {})
    task_states = {}
    task_processes = {}
    task_actions = {}
    short_wgdata = workgraph_to_short_json(wgdata)
    for name, task in wgdata['tasks'].items():
        task_states[name] = task['state']
        task_processes[name] = task['process']
        task_actions[name] = task['action']
        # clean pickled executor before save to database
        clean_pickled_task_executor(task)
    node.task_states = task_states
    node.task_processes = task_processes
    node.task_actions = task_actions
    node.workgraph_data = wgdata
    node.workgraph_data_short = short_wgdata
    node.workgraph_error_handlers = wgdata.pop('error_handlers', {})
    graph_inputs = dict(inputs.pop('graph_inputs', {}))
    tasks = dict(inputs.pop('tasks', {}))
    tasks['graph_inputs'] = graph_inputs
    node.task_inputs = serialize(tasks)


def restore_workgraph_data_from_raw_inputs(raw_inputs: dict[str, Any]) -> dict[str, Any]:
    """Restore the workgraph data from the raw inputs."""
    from aiida.workgraph.engine.process import WorkGraphSpec

    raw_inputs = dict(raw_inputs)
    wgdata = dict(raw_inputs.pop(WorkGraphSpec.WORKGRAPH_DATA_KEY, {}))
    task_inputs = dict(raw_inputs.pop('tasks', {}))
    graph_inputs = dict(raw_inputs.pop('graph_inputs', {}))
    task_inputs['graph_inputs'] = graph_inputs
    for name, data in task_inputs.items():
        wgdata['tasks'][name]['inputs'] = data
    return wgdata


def load_workgraph_data(node: int | orm.Node) -> dict[str, Any] | None:
    """
    Get the workgraph data from the given process node.
    """
    from aiida.orm import load_node
    from aiida.workgraph.engine.process import WorkGraphSpec

    if isinstance(node, int):
        node = load_node(node)
    wgdata = node.base.attributes.get(WorkGraphSpec.WORKGRAPH_DATA_KEY)
    try:
        task_inputs = deserialize_safe(node.task_inputs or '')
    except (yaml.constructor.ConstructorError, yaml.YAMLError):
        LOGGER.info('Could not deserialize inputs. The workgraph is still loaded and tasks/outputs remain inspectable.')
        task_inputs = {}

    for name, data in task_inputs.items():
        wgdata['tasks'][name]['inputs'] = data
    wgdata['error_handlers'] = node.workgraph_error_handlers
    return wgdata


def get_parent_workgraphs(pk: int) -> list[list[str, int]]:
    """Get the list of parent workgraphs.
    Use aiida incoming links to find the parent workgraphs.
    the parent workgraph is the workgraph that has a link (type CALL_WORK) to the current workgraph.
    """
    from aiida import orm
    from aiida.common.links import LinkType

    node = orm.load_node(pk)
    parent_workgraphs = [[node.process_label, node.pk]]
    links = node.base.links.get_incoming(link_type=LinkType.CALL_WORK).all()
    if len(links) > 0:
        parent_workgraphs.extend(get_parent_workgraphs(links[0].node.pk))
    return parent_workgraphs


def get_processes_latest(
    pk: int, task_name: str | None = None, item_type: str = 'task'
) -> dict[str, dict[str, int | str]]:
    """Get the latest info of all tasks from the process."""
    import aiida
    from aiida.orm import WorkGraphNode

    tasks = {}
    if pk is None:
        return tasks
    node = aiida.orm.load_node(pk)
    if item_type == 'called_process':
        # fetch the process that called by the workgraph
        for link in node.base.links.get_outgoing().all():
            if isinstance(link.node, aiida.orm.ProcessNode):
                tasks[f'{link.link_label}-{link.node.pk}'] = {
                    'pk': link.node.pk,
                    'process_type': link.node.process_type,
                    'state': link.node.process_state.value,
                    'ctime': link.node.ctime,
                    'mtime': link.node.mtime,
                }
    elif item_type == 'task':
        if not isinstance(node, WorkGraphNode):
            return tasks
        task_states = node.task_states
        task_processes = node.task_processes
        task_names = [task_name] if task_name else task_states.keys()
        for name in task_names:
            state = task_states[name]
            task_process = deserialize_safe(task_processes.get(name, ''))
            tasks[name] = {
                'pk': task_process.pk if task_process else None,
                'process_type': task_process.process_type if task_process else '',
                'state': state,
                'ctime': task_process.ctime if task_process else None,
                'mtime': task_process.mtime if task_process else None,
            }

    return tasks


def get_or_create_code(
    computer: str = 'localhost',
    code_label: str = 'python3',
    code_path: str | None = None,
    prepend_text: str = '',
):
    """Try to load code, create if not exit."""
    from aiida.orm.nodes.data.code.installed import InstalledCode

    try:
        return orm.load_code(f'{code_label}@{computer}')
    except NotExistent:
        description = f'Code on computer: {computer}'
        computer = orm.load_computer(computer)
        code_path = code_path or code_label
        code = InstalledCode(
            computer=computer,
            label=code_label,
            description=description,
            filepath_executable=code_path,
            default_calc_job_plugin='workgraph.python',
            prepend_text=prepend_text,
        )

        code.store()
        return code


def create_and_pause_process(
    runner: Runner = None,
    process_class: Callable | None = None,
    inputs: dict | None = None,
    state_msg: str = '',
) -> Process:
    from aiida.engine.utils import instantiate_process

    process_inited = instantiate_process(runner, process_class, **inputs)
    process_inited.pause(state_msg)
    process_inited.runner.persister.save_checkpoint(process_inited)
    process_inited.close()
    runner.controller.continue_process(process_inited.pid, nowait=True, no_reply=True)
    return process_inited


def get_raw_value(identifier, value: Any) -> Any:
    """Get the raw value from a Data node."""
    if identifier in [
        'workgraph.int',
        'workgraph.float',
        'workgraph.string',
        'workgraph.bool',
        'workgraph.aiida_int',
        'workgraph.aiida_float',
        'workgraph.aiida_string',
        'workgraph.aiida_bool',
    ]:
        if isinstance(value, TaggedValue):
            value = value.__wrapped__
        if value is not None and isinstance(value, orm.Data):
            return value.value
        else:
            return value
    elif isinstance(value, orm.Data):
        # avoid modifying the original attributes
        content = deepcopy(value.backend_entity.attributes)
        content['node_type'] = value.node_type
        return content


def process_properties(task: dict) -> dict:
    """Extract raw values."""
    result = {}
    for name, prop in task.get('properties', {}).items():
        identifier = prop['identifier']
        value = prop.get('value')
        result[name] = {
            'identifier': identifier,
            'value': get_raw_value(identifier, value),
        }
    for name, input in task.get('input_sockets', {}).get('sockets', {}).items():
        if input.get('property'):
            prop = input['property']
            identifier = prop['identifier']
            value = prop.get('value')
            result[name] = {
                'identifier': identifier,
                'value': get_raw_value(identifier, value),
            }

    return result


def workgraph_to_short_json(wgdata: dict[str, str | list | dict]) -> dict[str, str | dict]:
    """Export a workgraph to a rete js editor data."""

    wgdata_short = {
        'name': wgdata['name'],
        'uuid': wgdata.get('uuid', ''),
        'state': wgdata.get('state', ''),
        'nodes': {},
        'links': deepcopy(wgdata.get('links', [])),
    }
    for name, task in wgdata['tasks'].items():
        # Add required inputs to tasks
        inputs = []
        for input in task.get('input_sockets', {}).get('sockets', {}).values():
            metadata = input.get('metadata', {}) or {}
            if metadata.get('required', False):
                inputs.append({'name': input['name'], 'identifier': input['identifier']})

        properties = process_properties(task)
        wgdata_short['nodes'][name] = {
            'identifier': task['identifier'],
            'label': task['name'],
            'node_type': task['spec']['task_type'].upper(),
            'inputs': inputs,
            'properties': properties,
            'outputs': [],
            'position': task.get('position', [0, 0]),
            'children': task.get('children', []),
        }

    # Add links to tasks
    for link in wgdata_short.get('links', []):
        wgdata_short['nodes'][link['to_task']]['inputs'].append(
            {
                'name': link['to_socket'],
            }
        )
        wgdata_short['nodes'][link['from_task']]['outputs'].append(
            {
                'name': link['from_socket'],
            }
        )

    # remove the inputs socket of "graph_inputs"
    if 'graph_inputs' in wgdata_short['nodes']:
        wgdata_short['nodes']['graph_inputs']['inputs'] = []
    # remove the empty graph-level tasks
    for name in ['graph_inputs', 'graph_outputs', 'graph_ctx']:
        if name in wgdata_short['nodes']:
            node = wgdata_short['nodes'][name]
            if len(node['inputs']) == 0 and len(node['outputs']) == 0:
                del wgdata_short['nodes'][name]
    for link in wgdata_short['links']:
        link['from_node'] = link.pop('from_task')
        link['to_node'] = link.pop('to_task')
        link['from_socket'] = link.pop('from_socket')
        link['to_socket'] = link.pop('to_socket')
    return wgdata_short


def wait_to_link(wgdata: dict[str, Any]) -> None:
    """Convert wait attribute to link."""
    for name, task in wgdata['tasks'].items():
        for wait_task in task['wait']:
            if wait_task in wgdata['tasks']:
                wgdata['links'].append(
                    {
                        'from_task': wait_task,
                        'from_socket': '_wait',
                        'to_task': name,
                        'to_socket': '_wait',
                    }
                )


def shallow_copy_nested_dict(d):
    """Recursively copies only the dictionary structure but keeps value references."""
    from plumpy.utils import AttributesFrozendict

    if isinstance(d, (dict, AttributesFrozendict)):
        return {key: shallow_copy_nested_dict(value) for key, value in d.items()}
    return d


def make_json_serializable(data):
    """Recursively convert AiiDA objects to JSON-serializable structures."""
    from collections.abc import Mapping, Sequence

    if isinstance(data, orm.Data):
        # Return an int if it's an orm.Int, or a more general dict for other data
        return {
            '__aiida_class__': data.__class__.__name__,
            'uuid': str(data.uuid),
        }
    elif isinstance(data, Mapping):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        return [make_json_serializable(item) for item in data]
    else:
        return data


def resolve_tagged_values(inputs: dict[str, Any]) -> None:
    """Recursively resolve all TaggedValue either in a dictionary or a TaggedValue."""
    from node_graph.utils import resolve_tagged_values as _resolve_tagged_values

    _resolve_tagged_values(inputs)


def serialize_graph_level_data(
    input_socket: dict[str, Any],
    port_schema: SocketSpec | dict[str, Any],
    serializers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Recursively walk over the sockets and convert raw Python
    values to AiiDA Data nodes, if needed.
    """
    from aiida.workgraph import serialize_ports

    resolve_tagged_values(input_socket)
    return serialize_ports(
        python_data=input_socket,
        port_schema=port_schema,
        serializers=serializers or {},
    )


def get_process_summary(node: orm.ProcessNode | int, data: str = ['outputs']) -> None:
    """Get the outputs of a process node."""
    from aiida.cmdline.utils.common import format_nested_links
    from aiida.common.links import LinkType

    node = orm.load_node(node) if isinstance(node, int) else node
    result = ''
    if 'inputs' in data:
        nodes_input = node.base.links.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK))
        result += f'\n{format_nested_links(nodes_input.nested(), headers=["Inputs", "PK", "Type"])}'

    if 'outputs' in data:
        nodes_output = node.base.links.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN))
        result += f'\n{format_nested_links(nodes_output.nested(), headers=["Outputs", "PK", "Type"])}'
    return result


def call_depth_from_node(node: str | int | orm.Node) -> int:
    node = orm.load_node(node) if not isinstance(node, orm.Node) else node
    depth = 0
    while getattr(node, 'caller', None) is not None:
        depth += 1
        node = node.caller
    return depth


# --- generic dict / link-manager helpers (moved to core in the serializer step) ---
from aiida.orm.utils.managers import NodeLinksManager as _NodeLinksManager  # noqa: E402


def get_nested_dict(d: Any, name: str, **kwargs: Any) -> Any:
    """Get the value from a nested dictionary.

    ``d`` is deliberately ``Any``: the traversal descends through both plain dicts and AiiDA
    ``_NodeLinksManager`` containers, whose values are heterogeneous.

    If default is provided, return the default value if the key is not found.
    Otherwise, raise ValueError.
    For example:
    d = {"base": {"pw": {"parameters": 2}}}
    name = "base.pw.parameters"
    """
    keys = name.split('.')
    current = d
    for key in keys:
        if key not in current:
            if 'default' in kwargs:
                return kwargs.get('default')
            if isinstance(current, dict):
                avaiable_keys = list(current.keys())
            elif isinstance(current, _NodeLinksManager):
                avaiable_keys = list(current._get_keys())
            else:
                avaiable_keys = []
            raise ValueError(f'{name} not exist. Available keys: {avaiable_keys}')
        current = current[key]
    return current


def merge_dicts(dict1: Any, dict2: Any) -> Any:
    """Recursively merges two dictionaries."""
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            dict1[key] = merge_dicts(dict1[key], value)
        else:
            # Overwrite or add the key
            dict1[key] = value
    return dict1


def update_nested_dict(base: dict[str, Any] | None, key_path: str, value: Any) -> dict[str, Any]:
    """
    Update or create a nested dictionary structure based on a dotted key path.

    This function allows updating a nested dictionary or creating one if `d` is `None`.
    Given a dictionary and a key path (e.g., "base.pw.parameters"), it will traverse
    or create the necessary nested structure to set the provided value at the specified
    key location. If intermediate dictionaries do not exist, they will be created.
    If the resulting dictionary is empty, it is set to `None`.

    Args:
        base (Dict[str, Any] | None): The dictionary to update, which can be `None`.
                                   If `None`, an empty dictionary will be created.
        key (str): A dotted key path string representing the nested structure.
        value (Any): The value to set at the specified key.

    Example:
        base = None
        key = "scf.pw.parameters"
        value = 2
        After running:
            update_nested_dict(d, key, value)
        The result will be:
            base = {"scf": {"pw": {"parameters": 2}}}

    Edge Case:
        If the resulting dictionary is empty after the update, it will be set to `None`.

    """
    if base is None:
        base = {}
    keys = key_path.split('.')
    current_key = keys[0]
    if len(keys) == 1:
        # Base case: Merge dictionaries or set the value directly.
        if isinstance(base.get(current_key), dict) and isinstance(value, dict):
            base[current_key] = merge_dicts(base[current_key], value)
        else:
            base[current_key] = value
    else:
        # Recursive case: Ensure the key exists and is a dictionary, then recurse.
        if current_key not in base or not isinstance(base[current_key], dict):
            base[current_key] = {}
        base[current_key] = update_nested_dict(base[current_key], '.'.join(keys[1:]), value)

    return base


def update_nested_dict_with_special_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Update the nested dictionary with special keys like "base.pw.parameters"."""
    # Remove None
    data = {k: v for k, v in data.items() if v is not None}
    special_keys = [k for k in data.keys() if '.' in k]
    for key in special_keys:
        value = data.pop(key)
        update_nested_dict(data, key, value)
    return data


def resolve_node_link_managers(data: Any) -> Any:
    """Recursively resolve all NodeLinksManagers either in a dictionary or a _NodeLinksManager."""
    if isinstance(data, dict):
        return {key: resolve_node_link_managers(value) for key, value in data.items()}
    if isinstance(data, _NodeLinksManager):
        return convert_node_link_manager_to_dict(data)
    return data


def convert_node_link_manager_to_dict(node_link_manager: _NodeLinksManager) -> dict[str, Any]:
    """Recursively convert a _NodeLinksManager to a dictionary representation."""
    data = {}
    for name in node_link_manager._get_keys():
        item = node_link_manager._get_node_by_link_label(name)
        if isinstance(item, _NodeLinksManager):
            data[name] = convert_node_link_manager_to_dict(item)
        else:
            data[name] = item
    return data
