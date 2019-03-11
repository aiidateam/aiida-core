"""Tools to operate on `TrajectoryData` nodes."""
from __future__ import absolute_import

from aiida.engine import calcfunction


@calcfunction
def _get_aiida_structure_inline(trajectory, parameters):
    """
    Creates :py:class:`aiida.orm.nodes.data.structure.StructureData` using ASE.

    .. note:: requires ASE module.
    """
    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    if 'index' not in kwargs.keys() or kwargs['index'] is None:
        raise ValueError("Step index is not supplied for TrajectoryData")
    return {'structure': trajectory.get_step_structure(**kwargs)}
