"""
Module for shebang custom click type
"""

from click.types import StringParamType


class ShebangParamType(StringParamType):
    """
    Custom click param type for shbang line
    """
    name = 'shebangline'

    def convert(self, value, param, ctx):
        newval = super(ShebangParamType, self).convert(value, param, ctx)
        if newval is None:
            return None
        if not newval.startswith('#!'):
            self.fail('The shebang line should start with the two caracters #!, it is instead: {}'.format(newval))
        return newval

    def __repr__(self):
        return 'SHEBANGLINE'
