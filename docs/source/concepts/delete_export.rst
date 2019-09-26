.. _delete_export:

*****************
Delete and Export
*****************

Because of the very nature of scientific research, it becomes indispensable to be able to both delete parts of a database (e.g., if errors are made, inputs are misspelled, or useless calculations are performed) or export it (for collaboration or publication purposes).
Both these features have one aspect in common: they can easily lead to a provenance graph with incomplete information.
To better understand why, let's take a look at the following basic provenance graph:

.. _delexp_example01a:
.. figure:: include/images/delexp_example01a.png

Even in this simple case, if we were to export only the calculation node and the output data node (or, equivalently, delete just the input data node), then we would have lost part of the critical information needed to run the calculation (the |D_1| node), thus losing the reproducibility of the calculation |C_1|.
In this simple case, therefore, in order to have a consistent provenance, whenever you export a calculation node you must also import *all* of its input nodes (or, symmetrically, whenever you delete a data node you must also delete all calculations that used it as an input).

This is just one of the many rules that must be considered when trying to manually edit a provenance database.
The key message to remember is that AiiDA will not only delete or export the nodes explicitly targeted by the user, but will also include any other nodes that are needed for keeping a consistent provenance in the resulting database.

It is also worth noting that if you do successive exports of partial information, AiiDA will be able to reconstruct links that might have been broken when dividing the data for export.
So if you first where to export the previous graph, and then you exported the next section of your full database:

.. _delexp_example01b:
.. figure:: include/images/delexp_example01b.png

Then AiiDA will be able to automatically identfy the shared node |D_2| and connect both sections back together during the import process.
For this kind of recognition it doesn't matter which subgraph was exported first.

In the following section we will explain in more detail the criteria for including other nodes and the corresponding traversal rules.


Traversal Rules
===============

When you run ``verdi node delete [NODE_IDS]`` or ``verdi export create -N [NODE_IDS]``, AiiDA will look at the links incoming or outgoing from the nodes that you specified and decide if there are other nodes that are critical to keep.

For this decision, it is not only important to consider the type of link, but also if we are following it along its direction (we will call this ``forward`` direction) or in the reversed direction (``backward`` direction).
To clarify this, in the example above, when deleting data node |D_1|, AiiDA will follow the ``input_calc`` link in the ``forward`` direction (in this case, it will decide that the linked node (|C_1|) must then also be deleted).
If the initial target node was, instead, |C_1| the ``input_calc`` link would be followed in the ``backward`` direction (and in this case the node |D_1| will not be deleted, as we will explain below).

This process will be repeated recursively for every node that has just been included for deletion or export, until no more nodes need to be added.
The rules defining whether a linked node should be added or not to the delete/export list (based on the kind and direction of the link) are called *traversal rules*.
In the following section we will describe these rules both for the export and delete procedures.

The tables below are grouped according to the type of nodes and links involved.
We also provide illustrations of the cases considered, where the encircled node is the one being targeted, and the other node (to which the red arrow is pointing) is the one that is being considered for addition into the delete/export list.

Data and Calculation Nodes
--------------------------

The first example above already discusses the case of deleting an input node: in this case, it is necessary to also delete any calculation that uses it as an input.

In AiiDA, we apply the same criterion also when deleting an output: in this case, we follow the ``create`` link in the ``backward`` direction and we mark for deletion also the calculation that created it.
The reason for this is that a calculation with missing outputs could be misleading. For instance, some calculations produce optional outputs depending on the combination of input flags that are used.
A missing output might be interpreted as if that piece of information was not computed by the calculation.
In the case of export, the rules are typically the reverse of those used for deletion.
Therefore, in this case, the folowing rule applies: when exporting a calculation node, all its input data nodes and created output nodes must be exported as well.

On the other hand, when exporting a data node, users typically do not need to also export all the calculations that used it as an input.
These may represent further work that, by default, does not need to be exported as well (unless explicitly specified by the user in the list of nodes).
Equivalently, when deleting a calculation, one typically wants to keep its inputs, as they might be used by other unrelated calculations.

What should happen instead for the outputs of a calculation to be deleted?
Often, one might want to delete (recursively) all the outputs generated by it.
However, we leave the option to users to just delete the calculation, keeping its outputs in the database.
While we emphasize that this operation removes all provenance information for the output nodes, there are cases in which this is useful or even needed (removal of inputs that are protected by copyright, or creating a smaller export file to transfer to collaborators who want to work with the output data).

+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| Illustrative diagram (explicitly targeted     | Name of Rule            | Behavior when exporting target node                 | Behavior when deleting target node                 |
| node is encircled)                            |                         |                                                     |                                                    |
+===============================================+=========================+=====================================================+====================================================+
| .. image:: include/images/delexp_caseDC1.png  | ``input_calc_forward``  | - Default Value: ``False``                          | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **won't** be exported **by default**. | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseDC2.png  | ``input_calc_backward`` | - Fixed Value: ``True``                             | - Fixed Value: ``False`` [#f01]_                   |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **will never** be deleted.           |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseCD1.png  | ``create_forward``      | - Fixed Value: ``True``                             | - Default Value: ``True``                          |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **will** be deleted **by default**.  |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseCD2.png  | ``create_backward``     | - Default Value: ``True``.                          | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **will** be exported **by default**.  | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+

