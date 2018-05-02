.. highlight:: python
   :linenothreshold: 20

===============
AiiDA workflows
===============

The AiiDA workflow system tries to strike a balance between providing the user as much power to automate tasks while
adding features essential for carrying out high-throughput computation such as error recovery, the ability suspend and
resume, ability to run on remote resources, logging, etc.

Overview
++++++++

The workflow system allows the user to define one or more Processes that (optionally) take some inputs and (optionally)
produce some outputs.  By now, this concept should be familiar and, in fact, each time you execute a Process it
generates a :class:`~aiida.orm.implementation.general.calculation.AbstractCalculation` node along with the corresponding inputs and ouputs to keep
the provenance of what happened.

At the moment there are two ways that you can define a Process: :class:`~aiida.work.workfunctions` s or
:class:`~aiida.work.workchain.WorkChain` s.  Let's start with the former as it's the easier of the two.

Workfunctions
+++++++++++++

A workfunction is simply a python function with a decorator and a couple of constraints on its inputs and return value.
Let's dive in.

>>> from aiida.orm.data.int import Int
>>> from aiida.work.workfunctions import workfunctions as wf
>>>
>>> @wf
>>> def sum(a, b):
>>>    return a + b
>>>
>>> r = sum(Int(4), Int(5))
>>> print(r)
9
>>> r.get_inputs_dict() # doctest: +SKIP
{u'_return': <WorkCalculation: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>}
>>> r.get_inputs_dict()['_return'].get_inputs()
[4, 5]

In the above example you can see a workfunction being declare, called and then the provenance being explored.

This is a good point to highlight the constraints that workfunctions must conform to:

* All of the input parameters must be of type :class:`~aiida.orm.data.Data`
* The return value can be either

   a) a single value of type :class:`~aiida.orm.data.Data` in which case there will be a single output link with label
      ``_return``, or,
   b) a dictionary with string keys and :class:`~aiida.orm.data.Data` values where the strings are used as the label
      for the output link from the calculation.


Now, let's try making a slightly more complex workflow by composing workfunctions

>>> @wf
>>> def prod(a, b):
>>>    return a * b
>>>
>>> @wf
>>> def prod_sum(a, b, c):
>>>   return prod(sum(a, b), c)
>>>
>>> r = prod_sum(Int(2), Int(3), Int(4))
>>>
>>> from aiida.utils.ascii_vis import draw_parents
>>> draw_parents(r, dist=4) # doctest: +SKIP
                       /-4 [3582]
-- /20 [3588]prod [3587]
                      |                  /-2 [3581]
                       \5 [3586]sum [3585]
                                         \-3 [3583]

Above we see the workflow that was executed with the outputs and the PKs of all the nodes along the way.

Let's look at a slightly more complex example, that of performing an Equation of State calculation.

.. note:: The following example workflows use the Quantum ESPRESSO plugins that are hosted
  `in the aiida-quantumespresso plugin repository <https://github.com/aiidateam/aiida-quantumespresso>`_.


Here is the code::

    from aiida.orm.utils import DataFactory
    import ase

    @wf
    def rescale(structure, scale):
        the_ase = structure.get_ase()
        new_ase = the_ase.copy()
        new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
        new_structure = DataFactory('structure')(ase=new_ase)
        return new_structure

    from aiida_quantumespresso.calculations.pw import PwCalculation
    from aiida.orm.data.float import Float
    from aiida.work.run import run

    @wf
    def eos(structure, codename, pseudo_family):
        Proc = PwCalculation.process()
        results = {}
        for s in (0.98, 0.99, 1.0, 1.02, 1.04):
            rescaled = rescale(structure, Float(s))
            inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
            outputs = run(Proc, **inputs)
            res = outputs['output_parameters'].dict
            results[str(s)] = res

        return results

    eos(my_structure, Str('pw-5.1@localhost'), Str('GBRV_lda')) # doctest: +SKIP

