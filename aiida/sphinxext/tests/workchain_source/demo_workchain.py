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
        spec.output('x', valid_type=Float, help='Output of the demoworkchain.')

class NormalClass(object):
    """This is here to check that we didn't break the regular 'autoclass."""
