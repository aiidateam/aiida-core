###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`WorkChain` tasks shared by the graph behavior suites.

Authoring examples illustrate the recommended shapes, including the inline retry policy;
regression fixtures preserve historical edge-case behavior.
"""

from aiida.engine import PortModel, WorkChain, calcfunction, expose, task
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph
from aiida.orm import Bool, Float, Int
from tests.engine.processes.graphs.programs.tasks import combine_model


@calcfunction
def add(x: Int, y: Int) -> Int:
    """Add two integers; creating nodes belongs in a `calcfunction`, not the `WorkChain` body."""
    return Int(x.value + y.value)


class AddWorkChain(WorkChain):
    """Add two integers through a single outline step."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.output('result', valid_type=Int)
        spec.outline(cls.add_numbers)

    def add_numbers(self):
        """Store the sum of the two inputs."""
        self.out('result', add(self.inputs.x, self.inputs.y))


add_chain = task(AddWorkChain)


class OptionalInputWorkChain(WorkChain):
    """Return `x`; `y` is optional and has no default."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int, required=False)
        spec.output('result', valid_type=Int)
        spec.outline(cls.return_x)

    def return_x(self):
        """Return the required input unchanged."""
        self.out('result', self.inputs.x)


optional_input_chain = task(OptionalInputWorkChain)


class OptionalBundle(PortModel):
    """The inputs of `OptionalInputWorkChain` returned as one namespace."""

    x: int
    y: int | None = None


@graph
def forward_optional_field(bundle: expose(optional_input_chain)) -> int | None:
    """Return an optional forwarded field without a default; an omitted one emits no output."""
    return bundle.y


@calcfunction
def pair_with_bonus(x: Int, y: Int) -> dict[str, Int]:
    """Return the sum and product, plus an extra `bonus` node."""
    return {'sum': Int(x.value + y.value), 'product': Int(x.value * y.value), 'bonus': Int(0)}


class BonusPairWorkChain(WorkChain):
    """Emit the pair outputs and an undeclared `bonus` on dynamic outputs."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.outputs.dynamic = True
        spec.outline(cls.emit)

    def emit(self):
        """Return every node of the calculation, declared or not."""
        for label, node in pair_with_bonus(self.inputs.x, self.inputs.y).items():
            self.out(label, node)


bonus_pair_chain = task(BonusPairWorkChain, outputs={'sum': Int, 'product': Int})


@graph
def select_declared(x: Int, y: Int, flag: bool) -> int:
    """Route a dynamic namespace into a branch; only its declared outputs enter the region."""
    pair = bonus_pair_chain(x=x, y=y)
    if flag:
        selected = pair.sum
    else:
        selected = pair.product
    return selected


@graph
def add_single(x: Int, y: Int) -> int:
    """Add two numbers through a single `WorkChain` placement."""
    total = add_chain(x=x, y=y)
    return total.result


@graph
def add_twice(x: Int, y: Int) -> int:
    """Add two numbers through two chained `WorkChain` placements."""
    first = add_chain(x=x, y=y)
    second = add_chain(x=first.result, y=y).alias('add_chain_2')
    return second.result


@graph
def forward_declared(x: Int, y: Int) -> int:
    """Wire a dynamic namespace whole; only its declared outputs reach the static input."""
    pair = bonus_pair_chain(x=x, y=y)
    return combine_model(pair=pair)


@graph
def forward_optional_namespace(bundle: expose(optional_input_chain)) -> OptionalBundle:
    """Return a forwarded namespace; an omitted optional field stays out of it."""
    return bundle


class ChainErrors(ExitCodeEnum):
    """Declared failures of the `flaky_chain` task."""

    UNSTABLE = ExitCode(410, 'Unstable chain.')


@calcfunction
def make_result() -> Float:
    """Store the successful result."""
    return Float(1.0)


