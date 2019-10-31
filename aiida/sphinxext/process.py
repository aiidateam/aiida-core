# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Defines an rst directive to auto-document AiiDA processes.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.ext.autodoc import ClassDocumenter

from plumpy.ports import OutputPort
from aiida.common.utils import get_object_from_string


def setup_extension(app):
    app.add_directive_to_domain('py', AiidaProcessDocumenter.directivetype, AiidaProcessDirective)
    app.add_autodocumenter(AiidaProcessDocumenter)


class AiidaProcessDocumenter(ClassDocumenter):
    """Sphinx Documenter class for AiiDA Processes."""
    directivetype = 'aiida-process'
    objtype = 'process'
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        from aiida.engine import Process
        return issubclass(cls, Process)


class AiidaProcessDirective(Directive):
    """
    Directive to auto-document AiiDA processes.
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    HIDE_UNSTORED_INPUTS_FLAG = 'hide-nondb-inputs'
    option_spec = {'module': directives.unchanged, HIDE_UNSTORED_INPUTS_FLAG: directives.flag}
    signature = 'Process'
    annotation = 'process'

    has_content = True

    def run(self):
        self.initialize()
        return self.build_node_tree()

    def initialize(self):
        """Set internal attributes of the class.

        Includes importing the process class.
        """
        # pylint: disable=attribute-defined-outside-init
        from aiida.manage.configuration import load_profile
        load_profile()

        self.class_name = self.arguments[0].split('(')[0]
        self.module_name = self.options['module']
        self.process_name = self.module_name + '.' + self.class_name
        self.process = get_object_from_string(self.process_name)
        self.process_spec = self.process.spec()

    def build_node_tree(self):
        """Returns the docutils node tree."""
        process_node = addnodes.desc(desctype='class', domain='py', noindex=False, objtype='class')
        process_node += self.build_signature()
        process_node += self.build_content()
        return [process_node]

    def build_signature(self):
        """Returns the signature of the process."""
        signature = addnodes.desc_signature(first=False, fullname=self.signature)
        signature += addnodes.desc_annotation(text=self.annotation)
        signature += addnodes.desc_addname(text=self.module_name + '.')
        signature += addnodes.desc_name(text=self.class_name)
        return signature

    def build_content(self):
        """
        Returns the main content (docstring, inputs, outputs) of the documentation.
        """
        content = nodes.paragraph(text=self.process.__doc__)

        content += self.build_doctree(
            title='Inputs:',
            port_namespace=self.process_spec.inputs,
        )
        content += self.build_doctree(title='Outputs:', port_namespace=self.process_spec.outputs)

        return content

    def build_doctree(self, title, port_namespace):
        """
        Returns a doctree for a given port namespace, including a title.
        """
        paragraph = nodes.paragraph()
        paragraph += nodes.strong(text=title)
        namespace_doctree = self.build_portnamespace_doctree(port_namespace)
        if namespace_doctree:
            paragraph += namespace_doctree
        else:
            paragraph += nodes.paragraph(text='None defined.')

        return paragraph

    def build_portnamespace_doctree(self, port_namespace):
        """
        Builds the doctree for a port namespace.
        """
        from aiida.engine.processes.ports import InputPort, PortNamespace

        if not port_namespace:
            return None
        result = nodes.bullet_list(bullet='*')
        for name, port in sorted(port_namespace.items()):
            item = nodes.list_item()
            if _is_non_db(port) and self.HIDE_UNSTORED_INPUTS_FLAG in self.options:
                continue
            if isinstance(port, (InputPort, OutputPort)):
                item.extend(self.build_port_content(name, port))
            elif isinstance(port, PortNamespace):
                item += addnodes.literal_strong(text=name)
                item += nodes.Text(', ')
                item += nodes.emphasis(text='Namespace')
                if port.help is not None:
                    item += nodes.Text(' -- ')
                    item.extend(publish_doctree(port.help)[0].children)
                sub_doctree = self.build_portnamespace_doctree(port)
                if sub_doctree:
                    # This is a workaround because this extension doesn't work with Python2.
                    try:
                        from sphinxcontrib.details.directive import details, summary
                        sub_item = details()
                        sub_item += summary(text='Namespace Ports')
                        sub_item += sub_doctree
                    except ImportError:
                        sub_item = sub_doctree
                    item += sub_item
            else:
                raise NotImplementedError
            result += item
        return result

    def build_port_content(self, name, port):
        """
        Build the content that describes a single port.
        """
        res = []
        res.append(addnodes.literal_strong(text=name))
        res.append(nodes.Text(', '))
        res.append(nodes.emphasis(text=self.format_valid_types(port.valid_type)))
        res.append(nodes.Text(', '))
        res.append(nodes.Text('required' if port.required else 'optional'))
        if _is_non_db(port):
            res.append(nodes.Text(', '))
            res.append(nodes.emphasis(text='non_db'))
        if port.help:
            res.append(nodes.Text(' -- '))
            # publish_doctree returns <document: <paragraph...>>.
            # Here we only want the content (children) of the paragraph.
            res.extend(publish_doctree(port.help)[0].children)
        return res

    @staticmethod
    def format_valid_types(valid_type):
        """Format valid types."""
        try:
            return valid_type.__name__
        except AttributeError:
            try:
                return '(' + ', '.join(v.__name__ for v in valid_type) + ')'
            except (AttributeError, TypeError):
                return str(valid_type)


def _is_non_db(port):
    return getattr(port, 'non_db', False)
