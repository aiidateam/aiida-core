"""Test the caching functionality for a :class:`aiida.engine.processes.process.Process`."""

from aiida.engine import Process, run
from aiida.manage import enable_caching
from aiida.orm import CalcJobNode, Int


class NestedOutputsProcess(Process):
    """Process with dynamic nested output namespace."""

    _node_class = CalcJobNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('a')
        spec.output_namespace('nested', dynamic=True)

    async def run(self):
        self.out('nested', {'a': self.inputs.a + 2})


def test_caching_nested_output_namespace():
    """Test that caching from a process with a nested output namespace works."""
    _, node_original = run.get_node(NestedOutputsProcess, a=Int(1))
    assert not node_original.base.caching.is_created_from_cache

    with enable_caching():
        _, node_clone = run.get_node(NestedOutputsProcess, a=Int(1))

    assert node_clone.base.caching.is_created_from_cache
    assert node_clone.base.caching.get_cache_source() == node_original.uuid

    outputs = node_clone.base.links.get_outgoing().nested()
    assert list(outputs.keys()) == ['nested']
    assert list(outputs['nested'].keys()) == ['a']
    assert isinstance(outputs['nested']['a'], Int)
