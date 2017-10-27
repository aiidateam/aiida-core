from aiida.orm.data.base import Int
from aiida.work.run import submit
from aiida.work.workchain import WorkChain, ToContext, append_

class ParentWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(ParentWorkChain, cls).define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(
            cls.run,
            cls.results
        )
        spec.output('output', valid_type=Int, required=True)

    def run(self):
        inputs = {
            'inp': self.inputs.inp
        }
        running = submit(SubWorkChain, **inputs)
        self.report('launching SubWorkChain<{}>'.format(running.pid))

        return ToContext(workchains=append_(running))

    def results(self):
        subworkchain = self.ctx.workchains[0]
        self.out('output', subworkchain.out.output)

class SubWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SubWorkChain, cls).define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(
            cls.run
        )
        spec.output('output', valid_type=Int, required=True)

    def run(self):
        self.out('output', Int(self.inputs.inp.value * 2))