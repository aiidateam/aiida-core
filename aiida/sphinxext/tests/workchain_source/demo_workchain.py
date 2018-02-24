"""This module defines an example workchain for the aiida-workchain documentation directive."""

# This import is here to test an error which is triggered if
# can_document_member raises an exception.
import re

from aiida.work.workchain import WorkChain
from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int


class DemoWorkChain(WorkChain):  # pylint: disable=abstract-method
    """
    A demo workchain to show how the workchain auto-documentation works.
    """

    @classmethod
    def define(cls, spec):
        super(DemoWorkChain, cls).define(spec)

        spec.input('x', valid_type=Float, help='First input argument.')
        spec.input('y.z', valid_type=Int, help='Input in a separate namespace.')
        spec.output('z', valid_type=Bool, help='Output of the demoworkchain.')

class NormalClass(object):
    """This is here to check that we didn't break the regular 'autoclass."""
