
from aiida.common.links import LinkType
from ete3 import Tree


def get_ascii_tree(node, node_label='type', show_pk=True, max_depth=1,
                   follow_links_of_type=LinkType.CALL):
    tree_string = build_tree(
       node,
       node_label=node_label,
       show_pk=show_pk,
       max_depth=max_depth,
       follow_links_of_type=follow_links_of_type
    )
    t = Tree("({});".format(tree_string), format = 1)
    return t.get_ascii(show_internal=True)


def build_tree(node, node_label='type', show_pk=True, depth=0, max_depth=1,
               follow_links_of_type=LinkType.CALL):
    out_values = []

    if depth < max_depth:
        children =[]
        outputs = node.get_outputs(link_type=follow_links_of_type)
        for child in sorted(outputs, key=_ctime):
            children.append(
                build_tree(child, node_label, depth=depth + 1,
                           max_depth=max_depth))

        if children:
            out_values.append("(")
            out_values.append(", ".join(children))
            out_values.append(")")

    try:
        label = str(getattr(node, node_label))
    except AttributeError:
        try:
            label = node.get_attr(node_label)
        except AttributeError:
            label = node.__class__.__name__
    if show_pk:
        label += " [{}]".format(node.pk)

    out_values.append(label)

    return "".join(out_values)


def _ctime(node):
    return node.ctime
