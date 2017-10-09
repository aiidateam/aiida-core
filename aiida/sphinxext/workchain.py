"""
Defines an rst directive to auto-document AiiDA workchains.
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
import aiida
from plum.util import load_class
from plum.port import InputPort, OutputPort


def setup_aiida_workchain(app):
    app.add_directive('aiida-workchain', AiidaWorkchainDirective)


class AiidaWorkchainDirective(Directive):
    """
    Directive to auto-document AiiDA workchains.
    """
    required_arguments = 1
    HIDDEN_PORTS_FLAG = 'hidden-ports'
    option_spec = {HIDDEN_PORTS_FLAG: directives.flag}
    has_content = False

    def run(self):
        aiida.try_load_dbenv()
        self.load_workchain()
        return self.build_node_tree()

    def load_workchain(self):
        """Loads the workchain and sets up additional attributes."""
        # pylint: disable=attribute-defined-outside-init
        self.workchain_name = self.arguments[0]
        self.module_name, self.class_name = self.workchain_name.rsplit('.', 1)
        self.workchain = load_class(self.workchain_name)
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
            title='Inputs:', port_namespace=self.workchain_spec.inputs
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
        paragraph += self.build_portnamespace_doctree(port_namespace)

        return paragraph

    def build_portnamespace_doctree(self, portnamespace):
        """
        Builds the doctree for a port namespace.
        """
        from aiida.work.process import PortNamespace

        result = nodes.bullet_list(bullet='*')
        for name, port in sorted(portnamespace.items()):
            if name.startswith(
                '_'
            ) and self.HIDDEN_PORTS_FLAG not in self.options:
                continue
            if name == 'dynamic':
                continue
            item = nodes.list_item()
            if isinstance(port, (InputPort, OutputPort)):
                item += self.build_port_paragraph(name, port)
            elif isinstance(port, PortNamespace):
                # item += addnodes.literal_strong(
                #     text='Namespace {}'.format(name)
                # )
                item += addnodes.literal_strong(text=name)
                item += nodes.Text(', ')
                item += nodes.emphasis(text='Namespace')
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
        if port.help:
            paragraph += nodes.Text(' -- ')
            paragraph += nodes.Text(port.help)
        return paragraph

    @staticmethod
    def format_valid_types(valid_type):
        try:
            return valid_type.__name__
        except TypeError:
            return str(valid_type)
