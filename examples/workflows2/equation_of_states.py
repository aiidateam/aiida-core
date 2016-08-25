from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import load_node
from aiida.orm.utils import DataFactory
from aiida.workflows2.db_types import make_float, make_str, NumericType, SimpleData
from aiida.orm.code import Code
from aiida.orm.data.structure import StructureData
from aiida.workflows2.run import run, asyncd
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, \
    ResultToContext, while_
from examples.workflows2.diamond_fcc import rescale
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.workflows2.wf import wf

# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")


PwProcess = PwCalculation.process()

@wf
def rescale(structure, scale):
    """
    Workfunction to rescale a structure

    :param structure: An AiiDA structure to rescale
    :param scale: The scale factor
    :return: The rescaled structure
    """
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return new_structure


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


def generate_scf_input_params(structure, codename, pseudo_family):
    # The inputs
    inputs = PwCalculation.process().get_inputs_template()

    # The structure
    inputs.structure = structure

    inputs.code = Code.get_from_string(codename.value)
    inputs._options.resources = {"num_machines": 1}
    inputs._options.max_wallclock_seconds = 30 * 60

    # Kpoints
    KpointsData = DataFactory("array.kpoints")
    kpoints = KpointsData()
    kpoints_mesh = 2
    kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
    inputs.kpoints = kpoints

    # Calculation parameters
    parameters_dict = {
        "CONTROL": {"calculation": "scf",
                    "tstress": True,  #  Important that this stays to get stress
                    "tprnfor": True,},
        "SYSTEM": {"ecutwfc": 30.,
                   "ecutrho": 200.,},
        "ELECTRONS": {"conv_thr": 1.e-6,}
    }
    ParameterData = DataFactory("parameter")
    inputs.parameters = ParameterData(dict=parameters_dict)

    # Pseudopotentials
    inputs.pseudo = get_pseudos(structure, str(pseudo_family))

    return inputs


class EquationOfState(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("structure", valid_type=StructureData)
        spec.input("start", valid_type=NumericType, default=make_float(0.96))
        spec.input("delta", valid_type=NumericType, default=make_float(0.02))
        spec.input("end", valid_type=NumericType, default=make_float(1.04))
        spec.input("code", valid_type=SimpleData)
        spec.input("pseudo_family", valid_type=SimpleData)
        spec.outline(
            cls.run_pw,
            cls.print_eos
        )

    def run_pw(self, ctx):
        calcs = {}

        scale = self.inputs.start
        while scale <= self.inputs.end:
            scaled = rescale(self.inputs.structure, scale)

            inputs = generate_scf_input_params(
                scaled, self.inputs.code, self.inputs.pseudo_family)

            # Launch the code
            future = self.submit(PwProcess, inputs)
            #print scale.value, future.pid
            # Store the future
            calcs["s_{}".format(scale)] = future
            scale = scale.value + self.inputs.delta.value

        # Ask the workflow to continue when the results are ready and store them
        # in the context
        return ResultToContext(**calcs)

    def print_eos(self, ctx):
        for label in ctx:
            if "s_" in label:
                print "{} {}".format(
                    label, ctx[label]['output_parameters'].dict.energy)


class EquationOfState2(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("structure", valid_type=StructureData)
        spec.input("code", valid_type=SimpleData)
        spec.input("pseudo_family", valid_type=SimpleData)
        spec.outline(
            cls.init,
            while_(cls.not_finished)(
                cls.run_pw,
                cls.print_result
            )
        )

    def init(self, ctx):
        ctx.scales = (0.96, 0.98, 1., 1.02, 1.04)
        ctx.i = 0

    def not_finished(self, ctx):
        return ctx.i < len(ctx.scales)

    def run_pw(self, ctx):
        scale = ctx.scales[ctx.i]
        scaled = rescale(self.inputs.structure, scale)

        inputs = generate_scf_input_params(
            scaled, self.inputs.code, self.inputs.pseudo_family)

        # Launch the code
        calc = self.submit(PwProcess, inputs)

        ctx.i += 1
        return ResultToContext(result=calc)

    def print_result(self, ctx):
        print ctx.scales[ctx.i],\
            ctx.result['output_parameters'].dict.energy


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Equation of states example.')
    parser.add_argument('--structure', type=int, dest='structure_pk',
                        help='The structure pk to use.', required=True)
    parser.add_argument('--range', type=str, dest='range',
                        help='The scale range of the equation of states '
                             'calculation written as [start]:[end]:[delta]',
                             default='0.96:1.04:0.02')
    parser.add_argument('--pseudo', type=str, dest='pseudo',
                        help='The pseudopotential family', required=True)
    parser.add_argument('--code', type=str, dest='code',
                        help='The codename to use', required=True)

    args = parser.parse_args()
    start, end, delta = args.range.split(':')

    # Get the structure from the calculation
    # run(EquationOfStates, structure=load_node(args.structure_pk),
    #     start=Float(start), end=Float(end), delta=Float(delta),
    #     code=Str(args.code), pseudo_family=Str(args.pseudo))
    asyncd(EquationOfState, structure=load_node(args.structure_pk),
           start=make_float(start), end=make_float(end), delta=make_float(delta),
           code=make_str(args.code), pseudo_family=make_str(args.pseudo))


