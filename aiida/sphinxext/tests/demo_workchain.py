"""This module defines an example workchain for the aiida-workchain documentation directive."""

from aiida.work.workchain import WorkChain
from aiida.orm.data.base import Int, Float, Bool


class DemoWorkChain(WorkChain):  # pylint: disable=abstract-method
    """
    A demo workchain to show how the workchain auto-documentation works.
    """

    @classmethod
    def define(cls, spec):
        super(DemoWorkChain, cls).define(spec)

        spec.input('x', valid_type=Float, help='First input argument.')
        spec.output('x', valid_type=Float)
        spec.expose_inputs(SubWorkChain, namespace='sub')
        spec.expose_outputs(SubWorkChain)


class SubWorkChain(WorkChain):  # pylint: disable=abstract-method
    """
    A sub-workchain, to show how port namespaces are handled.
    """

    @classmethod
    def define(cls, spec):
        super(SubWorkChain, cls).define(spec)

        spec.input(
            'y',
            valid_type=Int,
            help="The second, nested input.",
            required=False
        )
        spec.output('y', valid_type=Int)
        spec.expose_inputs(NestedSubWorkChain, namespace='sub')
        spec.expose_outputs(NestedSubWorkChain)


class NestedSubWorkChain(WorkChain):  # pylint: disable=abstract-method
    """
    A nested workchain, to show how second-level port namespaces are handled.
    """

    @classmethod
    def define(cls, spec):
        super(NestedSubWorkChain, cls).define(spec)

        spec.input(
            'z',
            valid_type=Bool,
            help="A third input variable, that is nested two levels deep."
        )
        spec.output('z', valid_type=Bool)
