"""Add a ``panels`` directive.

This directive creates panels of content in a 2 x N layout.
The panels are separated by `---`::

    .. panels::
        :centred:

        Content of the top-left panel

        ---

        Content of the top-right panel

        ---

        Content of the bottom-left panel

        ---

        Content of the bottom-right panel

The content can be any valid rST.
`:centred:` indicates that the panel contents should be horizontally centred.
"""
import os
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class Panels(SphinxDirective):
    """Two Column Panels."""

    has_content = True
    option_spec = {'centred': directives.flag}

    def run(self):

        # split the block into panels
        panel_blocks = []
        start_line = 0
        for i, line in enumerate(self.content):
            if line.startswith('---'):
                panel_blocks.append((self.content[start_line:i], start_line))
                start_line = i + 1
        try:
            panel_blocks.append((self.content[start_line:], start_line))
        except IndexError:
            pass

        parent = nodes.container(classes=['sphinx-panels'])
        for content, offset in panel_blocks:
            panel = nodes.container(classes=['sphinx-panel', 'width50'])
            parent += panel
            content_box = nodes.container(
                classes=['sphinx-panel-content'] + (['text-center'] if 'centred' in self.options else [])
            )
            self.state.nested_parse(content, self.content_offset + offset, content_box)
            panel += content_box
        return [parent]


def add_static_path(app):
    static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '_static'))
    if static_path not in app.config.html_static_path:
        app.config.html_static_path.append(static_path)


def setup(app):
    app.add_directive('panels', Panels)
    app.connect('builder-inited', add_static_path)
    app.add_css_file('panels.css')
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