class FlakyChain(WorkChain):
    """Fail with a mapped status or store one result, leaving the other arm absent."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('fail', valid_type=Bool)
        spec.outputs.dynamic = True
        spec.outline(cls.produce)

    def produce(self):
        """Exit mapped without outputs, or store the result."""
        if self.inputs.fail.value:
            return ChainErrors.UNSTABLE.value
        self.out('result', make_result())


flaky_chain = task(FlakyChain, outputs={'result': Float}, errors=ChainErrors)


@task
def check_chain_result(value: float | None) -> None:
    """Validate the recovered chain result, leaving the returned node untouched."""
    if value is None:
        raise ValueError('the chain never succeeded.')


@graph
def retry_chain_allowed(error: ChainErrors | None, attempt: int, limit: int) -> bool:
    """Factor an inline retry predicate without a child process or stored boolean."""
    return error is ChainErrors.UNSTABLE and attempt < limit


@graph
def retry_chain_until_repaired(max_retries: int = 1, attempt: int = 0) -> float | None:
    """Retry the flaky chain on its declared unstable failure, returning its own result node.

    The nested graph helper combines the retryable member check with the budget.
    The collaborator fails on attempt zero and runs repaired thereafter.
    The trailing guard validates without replacing the chain's result node.

    :param max_retries: the retry budget; `0` runs once and lets the guard fail.
    :param attempt: the zero-based attempt the first run steps from.
    :return: the first present chain result; the guard fails if none succeeded.
    """
    fail = attempt < 1
    ran = flaky_chain(fail=fail)
    retry = retry_chain_allowed(error=ran.error, attempt=attempt, limit=max_retries)
    while retry:
        attempt = attempt + 1
        fail = attempt < 1
        ran = flaky_chain(fail=fail)
        retry = retry_chain_allowed(error=ran.error, attempt=attempt, limit=max_retries)
    checked = check_chain_result(value=ran.result)  # noqa: F841 - the guard validates without feeding the return
    return ran.result


@task
def recover_chain(error: ChainErrors) -> str:
    """Recover from the declared chain failure."""
    return f'recovered from {error.value.status}'


@task
def read_result(result: float) -> str:
    """Read the successful result."""
    return f'result:{result}'


@task
def ensure_result(value: float | None, error: ChainErrors | None) -> str:
    """Read both arms; the absent success arm arrives as `None`."""
    if error is not None:
        return f'recovered from {error.value.status}'
    assert value is not None
    return f'result:{value}'


@graph
def recover_unproduced(fail: bool) -> str:
    """Run a chain that may fail mapped without outputs, recovering on its error arm."""
    ran = flaky_chain(fail=fail)
    if ran.error is not None:
        selected = recover_chain(error=ran.error)
    else:
        selected = read_result(result=ran.result)
    return selected


@graph
def read_absent_arm(fail: bool) -> str:
    """Read both arms unconditionally; the absent success arm arrives as `None`."""
    ran = flaky_chain(fail=fail)
    return ensure_result(value=ran.result, error=ran.error)


class FlakyStaticChain(WorkChain):
    """Fail with a mapped status or store one static result, leaving the other arm absent."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('fail', valid_type=Bool)
        spec.output('result', valid_type=Float)
        spec.outline(cls.produce)

    def produce(self):
        """Exit mapped without outputs, or store the static result."""
        if self.inputs.fail.value:
            return ChainErrors.UNSTABLE.value
        self.out('result', make_result())


flaky_static_chain = task(FlakyStaticChain, errors=ChainErrors)


class ErrorOutputChain(WorkChain):
    """Declare an `error` output of its own, the name a declared failure arm takes."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.output('error', valid_type=Int, required=False)
        spec.outline(cls.finish)

    def finish(self) -> None:
        """Finish without outputs."""


@graph
def recover_static(fail: bool) -> str:
    """Recover from a mapped failure that leaves a static output absent."""
    ran = flaky_static_chain(fail=fail)
    if ran.error is not None:
        selected = recover_chain(error=ran.error)
    else:
        selected = read_result(result=ran.result)
    return selected


@graph
def read_absent_static(fail: bool) -> str:
    """Read a static success arm unconditionally; absence arrives as `None`."""
    ran = flaky_static_chain(fail=fail)
    return ensure_result(value=ran.result, error=ran.error)


class NestedDynamicChain(WorkChain):
    """Declare a nested dynamic namespace for static specialization."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input_namespace('sub', dynamic=True)
        spec.input_namespace('sub.members', valid_type=Int, dynamic=True)
        spec.output('result', valid_type=Int)
        spec.outline(cls.noop)

    def noop(self):
        """Declare the contract only; graphs build without running this."""


nested_dynamic_chain = task(NestedDynamicChain, inputs={'sub': {'members': {'a': Int}}})


@graph
def static_nested(a: int) -> int:
    """Wire a static name into a nested dynamic namespace."""
    total = nested_dynamic_chain(sub={'members': {'a': a}})
    return total.result
