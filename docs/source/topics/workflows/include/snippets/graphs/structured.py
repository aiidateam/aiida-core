import typing as t

from aiida.engine import PortField, PortModel, graph_source, run_get_node, task_source


class RelaxInputs(PortModel):
    structure: t.Annotated[str, PortField(help='Structure to relax.')]
    steps: int = 10


@task_source
def relax(given: RelaxInputs) -> str:
    # given is an attribute-accessible namespace, not a RelaxInputs instance.
    return f'{given.structure}-relaxed-{given.steps}'


@graph_source
def relax_and_report(given: RelaxInputs) -> str:
    return relax(given=given)


results, node = run_get_node(relax_and_report, given={'structure': 'si'})
assert results['result'] == 'si-relaxed-10'
