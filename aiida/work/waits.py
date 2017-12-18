__all__ = ['LegacyWorkflow']


class Wait(object):
    pass


class LegacyWorkflow(Wait):
    def __init__(self, pk):
        self.pk = pk
