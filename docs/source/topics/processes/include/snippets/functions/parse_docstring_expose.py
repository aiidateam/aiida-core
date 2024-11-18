from aiida.engine import WorkChain, calcfunction


@calcfunction
def add(x: int, y: int):
    """Add two integers.

    :param x: Left hand operand.
    :param y: Right hand operand.
    """
    return x + y


class Wrapper(WorkChain):
    """Workchain that exposes the ``add`` calcfunction."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(add)
