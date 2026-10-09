from aiida import orm
from aiida.engine import PortModel, WorkChain, run, task_from_workchain
from aiida.engine import graph_execution as graph


class Combine(WorkChain):
    """A work chain like any other, taking and producing values in namespaces."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('pair.left', valid_type=orm.Int)
        spec.input('pair.right', valid_type=orm.Int)
        spec.outline(cls.combine)
        spec.output('sums.total', valid_type=orm.Int)

    def combine(self):
        self.out('sums.total', orm.Int(self.inputs.pair.left + self.inputs.pair.right).store())


combine = task_from_workchain(Combine)


class Results(PortModel):
    total: orm.Int


@graph
def combine_two(left, right) -> Results:
    return Results(total=combine(pair={'left': left, 'right': right}).sums.total)


results = run(combine_two, left=2, right=3)
