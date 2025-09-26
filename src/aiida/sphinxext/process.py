###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Defines an rst directive to auto-document AiiDA processes."""

import inspect
from collections.abc import Iterable, Mapping

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import directives
from plumpy.ports import OutputPort
from sphinx import addnodes
from sphinx.ext.autodoc import ClassDocumenter
from sphinx.util.docutils import SphinxDirective

from aiida.common.utils import get_object_from_string
from aiida.engine import Process
from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.manage.configuration import load_profile


def setup_extension(app):
    app.add_directive_to_domain('py', AiidaProcessDocumenter.directivetype, AiidaProcessDirective)
    # app.add_autodocumenter(AiidaProcessDocumenter)


class AiidaProcessDocumenter(ClassDocumenter):
    """Sphinx Documenter class for AiiDA Processes."""

    directivetype = 'aiida-process'
    objtype = 'process'
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return inspect.isclass(member) and issubclass(member, Process)


class AiidaProcessDirective(SphinxDirective):
    """Directive to auto-document AiiDA processes."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    HIDE_UNSTORED_INPUTS_FLAG = 'hide-nondb-inputs'
    EXPAND_NAMESPACES_FLAG = 'expand-namespaces'
    option_spec = {
        'module': directives.unchanged_required,
        HIDE_UNSTORED_INPUTS_FLAG: directives.flag,
        EXPAND_NAMESPACES_FLAG: directives.flag,
    }
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
        load_profile()

        self.class_name = self.arguments[0].split('(')[0]
        self.module_name = self.options['module']
        self.process_name = f'{self.module_name}.{self.class_name}'
        self.process = get_object_from_string(self.process_name)

        try:
            self.process_spec = self.process.spec()
        except Exception as exc:
            raise RuntimeError(f"Error while building the spec for process '{self.process_name}': '{exc!r}.'") from exc

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
        signature += addnodes.desc_addname(text=f'{self.module_name}.')
        signature += addnodes.desc_name(text=self.class_name)
        return signature

    def build_content(self):
        """Returns the main content (docstring, inputs, outputs) of the documentation."""
        content = addnodes.desc_content()

        content += nodes.paragraph(text=self.process.__doc__)

        content += self.build_doctree(
            title='Inputs:',
            port_namespace=self.process_spec.inputs,
        )
        content += self.build_doctree(title='Outputs:', port_namespace=self.process_spec.outputs)

        if hasattr(self.process_spec, 'get_outline'):
            try:
                outline = self.process_spec.get_outline()
                if outline is not None:
                    content += self.build_outline_doctree(outline=outline)
            except AssertionError:
                pass
        return content

    def build_doctree(self, title, port_namespace):
        """Returns a doctree for a given port namespace, including a title."""
        paragraph = nodes.paragraph()
        paragraph += nodes.strong(text=title)
        namespace_doctree = self.build_portnamespace_doctree(port_namespace)
        if namespace_doctree:
            paragraph += namespace_doctree
        else:
            paragraph += nodes.paragraph(text='None defined.')

        return paragraph

    def build_portnamespace_doctree(self, port_namespace):
        """Builds the doctree for a port namespace."""
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
                item += self.build_portnamespace_doctree(port)
            else:
                raise NotImplementedError
            result += item
        return result

    def build_port_content(self, name, port):
        """Build the content that describes a single port."""
        res: list = []
        res.append(addnodes.literal_strong(text=name))
        res.append(nodes.Text(', '))
        res.append(nodes.emphasis(text=self.format_valid_types(port.valid_type)))
        res.append(nodes.Text(', '))
        res.append(nodes.Text('required' if port.required else 'optional'))
        if _is_non_db(port):
            res.append(nodes.Text(', '))
            res.append(nodes.emphasis(text='non_db'))
        if _is_metadata(port):
            res.append(nodes.Text(', '))
            res.append(nodes.emphasis(text='is_metadata'))
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
                return f"({', '.join(v.__name__ for v in valid_type)})"
            except (AttributeError, TypeError):
                return str(valid_type)

    def build_outline_doctree(self, outline):
        """Build the doctree for a spec outline."""
        paragraph = nodes.paragraph()
        paragraph += nodes.strong(text='Outline:')
        outline_str = '\n'.join(self.build_outline_lines(outline.get_description(), indent=0))
        paragraph += nodes.literal_block(outline_str, outline_str)
        return paragraph

    def build_outline_lines(self, outline, indent):
        """Return a list of lines which describe the process outline."""
        indent_str = ' ' * indent
        res = []
        if isinstance(outline, str):
            res.append(indent_str + outline)
        elif isinstance(outline, Mapping):
            for key, outline_part in outline.items():
                res.append(indent_str + key)
                res.extend(self.build_outline_lines(outline_part, indent=indent + 4))
        else:
            assert isinstance(outline, Iterable)
            for outline_part in outline:
                res.extend(self.build_outline_lines(outline_part, indent=indent))
        return res


def _is_non_db(port):
    return getattr(port, 'non_db', False)


def _is_metadata(port):
    return getattr(port, 'is_metadata', False)
