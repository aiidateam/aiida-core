# TODO this class needs to be removed

from aiida.engine import ToContext, WorkChain
from aiida.orm import Bool


class MainWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('kill', default=lambda: Bool(False))
        spec.outline(cls.submit_child, cls.check)

    def submit_child(self):
        return ToContext(child=self.submit(SubWorkChain, kill=self.inputs.kill))

    def check(self):
        raise RuntimeError('should have been aborted by now')


class SubWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('kill', default=lambda: Bool(False))
        spec.outline(cls.begin, cls.check)

    def begin(self):
        """If the Main should be killed, pause the child to give the Main a chance to call kill on its children"""
        if self.inputs.kill:
            self.pause()

    def check(self):
        raise RuntimeError('should have been aborted by now')
