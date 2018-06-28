from click.types import StringParamType


class ShebangParamType(StringParamType):
    name = 'shebangline'

    def convert(self, value, param, ctx):
        newval = super(ShebangParamType, self).convert(value, param, ctx)
        if newval is None:
            return None
        if not newval.startswith('#!'):
            self.fail('The shebang line should start with the two caracters #!')
        return newval

    def __repr__(self):
        return 'SHEBANGLINE'
