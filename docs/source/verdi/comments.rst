########
Comments
########

There are various ways of attaching notes/comments to a node within AiiDA. In the first scripting examples, you might already have noticed the possibility of storing a ``label`` or a ``description`` to any AiiDA Node. However, these properties are defined at the creation of the Node, and it is not possible to modify them after the Node has been stored.

The Node ``comment`` provides a simple way to have a more dynamic management of comments, in which any user can write a comment on the Node, or modify it or delete it.

The ``verdi comment`` provides a set of methods that are used to manipulate the comments:

* **add**: add a new comment to a Node.
* **update**: modify a comment.
* **show**: show the existing comments attached to the Node.
* **remove**: remove a comment.
