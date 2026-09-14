from dataclasses import dataclass

from pydantic import BaseModel

from aiida.engine import graph, run, task


class RelaxInputs(BaseModel):
    """What the task takes, said once and used in both places."""

    structure: str
    steps: int = 10


@dataclass
class RelaxOutputs:
    """What it produces, which need not be said in the same words."""

    relaxed: str
    energy: float


@task
def relax(given: RelaxInputs) -> RelaxOutputs:
    return RelaxOutputs(relaxed=f'{given.structure}-relaxed', energy=-1.0 * given.steps)


@graph
def relax_and_report(structure):
    relaxed = relax(given={'structure': structure, 'steps': 3})
    return {'energy': relaxed.energy}


results = run(relax_and_report, structure='si')
