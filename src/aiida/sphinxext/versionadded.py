###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Defines an rst directive to mark changes in a new version."""

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import set_source_info


def setup_extension(app):
    app.add_directive('versionadded-block', VersionAddedBlockDirective)


class VersionAddedBlockDirective(SphinxDirective):
    """An admonition-block version of the built-in `versionadded` directive."""

    has_content = True
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {'class': directives.class_option}

    def run(self):
        classes = ['admonition', 'versionadded-block']
        classes.extend(self.options.get('class', []))

        admonition_node = nodes.admonition(classes=classes)
        set_source_info(self, admonition_node)

        title_text = _(f'New in version {self.arguments[0]}.')
        title_node = nodes.title(
            text=title_text,
            classes=['admonition-title', 'admonition-title-block'],
        )
        admonition_node += title_node

        body = nodes.paragraph()
        self.state.nested_parse(self.content, self.content_offset, body)
        admonition_node += body

        return [admonition_node]
