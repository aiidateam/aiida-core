
from aiida.workflows2.wf import wf
from aiida.orm import load_node
from aiida.orm.utils import DataFactory
from aiida.workflows2.db_types import Float
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.orm.code import Code
from aiida.orm.data.structure import StructureData
from aiida.workflows2.run import async
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, while_,\
    ResultToContext


# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")


def get_pseudos(structure, family_name):
    """
    Set the pseudo to use for all atomic kinds, picking pseudos from the
    family with name family_name.

    :note: The structure must already be set.

    :param family_name: the name of the group containing the pseudos
    """
    from collections import defaultdict
    from aiida.orm.data.upf import get_pseudos_from_structure

    # A dict {kind_name: pseudo_object}
    kind_pseudo_dict = get_pseudos_from_structure(structure, family_name)

    # We have to group the species by pseudo, I use the pseudo PK
    # pseudo_dict will just map PK->pseudo_object
    pseudo_dict = {}
    # Will contain a list of all species of the pseudo with given PK
    pseudo_species = defaultdict(list)

    for kindname, pseudo in kind_pseudo_dict.iteritems():
        pseudo_dict[pseudo.pk] = pseudo
        pseudo_species[pseudo.pk].append(kindname)

    pseudos = {}
    for pseudo_pk in pseudo_dict:
        pseudo = pseudo_dict[pseudo_pk]
        kinds = pseudo_species[pseudo_pk]
        for kind in kinds:
            pseudos[kind] = pseudo

    return pseudos


@wf
def rescale(structure, scale):
    """
    Inline calculation to rescale a structure

    :param structure: An AiiDA structure to rescale
    :param scale: The scale factor
    :return: a dictionary of the form {'rescaled_structure': rescaled_structure}
    """
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * scale.value, scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return {'rescaled_structure': new_structure}


class EquationOfStates(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("structure", type=StructureData)
        spec.input("start", type=Float)
        spec.input("delta", type=Float)
        spec.input("end", type=Float)
        spec.input("code", type=Code)
        spec.inputs("pseudo_family")
        spec.outline(
            cls.init,
            while_(cls.not_finished)(
                cls.run_pw,
                cls.up_scale
            ),
            cls.plot_eos
        )

    def init(self, ctx):
        ctx.scale = self.inputs.start
        ctx.results = {}

    def not_finished(self, ctx):
        return ctx.scale < self.inputs.end

    def run_pw(self, ctx):
        result_dict = rescale(self.inputs.structure, ctx.scale)

        JobCalc = PwCalculation.process()
        inputs = JobCalc.get_inputs_template()

        # Calculation parameters
        parameters_dict = {
            u'CONTROL': {
                u'calculation': u'scf',
                u'max_seconds': 3492,
                u'restart_mode': u'from_scratch',
                u'tstress': False},
            u'ELECTRONS': {u'conv_thr': 1e-06},
            u'SYSTEM': {
                u'ecutrho': 200.0,
                u'ecutwfc': 30.0
            }
        }
        inputs.parameters = ParameterData(dict=parameters_dict)

        # Kpoints
        inputs.kpoints = KpointsData()
        inputs.kpoints.set_kpoints_mesh([4, 4, 4])

        inputs.code = inputs.code
        inputs.structure(result_dict['rescaled_structure'])
        inputs.pseuso = get_pseudos(inputs.structure, inputs.pseudo_family)

        # Submission options
        inputs._options.resources({"num_machines": 1})
        inputs._options.max_wallclock_seconds(30 * 60)

        fut = self.submit(JobCalc, inputs)
        print ctx.scale.value, fut.pid

        context_assign(r1=result(f1, f2).structure)

        ctx.results[ctx.scale.value] = fut

    def up_scale(self, ctx):
        ctx.scale = ctx.scale + self.inputs.delta

    def plot_eos(self, ctx):
        pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Equation of states example.')
    parser.add_argument('--structure', type=int, dest='structure_pk',
                        help='The structure pk to use.')
    parser.add_argument('--range', type=str, dest='range',
                        help='The scale range of the equation of states '
                             'calculation written as [start]:[end]:[delta]',
                             default='0.96:0.1.04:0.02')
    parser.add_argument('--pseudo', type=str, dest='pseudo',
                        help='The pseudopotential family')
    parser.add_argument('--code', type=str, dest='code',
                        help='The codename to use')

    args = parser.parse_args()
    start, end, delta = args.range.split(':')

    # Get the structure from the calculation
    EquationOfStates.run(inputs={
        'structure': load_node(args.structure_pk),
        'start': Float(start),
        'end': Float(end),
        'delta': Float(delta),
        'code': Code.get_from_string(args.code),
        'pseudo_family': args.pseudo
    })
