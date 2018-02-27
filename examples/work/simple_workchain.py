from aiida import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()


from aiida import work
from aiida.orm.data.int import Int
import aiida.work.globals as globals

persistence = globals.get_persistence()


class ProdSum(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(ProdSum, cls).define(spec)
        spec.input("a")
        spec.input("b")
        spec.input("c")
        spec.outline(cls.add, cls.prod)

    def add(self):
        self.ctx.sum = self.inputs.a + self.inputs.b

    def prod(self):
        result = self.ctx.sum * self.inputs.c
        self.out("result", result)


class ProdSumBroken(ProdSum):
    def prod(self):
        raise RuntimeError("Break")


p = ProdSumBroken(inputs={'a': Int(2), 'b': Int(3), 'c': Int(4)})
pid = p.pid
persistence.persist_process(p)
try:
    p.play()
except RuntimeError:
    pass

cp = persistence.load_checkpoint(pid)
p = ProdSum.recreate_from(cp)

p.play()

print(p.outputs)
