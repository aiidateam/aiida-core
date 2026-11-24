"""Test the caching functionality for a :class:`aiida.engine.processes.process.Process`."""

from aiida.engine import Process, calcfunction, run
from aiida.manage import enable_caching
from aiida.orm import Bool, CalcJobNode, Int


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


@calcfunction
def emit_alphas(namespaced):
    """Emit ``alphas`` as a namespace or as a leaf, from the same process class."""
    if namespaced.value:
        return {'alphas': {'filled': Int(1)}}
    return {'alphas': Int(2)}


def test_caching_replay_keeps_class_spec():
    """Replaying the outputs of a cached node must not add ports to the spec shared by the process class.

    On a cache hit, the outputs of the cache source are emitted again under their port paths (``alphas.filled``).
    If that created the ``alphas`` namespace on the class-level spec, a later run of the same class emitting
    ``alphas`` as a leaf would fail output validation.

    Regression test for https://github.com/aiidateam/aiida-core/issues/7504
    """
    spec_outputs = emit_alphas.process_class.spec().outputs
    assert 'alphas' not in spec_outputs

    _, node_original = emit_alphas.run_get_node(namespaced=Bool(True))

    with enable_caching():
        _, node_clone = emit_alphas.run_get_node(namespaced=Bool(True))

    assert node_clone.base.caching.is_created_from_cache
    assert node_clone.base.caching.get_cache_source() == node_original.uuid
    assert node_clone.base.links.get_outgoing().nested()['alphas']['filled'].value == 1
    assert 'alphas' not in spec_outputs

    _, node_leaf = emit_alphas.run_get_node(namespaced=Bool(False))
    assert node_leaf.is_finished_ok
    assert node_leaf.outputs.alphas.value == 2
