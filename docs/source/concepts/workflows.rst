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

Exposing inputs and outputs
---------------------------

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

Next, we will see how a more complex parent workchain can be created by using the additional features of the expose functionality. The following workchain launches two children. These children share the input ``a``, but have different ``b`` and ``c``. The output ``e`` will be taken only from the first child, whereas ``d`` and ``f`` are taken from both children. In order to avoid name conflicts, we need to create a *namespace* for each of the two children, where the inputs and outputs which are not shared are stored. Our goal is that the workflow can be called as follows:

.. include:: expose_examples/run_complex.py
    :code: python

This is achieved by the following workflow. In the next section, we will explain each of the steps.

.. include:: expose_examples/complex_parent.py
    :code: python

First of all, we want to expose the ``a`` input and the ``e`` output at the top-level. For this, we again use :meth:`.expose_inputs` and :meth:`.expose_outputs`, but with the optional keyword ``include``. This specifies a list of keys, and only inputs or outputs which are in that list will be exposed. So by passing ``include=['a']`` to :meth:`.expose_inputs`, only the input ``a`` is exposed.

Additionally, we want to expose the inputs ``b`` and ``c`` (outputs ``d`` and ``f``), but in a namespace specific for each of the two children. For this purpose, we pass the ``namespace`` parameter to the expose functions. However, since we now shouldn't expose ``a`` (``e``) again, we use the ``exclude`` keyword, which specifies a list of keys that will not be exposed.

When calling the children, we again use the :meth:`.Process.exposed_inputs` method to forward the exposed inputs. Since the inputs ``b`` and ``c`` are now in a specific namespace, we need to pass this namespace as an additional parameter. By default, :meth:`.exposed_inputs` will search through all the parent namespaces of the given namespace to search for input, as shown in the call for ``child_1``. If the same input key exists in multiple namespaces, the input in the lowest namespace takes precedence. It's also possible to disable this behavior, and instead search only in the explicit namespace that was passed. This is done by setting ``agglomerate=False``, as shown in the call to ``child_2``. Of course, we then need to explicitly pass the input ``a``.

Finally, we use :meth:`.exposed_outputs` and :meth:`.out_many` to forward the outputs of the children to the outputs of the parent. Again, the ``namespace`` and ``agglomerate`` options can be used to select which outputs are returned by the :meth:`.exposed_outputs` method.
