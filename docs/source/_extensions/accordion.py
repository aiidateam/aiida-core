"""Add an ``accordion`` directive.

This directive creates "heading" button which, when pressed,
will expose the directives contents::

    .. accordion:: Click here to get more info

        Here's some more information.

The title and content can be any valid rST.

This follows very closely to:
https://www.w3schools.com/howto/howto_js_collapsible.asp
"""
import os
from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class ButtonNode(nodes.TextElement):
    pass


def visit_button_node(self, node):
    # type: (nodes.Element) -> None
    self.body.append(self.starttag(node, 'button', CLASS=' '.join(node['classes'])))


def depart_button_node(self, _):
    # type: (nodes.Element) -> None
    self.body.append('</button>\n\n')


class Accordion(SphinxDirective):
    """Accordion style expandable section."""

    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        title_text = self.arguments[0]
        textnodes, _ = self.state.inline_text(title_text, self.lineno)
        button = ButtonNode(title_text, '', *textnodes, classes=['accordion'])
        panel = nodes.container(classes=['accordion-content'])
        self.state.nested_parse(self.content, self.content_offset, panel)
        return [button, panel]


def add_static_path(app):
    static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '_static'))
    if static_path not in app.config.html_static_path:
        app.config.html_static_path.append(static_path)


def setup(app):

    app.add_node(ButtonNode, html=(visit_button_node, depart_button_node), latex=(None, None), text=(None, None))
    app.add_directive('accordion', Accordion)

    app.connect('builder-inited', add_static_path)
    app.add_js_file('accordion.js')
    app.add_css_file('accordion.css')

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
