from click.types import StringParamType


class NonemptyStringParamType(StringParamType):
    name = 'nonemptystring'

    def convert(self, value, param, ctx):
        newval = super(StringParamType, self).convert(value, param, ctx)
        if not newval:  # None or empty string
            self.fail("Empty string is not valid!")
        return newval

    def __repr__(self):
        return 'NONEMPTYSTRING'
