Node classes
------------
There are two *Node* sub-classes, *Data* and *ProcessNode*. The *Code* nodes
can be considered as sub-classes of *Data* nodes. *CalcJobNode*,
*CalcFunctionNode*, *WorkChainNode* and the *WorkFunctionNode* are subclasses of the
*ProcessNode* class.

AiIDA graph
-----------
The AiIDA graph is a `directed graph <https://en.wikipedia.org/wiki/Directed_graph>`_.
The links of the graph are arrows connecting two nodes. An arrow (x, y) is
considered to be directed from x to y; y is called the **head** and x is called
the **tail** of the arrow; y is said to be a **direct successor** of x and x
is said to be a **direct predecessor** of y. If a path leads from x to y, then
y is said to be a **successor** of x and reachable from x, and x is said to be a
**predecessor** of y. The arrow (y, x) is called the inverted arrow of (x, y).

AiiDA links
-----------
The following table summarises the available AiiDA links and their properties.
Each line of the table corresponds to a different link, it mentions the tail
of the arrow (from column), the head of the arrow (to column) and finally
the constraints that are related to the label of the link and the nodes involved.

========= =================== ================= ==========================================
Link type Tail of link (from) Head of link (to)	Unique condition (combinations that should
                                                be unique in the link table)
========= =================== ================= ==========================================
INPUT     Data	              Calculation	    (head Calculation node, link label)
CREATE	  Calculation	      Data	            (head Data node)
RETURN    Calculation         Data	            (tail Calculation node, label)
CALL	  Calculation	      Calculation	    (head Calculation node)
========= =================== ================= ==========================================


There are four different links available: **INPUT**, **CREATE**, **RETURN**
and **CALL**.

* The **INPUT** link is always from a *Data* node (tail of the link) to
  a *Calculation* node (head of the link). The unique constraint means that
  each *Calculation* node can have only one input *Data* node with given label
  (i.e., a calculation cannot accept two inputs with the same label).

* The **CREATE** link is always from a *Calculation* node (tail of the link)
  to a *Data* node (head of the link). The unique constraint means that each
  *Data* node can be created by one and only one *Calculation* node.

* The **RETURN** link is always from a *Calculation* node (tail of the link)
  to a *Data* node (head of the link). The unique constraint means that a
  *Calculation* cannot return two or more *Data* nodes with the same label. Code
  implementation detail: For the moment there is always and only a **CREATE**
  link from a *CalculationNode* to the generated *Data*. A **RETURN** link is
  implied with the conditions of a **RETURN** link (the implementation will be
  corrected to comply shortly).

* The **CALL** link is always from a *ProcessNode* to another *ProcessNode*
  node. A given *ProcessNode* node cannot be called by more than one
  *ProcessNode* node. In practice, the caller cannot be a *CalculationNode* but
  it is always a *WorkflowNode*. Instead called calculations can be of any
  subclass of *ProcessNode*.

Graph navigation
----------------
The links can be followed in both possible directions (forward & reverse) using
the QueryBuilder. This requires to define additional “names” for each direction
of the link, and they are documented at the
:doc:`QueryBuilder section <../querying/querybuilder/usage>`. For example,
if there is an **INPUT** link from data D to calculation C, D is the
“input_of” C, or equivalently D is the “output_of” C. Currently, in the
QueryBuilder, input_of and output_of refer to any link type, where C is the
head of the arrow and D is the tail.