.. [#f01]
   Although we provide the option to automatically export all calculations that use as input any targeted data node (by specifying ``input_calc_forward=True``) we *currently* do not provide the reciprocal option to delete all the data node inputs when targetting calculation nodes.
   This is mainly for the potential danger that would imply automatically enabling upwards traversal of the data provenance when deleting, which would make it extremely hard to predict or control the nodes that will be ultimately affected.


Data and Workflow Nodes
-----------------------

The behavior when considering ``input_work`` links is exactly the same as when considering ``input_calc`` links for the same reasons.
The case for ``return`` links is partially similar to the one for ``create`` one.
Indeed, it isn't desirable to have a resulting database with missing outputs, so when exporting a workflow the returned data nodes will also be included (and when deleting a data node, the returning workflow will also be removed).
However, when exporting a returned node, the default behavior is *not* to include the logical provenance of the workflows that returned it (equivalently, when targeting a workflow node for deletion, the algorithm will not traverse the ``return`` links to include also the returned data nodes - actually, this goal can be achieved in a different way following instead ``call`` and ``create`` links, as explained below).

+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| Illustrative diagram (explicitly targeted     | Name of Rule            | Behavior when exporting target node                 | Behavior when deleting target node                 |
| node is encircled)                            |                         |                                                     |                                                    |
+===============================================+=========================+=====================================================+====================================================+
| .. image:: include/images/delexp_caseDW1.png  | ``input_work_forward``  | - Default Value: ``False``                          | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **won't** be exported **by default**. | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseDW2.png  | ``input_work_backward`` | - Fixed Value: ``True``                             | - Fixed Value: ``False``                           |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **will never** be deleted.           |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseWD1.png  | ``return_forward``      | - Fixed Value: ``True``                             | - Fixed Value: ``False`` [#f02]_                   |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **will never** be deleted.           |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseWD2.png  | ``return_backward``     | - Default Value: ``False``.                         | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **won't** be exported **by default**. | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+

.. [#f02]
   The reason to prevent the deletion of returned data nodes is that, since the logical provenance can be cyclical, this might end up deleting inputs and thus propagating the deletion process to other unrelated parts of the database.
   In most cases where you will want to delete a returned data node, you will be able to do so by setting ``call_calc_forward=True`` (see below) and ``create_forward=True`` (which is the default value).



Workflows and Calculation Nodes
-------------------------------

Finally, we will consider the possible (call) links between processes.
The results of a parent workflow depend critically on the subworkflows or calculations launched by it; therefore, in AiiDA when exporting a Workflow node we always traverse its ``forward`` ``call`` links (both ``call_calc`` and ``call_work``).
Analogously, when deleting a process, the parent workflow that has called it (if present) will be deleted as well (by traversing a ``backward`` ``call_calc`` or ``call_work`` link).
Since the traversal rules are applied recursively, this means that also the caller of the caller of the process will be deleted, and so on.

The possibility to follow ``call`` links in the other direction is available to the users,but disabled by default, i.e., when you export a process you will not necessarily export the logical provenance of the workflows calling it, and when deleting a workflow you won't necessarily delete all its subworkflows and called calculations.

+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| Illustrative diagram (explicitly targeted     | Name of Rule            | Behavior when exporting target node                 | Behavior when deleting target node                 |
| node is encircled)                            |                         |                                                     |                                                    |
+===============================================+=========================+=====================================================+====================================================+
| .. image:: include/images/delexp_caseWC1.png  | ``call_calc_forward``   | - Fixed Value: ``True``                             | - Default Value: ``False`` [#f03]_                 |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **won't** be deleted **by default**. |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseWC2.png  | ``call_calc_backward``  | - Default Value: ``False``                          | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **won't** be exported **by default**. | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseWW1.png  | ``call_work_forward``   | - Fixed Value: ``True``                             | - Default Value: ``False``  [#f03]_                |
|    :scale: 60%                                |                         | - Linked node **will always** be exported.          | - Linked node **won't** be deleted **by default**. |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+
| .. image:: include/images/delexp_caseWW2.png  | ``call_work_backward``  | - Default Value: ``False``.                         | - Fixed Value: ``True``                            |
|    :scale: 60%                                |                         | - Linked node **won't** be exported **by default**. | - Linked node **will always** be deleted.          |
+-----------------------------------------------+-------------------------+-----------------------------------------------------+----------------------------------------------------+

.. [#f03]
   One should be extremely careful when enabling these options since this will not only enable the deletion of the subprocesses of the targeted workflow, but it will also delete all processes called by any of the parent processes of the targeted workflow.
   We will further illustrate this behavior below.


Cascading rules: an example
===========================

In the previous sections we have described the basic rules used by AiiDA to decide which nodes should also be included from an initial list of nodes to delete or export.
These rules are applied recursively: as new nodes are included in the deletion (or export)list, the rules are applied to them as well until no new nodes are included.
Therefore, the consequence of using these features on a given set of nodes may not always be straightforward, and the final set might include more nodes than naively expected.

Let us first focus on the data provenance only (i.e., only ``input_calc`` and ``create`` links). The following two rules apply when going in the ``forward`` direction:

* If you delete a data node, any calculation that uses it as input will *always* be deleted as well (``input_calc_forward=True``).
* If you delete a calculation node, any output data node will be deleted *by default* (``create_forward=True``).

The consequence of these two together is a "chain reaction" in which every node that can be traced back through the data provenance to any of the initial targeted nodes will end up being deleted as well.
The reciprocal is true for the export: the default behavior is that every ancestor will also be exported by default (because ``create_backward`` is ``True`` by default and ``input_calc_backward`` is always ``True``).

On the other hand, when considering the connection between data provenance and logical provenance, it is important to notice that, by default, AiiDA will always prioritize the former over the latter.
Thus, it will protect data nodes and calculation nodes when deleting workflow nodes, and it will leave behind workflow nodes when exporting data nodes or calculation nodes.

Enabling the optional rules in these cases overrides this default behavior.
To better illustrate this, we consider the following graph and we focus on the deletion feature only (similar considerations apply when exporting):

.. _delexp_example02:
.. image:: include/images/delexp_example02.png
   :scale: 80%

As you can see, |W_1| and |W_2| describe two similar but independent procedures (e.g., two tests run for the same research project), but launched by a single parent workflow |W_0|. It might be the case, therefore, that one would like to delete information from one of them without affecting the other (e.g., if one of the tests was later deemed unnecessary).
In this particular case, just targeting |C_1| with the default behavior gives the following result, that is probably the desired final state of the database (in the following figures, the dash-circled node is the targeted one, and nodes highlighted in red are those that are eventually deleted):

.. _delexp_example02a:
.. image:: include/images/delexp_example02-a00.png
   :scale: 80%

Notice that we arrived at this result through the following traversal rules (illustrated by the red arrows in the figure):

* |D_3| will be deleted because |C_1| is being deleted (``create_forward=True``).
* |W_1| will be deleted because |C_1| is being deleted (``call_calc_backward=True``).
* |W_0| will be deleted because |W_1| is being deleted (``call_work_backward=True``)


But what if there are more calculation called by |W_1|?
These won't be deleted by the default behavior, because ``call_calc_forward=False``.
This can be illustrated by considering what would happen if we targeted the workflow node |W_1| instead (which might be the most natural thing to do for what we intend to achieve):

.. _delexp_example02b:
.. image:: include/images/delexp_example02-b00.png
   :scale: 80%

As you see, only |W_0| and |W_1| have been deleted, but |C_1| is still in the database.
In this case in particular, to achieve the same result as above, it would suffice to enable ``call_calc_forward=True`` to traverse the ``call_calc`` link from |W_1| to |C_1| and then recover our desired result, starting from a different target (|W_1| here, instead of |C_1| above).
The second workflow |W_2| would still be unaffected because there was no need to forward traverse any ``call_work`` link so far.

.. _delexp_example02c:
.. image:: include/images/delexp_example02-c00.png
   :scale: 80%

But what if some of the child processes of |W_1| are workflows instead of calculations?
The naive answer would be to enable ``call_work_forward=True`` as well. However, this will delete much more that you might want! In fact, since we are also deleting |W_0|, this last rule would also imply going through the ``call_work`` link between |W_0| and |W_2|, thus producing the following final undesired result, where most nodes have been deleted:

.. _delexp_example02d:
.. image:: include/images/delexp_example02-d00.png
   :scale: 80%

So what can you do in the general case where you want to delete all processes (calculations and workflows) contained under |W_1| without affecting |W_2|?
First you would need to get rid of the connection between these two nodes by targetting the node |W_0| (with the default keywords, and in particular ``call_work_forward=False``).
This will delete only |W_0| and no other node.

Only then you can target |W_1| by activating the keywords to include all call links to its subprocesses (``call_work_forward=True`` and ``call_calc_forward=True``).
After this two-step procedure, you will get the desired result for this more general case:

.. _delexp_example02e:
.. image:: include/images/delexp_example02-e00.png
   :scale: 80%


The number of possible scenarios and desired outcomes is impossible to cover entirely, but hopefully this example helped to show how you need to analyze the outcome of applying the delete or export procedures in your own cases of interest, especially when not using the default rules.

.. |W_0| replace:: W\ :sub:`0`
.. |W_1| replace:: W\ :sub:`1`
.. |W_2| replace:: W\ :sub:`2`
.. |C_1| replace:: C\ :sub:`1`
.. |C_2| replace:: C\ :sub:`2`
.. |D_1| replace:: D\ :sub:`1`
.. |D_2| replace:: D\ :sub:`2`
.. |D_3| replace:: D\ :sub:`3`
.. |D_4| replace:: D\ :sub:`4`
