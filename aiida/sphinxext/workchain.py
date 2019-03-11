# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Defines an rst directive to auto-document AiiDA workchains.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.ext.autodoc import ClassDocumenter

import aiida
from aiida.common.utils import get_object_from_string
from plumpy.ports import OutputPort


def setup_aiida_workchain(app):
    app.add_directive_to_domain('py', 'aiida-workchain', AiidaWorkchainDirective)
    app.add_autodocumenter(WorkChainDocumenter)


class WorkChainDocumenter(ClassDocumenter):
    directivetype = 'aiida-workchain'
    objtype = 'workchain'
    priority = 20

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            import aiida
            aiida.try_load_dbenv()
            from aiida.engine import WorkChain
            return issubclass(member, WorkChain)
        except Exception:
            return False


class AiidaWorkchainDirective(Directive):
    """
    Directive to auto-document AiiDA workchains.
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    HIDE_UNSTORED_INPUTS_FLAG = 'hide-nondb-inputs'
    option_spec = {'module': directives.unchanged, HIDE_UNSTORED_INPUTS_FLAG: directives.flag}

    has_content = True

    def run(self):
        aiida.try_load_dbenv()
        self.load_workchain()
        return self.build_node_tree()

    def load_workchain(self):
        """Loads the workchain and sets up additional attributes."""
        # pylint: disable=attribute-defined-outside-init
        aiida.try_load_dbenv()

        self.class_name = self.arguments[0].split('(')[0]
        self.module_name = self.options['module']
        self.workchain_name = self.module_name + '.' + self.class_name
        self.workchain = get_object_from_string(self.workchain_name)
        self.workchain_spec = self.workchain.spec()

    def build_node_tree(self):
        """Returns the docutils node tree."""
        workchain_node = addnodes.desc(
            desctype='class', domain='py', noindex=False, objtype='class'
        )
        workchain_node += self.build_signature()
        workchain_node += self.build_content()
        return [workchain_node]

    def build_signature(self):
        """Returns the signature of the workchain."""
        signature = addnodes.desc_signature(first=False, fullname="Workchain")
        signature += addnodes.desc_annotation(text='workchain')
        signature += addnodes.desc_addname(text=self.module_name + '.')
        signature += addnodes.desc_name(text=self.class_name)
        return signature

    def build_content(self):
        """
        Returns the main content (docstring, inputs, outputs) of the workchain documentation.
        """
        content = addnodes.desc_content()
        content += nodes.paragraph(text=self.workchain.__doc__)

        content += self.build_doctree(
            title='Inputs:', port_namespace=self.workchain_spec.inputs,
        )
        content += self.build_doctree(
            title='Outputs:', port_namespace=self.workchain_spec.outputs
        )

        return content

    def build_doctree(self, title, port_namespace):
        """
        Returns a doctree for a given port namespace, including a title.
        """
        paragraph = nodes.paragraph()
        paragraph += nodes.strong(text=title)
        namespace_doctree = self.build_portnamespace_doctree(port_namespace)
        if len(namespace_doctree) > 0:
            paragraph += namespace_doctree
        else:
            paragraph += nodes.paragraph(text='None defined.')

        return paragraph

    def build_portnamespace_doctree(self, port_namespace):
        """
        Builds the doctree for a port namespace.
        """
        from aiida.engine.processes.ports import InputPort, PortNamespace

        result = nodes.bullet_list(bullet='*')
        for name, port in sorted(port_namespace.items()):
            item = nodes.list_item()
            if _is_non_db(port) and self.HIDE_UNSTORED_INPUTS_FLAG in self.options:
                continue
            if isinstance(port, (InputPort, OutputPort)):
                item += self.build_port_paragraph(name, port)
            elif isinstance(port, PortNamespace):
                item += addnodes.literal_strong(text=name)
                item += nodes.Text(', ')
                item += nodes.emphasis(text='Namespace')
                if port.help is not None:
                    item += nodes.Text(' -- ')
                    item.extend(publish_doctree(port.help)[0].children)
                item += self.build_portnamespace_doctree(port)
            else:
                raise NotImplementedError
            result += item
        return result

    def build_port_paragraph(self, name, port):
        """
        Build the paragraph that describes a single port.
        """
        paragraph = nodes.paragraph()
        paragraph += addnodes.literal_strong(text=name)
        paragraph += nodes.Text(', ')
        paragraph += nodes.emphasis(
            text=self.format_valid_types(port.valid_type)
        )
        paragraph += nodes.Text(', ')
        paragraph += nodes.Text('required' if port.required else 'optional')
        if _is_non_db(port):
            paragraph += nodes.Text(', ')
            paragraph += nodes.emphasis(text='non_db')
        if port.help:
            paragraph += nodes.Text(' -- ')
            # publish_doctree returns <document: <paragraph...>>.
            # Here we only want the content (children) of the paragraph.
            paragraph.extend(publish_doctree(port.help)[0].children)
        return paragraph

    @staticmethod
    def format_valid_types(valid_type):
        try:
            return valid_type.__name__
        except AttributeError:
            try:
                return '(' + ', '.join(v.__name__ for v in valid_type) + ')'
            except (AttributeError, TypeError):
                return str(valid_type)


def _is_non_db(port):
    return getattr(port, 'non_db', False)
