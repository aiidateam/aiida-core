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

Exposing inputs and outputs
---------------------------

.. include:: expose_examples/child.py
    :code: python

.. include:: expose_examples/simple_parent.py
    :code: python

.. include:: expose_examples/run_simple.py
    :code: python

.. include:: expose_examples/complex_parent.py
    :code: python

.. include:: expose_examples/run_complex.py
    :code: python
