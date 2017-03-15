from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.frozendict import FrozenDict
from aiida.orm.data.base import Int, Str


class TestFrozenDict(AiidaTestCase):
    def test_create(self):
        d = FrozenDict(dict={})

    def test_create_invalid(self):
        with self.assertRaises(AssertionError):
            d = FrozenDict(dict={'a': 5})

    def test_get_value(self):
        input = {'a': Int(5).store()}
        d = FrozenDict(dict=input)
        self.assertEqual(d['a'], input['a'])

    def test_iterate(self):
        input = {'a': Int(5).store(), 'b': Str('testing').store()}
        d = FrozenDict(dict=input)
        for k, v in d.iteritems():
            self.assertEqual(input[k], v)

    def test_length(self):
        input = {'a': Int(5).store(), 'b': Str('testing').store()}
        d = FrozenDict(dict=input)
        self.assertEqual(len(input), len(d))
