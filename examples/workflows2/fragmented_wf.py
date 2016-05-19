
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import threading
from aiida.workflows2.execution_engine import execution_engine
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction


def keep_ticking():
    execution_engine.tick()
    threading.Timer(10, keep_ticking()).start()

class W(FragmentedWorkfunction):
    definition = """
s1
s2
if cond1:
    s3
    s4
else:
    s5
    s6

while cond2:
    s7
    s8
s9
"""

    def s1(self):
        print "s1"
        self.ctx.v = 1

    def s2(self):
        print "s2"
        self.ctx.v = 2
        self.ctx.w = 2

    def cond1(self):
        return self.ctx.v == 3

    def s3(self):
        print "s3"

    def s4(self):
        print "s4"

    def s5(self):
        print "s5"

    def s6(self):
        print "s6"

#        f = async(slow)
#        return Wait(f)

    def cond2(self):
        return self.ctx.w < 10

    def s7(self):
        print " s7"
        self.ctx.w += 1
        print "w=", self.ctx.w

    def s8(self):
        print "s8"

    def s9(self):
        print "s9, end"


if __name__ == '__main__':
    w = W.create()
    execution_engine.submit(w, None)
    keep_ticking()
