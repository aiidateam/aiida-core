"""Implementation of the MultiplyAddWorkChain for testing and demonstration purposes."""

from aiida import orm
from aiida.engine import WorkChain, calcfunction


@calcfunction
def add_structure(x: orm.Group):
    x.add_nodes([orm.StructureData(next(x.nodes).cell).store()])
    return x


class SomeWorkchain(WorkChain):
    """WorkChain to multiply two numbers and add a third, for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.input('x', valid_type=orm.Group)
        spec.outline(
            cls.add_structure,
        )
        spec.output('result', valid_type=orm.Group)

    def add_structure(self):
        self.out('result', add_structure(self.inputs.x))