In the above we define a workfunction to rescale a structure by some scale factors.  Then the main work is carried out
by the ``eos`` workfunction.
On line 17 we get a Process class for the Quantum ESPRESSO calculation.  This is only necessary because the Quantum
ESPRESSO plugin was written before the new plugin system hence we get a class compatible with the new system using the
``PwCalculation.process()`` call.

On line 21-23 we first use a standard python function (not shown) to get a  set of
Quantum ESPRESSO inputs parameters for our structure.  Then we use the :func:`~aiida.work.launch.run` method to launch the
calculation.  This is a blocking call and will wait until the calculation has completed.

Upon completion on lines 24-25 we get the outputs dictionary from the calculation and store it for returning when
our workfunction completes.

This way of writing the workflow is fairly straightforward and easy to read, but it does have some drawbacks, namely:

* If, say, the 4th calculation crashes, we cannot restart and continue from that point
* We do not get any output until the workfunction has completed
* Any checking of input/return values being of a specific type (beyond being :class:`~aiida.orm.data.Data`) has to be
  done manually by the user.


To overcome these problems and add additional functionality we introduced the concept of Workchains.

Workchains
++++++++++

A workchain represents a series of instructions used to carry out a process with checkpoints being taken between each
instruction such that the process can be paused/stopped/resumed, even if the computer crashes.  The most obvious
practical difference between workchains and workfunctions is that workchains are classes as opposed to functions.

Let's start by creating a workchain for the product sum workflow from before::

    from aiida.work.workchain import WorkChain

    class ProdSum(WorkChain):
        @classmethod
        def define(cls, spec):
            super(ProdSum, cls).define(spec)
            spec.outline(cls.sum, cls.prod)

        def sum(self):
            self.ctx.sum = self.inputs.a + self.inputs.b

        def prod(self):
            self.out("result", self.ctx.sum * self.inputs.c)


On lines 4-6 we see use of the ``define`` function which is used to describe the workchain.  Other than calling
the superclass which is obligatory we define the outline of our workchain by calling the corresponding method
on the spec object.  Here we have just two simple steps and between them the workchain will checkpoint.

