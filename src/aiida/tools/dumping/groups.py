# Could also be a more general CollectionDumper class, actually
from aiida.common import timezone
# from aiida.common.utils import str_timedelta

class GroupDumper:
    def __init__(self) -> None:
        self.timestamp = None

    def dump(self, groups):
        self.timestamp = timezone.now()
        for group in groups:
            self._dump_group(group=group)


    def _dump_group(self, group):
        pass

