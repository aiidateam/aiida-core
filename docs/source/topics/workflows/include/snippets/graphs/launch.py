import typing as t

from aiida.common.exceptions import MissingRequiredInputsError
from aiida.engine import GraphProcess, PortField, PortModel, graph_source, run_get_node, task_source
from aiida.engine.processes.graphs.spec import GraphSpec


class Settings(PortModel):
    iterations: t.Annotated[int, PortField(help='Set the iteration count.')]


@task_source
def calculate(settings: Settings) -> int:
    return settings.iterations * 2


@graph_source
def workflow(settings: Settings) -> int:
    return calculate(settings=settings)


# Keep the declaration separate from each run's values.
declaration = workflow.build()
values = {'settings': {'iterations': 3}}
launch_inputs = GraphProcess.launch_inputs(declaration, values)
results, node = run_get_node(GraphProcess, **launch_inputs, metadata={'label': 'example'})
assert results['result'] == 6
assert node.label == 'example'
assert GraphSpec.from_dict(declaration.to_dict()).to_dict() == declaration.to_dict()
assert declaration.task_names == ('calculate',)

try:
    workflow.get_launch_inputs(settings={})
except MissingRequiredInputsError as error:
    assert error.missing[0].socket_path == 'settings.iterations'
    assert error.missing[0].help == 'Set the iteration count.'