Next on lines 9-13 we actually define what the steps do as familiar python functions.  Note on line 10 we use the inputs
which will be passed to us by the user.  We haven't explicitly stated what inputs we expect in this workflow so the user
is free to pass in anything they want (so long as it's a :class:`aiida.orm.data.Data`).

The other new concept we have used can be seen on line 10, namely ``self.ctx``.  This is known as the *context*, and
is used to store any data that should be persisted between step.  The reason for this is that each time a
step finishes a checkpoint is created, this can be used to continue in the case of a crash or suspension.
However, the checkpoint only stores data in the context and therefore any local variables are liable to disappear
between steps if the workchain is resumed.

.. note::
    context
        A data store used for variables that are used betweeen steps.


To run the workflow locally we call

>>> res = ProdSum.run(a=Int(2), b=Int(3), c=Int(4))
>>> print res
{'result': 20}
>>> draw_parents(res['result']) # doctest: +SKIP
                          /-2 [3594]
                         |
-- /20 [3598]ProdSum [3597]-3 [3596]
                         |
                          \-4 [3595]

We see that there is one output node with value 20 and the input nodes that we supplied to the calculation.
Of course the names of the inputs we supplied have to match up with those used in the workchain but we can make this
connection explicit, as well as specifying what type they should be::

    class ProdSumEx(ProdSum):
        @classmethod
        def define(cls, spec):
            super(ProdSumEx, cls).define(spec)
            spec.input('a', valid_type=Int, required=True)
            spec.input('b', valid_type=Int, required=True)
            spec.input('c', valid_type=Int, required=True)


Now the input types and their names are enforced.

>>> ProdSumEx.run(a=Int(2), b=Int(3))
TypeError: Cannot run process 'ProdSumEx' because required value was not provided for 'c'
>>> ProdSumEx.run(a=Float(2), b=Int(3), c=Int(4))
TypeError: Cannot run process 'ProdSumEx' because value 'a' is not of the right type. Got '<class 'aiida.orm.data.float.Float'>', expected '<class 'aiida.orm.data.int.Int'>'

This an example of the additional power of workchains.

Now, let's go back to the equation of state example and see what else is possible with workchains.  Let's start, as
usual, with the outline:

.. code-block:: python
    :emphasize-lines: 13

    from aiida.orm.data.structure import StructureData
    from aiida.work.workchain import while_

    class EquationOfState(WorkChain):
        @classmethod
        def define(cls, spec):
            super(EquationOfState, cls).define(spec)
            spec.input("structure", valid_type=StructureData)
            spec.input("code", valid_type=Str)
            spec.input("pseudo_family", valid_type=Str)
            spec.outline(
                cls.init,
                while_(cls.not_finished)(
                    cls.run_pw
                )
            )

Here we're using a while loop instruction, by doing this we can make sure that a checkpoint is automatically created
after each iteration.  Now all that remains is to define the contents of the steps themselves:

.. code-block:: python
    :linenos:

    def init(self):
        self.ctx.scales = (0.96, 0.98, 1., 1.02, 1.04)
        self.ctx.i = 0

    def not_finished(self):
        return self.ctx.i < len(self.ctx.scales)

    def run_pw(self):
        scale = self.ctx.scales[self.ctx.i]
        scaled = rescale(self.inputs.structure, Float(scale))

        inputs = generate_scf_input_params(
            scaled, self.inputs.code, self.inputs.pseudo_family)
        outputs = run(Proc, **inputs)
        res = outputs['output_parameters']
        self.out(str(scale), res)

        self.ctx.i += 1

This new implementation is already safer than the workfunction approach because it is checkpointed, however we can do
even better.  On line 14 we effectively call Quantum ESPRESSO to carry out the calculation which could take some time.
During this period the code waits and we cannot shutdown our computer without loosing the progress of that calculation.
To overcome this we allow the user to return special objects from a step to indicate that the workchain is
waiting for something to complete.  In the meantime the workchain can be suspended and be resumed later:

.. code-block:: python
    :linenos:
    :emphasize-lines: 19, 22

    class WaitingEquationOfState(EquationOfState):
        @classmethod
        def define(cls, spec):
            super(EquationOfState, cls).define(spec)
            spec.outline(
                cls.launch_calculations,
                cls.process_results
            )

        def launch_calculations(self):
            l = []
            for s in (0.96, 0.98, 1., 1.02, 1.04):
                scaled = rescale(self.inputs.structure, Float(s))
                inputs = generate_scf_input_params(
                    scaled, self.inputs.code, self.inputs.pseudo_family)
                pid = submit(Proc, **inputs)
                l.append(pid)

            return ToContext(s_0_96=l[0], s_0_98=l[1], s_1=l[2], s_1_02=l[3], s_1_04=l[4])

        def process_results(self):
            for key, outputs in self.ctx.iteritems():
                if key.startswith("s_"):
                    scale = key[2:].replace("_", ".")
                    self.out(Float(scale), outputs['output_parameters'].dict)


Here, on line 19 we use a so called *interstep* command.  These are objects you return from a step that can perform
actions at the end fo the step and just before the beginning of the next.  In this case we use
:data:`~aiida.work.context.ToContext`, the constructor takes keyword arguments of `[name]=[pid]`, it will then take
insert barriers into the workchain to make sure it does not continue until all of the specified processes have finished.
Then, before the next step, it will place the corresponding :class:`~aiida.orm.implementation.general.calculation.AbstractCalculation` nodes in the
specified `[name]` variables in the context.

On lines 22-25, we iterate the context looking for those entries that start with `s_` and emit the results from these
calculations.


Converting from old workflows
+++++++++++++++++++++++++++++

This section details some of the changes that need to be made to convert old workflows to the new system.

We begin with changes to the nomenclature where the rough correspondence in terms is as follows:

`workflows -> workchain`
`inline function -> workfunction`
