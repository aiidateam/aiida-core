from collections import Mapping
from aiida.orm.data import Data
from aiida.orm import load_node


class FrozenDict(Data, Mapping):
    """
    An immutable dictionary containing only Data nodes as values.

    .. note::
        All values must be stored before being passed to constructor.
    """
    def __init__(self, dict, **kwargs):
        super(FrozenDict, self).__init__(**kwargs)
        for value in dict.itervalues():
            assert isinstance(value, Data)
            assert value.is_stored

        for k, v in dict.iteritems():
            self._set_attr(k, v.pk)

        self._cache = {}

    def __getitem__(self, key):
        return self._get(key)

    def __iter__(self):
        return self.get_attrs().iterkeys()

    def __len__(self):
        return len(self.get_attrs())

    def _get(self, key):
        val = self._cache.get(key, None)
        if val is None:
            val = load_node(self.get_attr(key))
            self._cache[key] = val
        return val