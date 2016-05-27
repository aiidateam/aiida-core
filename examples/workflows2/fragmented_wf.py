from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()


from aiida.workflows2.process import run
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction


class Scope(object):
    def __init__(self, *args):
        self._passed = args


class IfScope():
    def __init__(self, *commands):
        self._if = commands
        self._elif = []
        self._else = None

    def elif_(self, condition):
        commands = ElifCommands(self)
        self._elif.append((condition, commands))
        return commands

    def else_(self, *commands):
        self._else = commands


class ElifCommands(object):
    def __init__(self, if_parent):
        self._if_parent = if_parent
        self._commands = None

    def __call__(self, *commands):
        self._commands = commands
        return self._if_parent


def if_(cond):
    return IfScope


else_ = Scope


def while_(cond, *args):
    return Scope


class W(FragmentedWorkfunction):
    definition = """
s1
s2
if cond1:
    s3
    s4
elif cond3:
    s11 # <- For Mounet
else:
    s5
    s6

while cond2:
    s7
    s8
s9
"""

    @classmethod
    def defi(cls):
        """
        Another suggestion for how to define the FragmentedWorkflow.
        :return: The definition of the workflow as a tuple.
        """
        return (
                cls.start,
                cls.s2,
                if_(cls.cond1)(
                    cls.s3,
                    cls.s4,
                ).elif_(cls.cond3)(
                    cls.s11
                ).else_(
                    cls.s5,
                    cls.s6
                ),
                while_(cls.cond2)(
                    cls.s7,
                    cls.s8
                ),
                cls.s9
            )

    def start(self, ctx):
        print "s1"
        ctx.v = 1

        return 1, 2, 3, 4

    def s2(self, ctx):
        print "s2"
        ctx.v = 2
        ctx.w = 2

    def cond1(self, ctx):
        return ctx.v == 3

    def s3(self, ctx):
        print "s3"

    def s4(self, ctx):
        print "s4"

    def s5(self, ctx):
        print "s5"

    def s6(self, ctx):
        print "s6"

    #        f = async(slow)
    #        return Wait(f)

    def cond2(self, ctx):
        return ctx.w < 10

    def s7(self, ctx):
        print " s7"
        ctx.w += 1
        print "w=", ctx.w

    def s8(self, ctx):
        print "s8"

    def s9(self, ctx):
        print "s9, end"


if __name__ == '__main__':
    run(W)
