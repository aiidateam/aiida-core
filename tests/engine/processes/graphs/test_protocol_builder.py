###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Optional upstream protocol integration, without running a PW calculation."""

import pytest

from aiida import orm
from aiida.engine import graph_execution, task_from_builder
from aiida.engine.processes.graphs.process import launched_as
from aiida.engine.processes.graphs.run import GraphRun
from aiida.engine.utils import instantiate_process

pytest.importorskip('aiida_quantumespresso')
pytest.importorskip('plumpy')  # Released QE still imports this optional compatibility dependency.


@pytest.mark.requires_broker
@pytest.mark.parametrize('explicit_pseudos', [False, True])
def test_pw_protocol_family_inputs(aiida_code_installed, aiida_manager, tmp_path, monkeypatch, explicit_pseudos):
    from aiida_pseudo.groups.family import SsspFamily
    from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain

    # Released QE still uses the old code base-class name. This test-only alias
    # leaves protocol selection and process port validation untouched.
    if not hasattr(orm, 'AbstractCode'):
        monkeypatch.setattr(orm, 'AbstractCode', orm.Code, raising=False)

    (tmp_path / 'Si.upf').write_text('<UPF version="2.0.1"><PP_HEADER element="Si" z_valence="4.0" /></UPF>')
    family = SsspFamily.create_from_folder(
        tmp_path, f'SSSP/1.3/PBEsol/{"precision" if explicit_pseudos else "efficiency"}'
    )
    family.set_cutoffs({'Si': {'cutoff_wfc': 30.0, 'cutoff_rho': 240.0}}, 'standard', unit='Ry')
    code = aiida_code_installed(default_calc_job_plugin='quantumespresso.pw', filepath_executable='/bin/true')
    structure = orm.StructureData(cell=[[5, 0, 0], [0, 5, 0], [0, 0, 5]])
    structure.append_atom(position=(0, 0, 0), symbols='Si')
    overrides = {'pseudo_family': family.label}
    if explicit_pseudos:
        overrides['pw'] = {
            'pseudos': family.get_pseudos(structure=structure),
            'parameters': {'SYSTEM': {'ecutwfc': 44.0, 'ecutrho': 352.0}},
        }
    builder = PwBaseWorkChain.get_builder_from_protocol(
        code=code, structure=structure, protocol='moderate', overrides=overrides
    )

    def forbidden(*args, **kwargs):
        pytest.fail('Adapting or replacing inputs must not rerun protocol preparation')

    monkeypatch.setattr(PwBaseWorkChain, 'get_builder_from_protocol', forbidden)
    builder.metadata.label = 'protocol child'
    adapted = task_from_builder(builder)

    @graph_execution
    def protocol_graph():
        return adapted().remote_folder

    launch = protocol_graph.get_launch_inputs()
    body = protocol_graph.build()
    given = {**launch['graph_inputs'], **launch.get('graph_bindings', {})}
    (start,) = GraphRun(graph=body, given=given).step().starts
    process_class, inputs = launched_as(start)
    child = instantiate_process(aiida_manager.get_runner(), process_class, **inputs)
    assert child.node.label == 'protocol child'
    assert child.node.inputs.pw.code.uuid == code.uuid
    assert child.node.inputs.pw.structure.uuid == structure.uuid
    assert child.node.inputs.pw.pseudos.Si.uuid == builder.pw.pseudos['Si'].uuid
    assert child.node.inputs.pw.parameters.uuid == builder.pw.parameters.uuid
    assert builder.pw.parameters.get_dict()['SYSTEM']['ecutwfc'] == (44.0 if explicit_pseudos else 30.0)
    assert (
        child.inputs.pw.metadata.options.resources['num_machines']
        == builder.pw.metadata.options.resources['num_machines']
    )
    assert child.inputs.pw.metadata.options.max_wallclock_seconds == builder.pw.metadata.options.max_wallclock_seconds
    assert child.inputs.clean_workdir == builder.clean_workdir
    assert not child.node.inputs.pw.pseudos.Si.base.links.get_incoming().all()
