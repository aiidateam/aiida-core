.. _workflows:

*********
Workflows
*********

Workflows are a central concept in AiiDA that allow you to string together multiple calculations that encodes the logic of a typical scientific workflow.
In this section, we explain what workflows are, how they can be used and run.
Finally, we will detail some best practices when designing workflows.


Workchains and workfunctions
============================

At the core of a workflow, is the logic that defines the sequence of calculations that need to be executed to get from the initial inputs to the desired final answer.
The way to encode this workflow logic in AiiDA, are workchains and workfunctions.
By chaining workchains and workfunctions together, that each can run calculations within them, we can define a workflow.

ISSUE#1127


Running workflows
=================

Workfunctions can be run directly, workchains need to be run through a ``runner``.
The easiest way is to use the ``ProcessBuilder`` (see :ref:`this section<process_builder>`).

ISSUE#1128


Monitoring workflows
====================

ISSUE#1129


Workflow development
====================

ISSUE#1130

.. _expose_inputs_outputs:

Modular workflows: exposing inputs and outputs
----------------------------------------------

When creating complex workflows, it is a good idea to split them up into smaller, modular parts. At the lowest level, each workflow should perform exactly one task. These workflows can then be wrapped together by a "parent" workflow to create a larger logical unit.

In order to make this approach manageable, it needs to be as simple as possible to glue together multiple workflows in a larger parent workflow. For this reason, AiiDA provides the *expose* functionality, which will be explained here.

Consider the following example workchain, which simply takes a few inputs and returns them again as outputs:

.. include:: expose_examples/child.py
    :code: python

As a first example, we will implement a thin wrapper workflow, which simply forwards its inputs to ``ChildWorkChain``, and forwards the outputs of the child to its outputs:

.. include:: expose_examples/simple_parent.py
    :code: python

In the ``define`` method of this simple parent workchain, we use the :meth:`.expose_inputs` and :meth:`.expose_outputs`. This creates the corresponding input and output ports in the parent workchain.

Additionally, AiiDA remembers which inputs and outputs were exposed from that particular workchain class. This is used when calling the child in the ``run_child`` method. The :meth:`.Process.exposed_inputs` method returns a dictionary of inputs that the parent received which were exposed from the child, and so it can be used to pass these on to the child.

Finally, in the ``finalize`` method, we use :meth:`.Process.exposed_outputs` to retrieve the outputs of the child which were exposed to the parent. Using :meth:`.out_many`, these outputs are added to the outputs of the parent workchain.

This workchain can now be run in exactly the same way as the child itself:

.. include:: expose_examples/run_simple.py
    :code: python



.. include:: expose_examples/complex_parent.py
    :code: python

.. include:: expose_examples/run_complex.py
    :code: python
