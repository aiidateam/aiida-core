"""
Module for the non empty string parameter type
"""

from __future__ import absolute_import
from click.types import StringParamType


class NonEmptyStringParamType(StringParamType):
    """
    Parameter that cannot be an an empty string.
    """
    name = 'nonemptystring'

    def convert(self, value, param, ctx):
        newval = super(NonEmptyStringParamType, self).convert(value, param, ctx)
        if not newval:  # None or empty string
            self.fail("Empty string is not valid!")

        return newval

    def __repr__(self):
        return 'NONEMPTYSTRING'
