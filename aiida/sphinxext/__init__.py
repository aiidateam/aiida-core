"""
Defines reStructuredText directives to simplify documenting AiiDA and its plugins.
"""

__version__ = '0.1.0'

from . import workchain


def setup(app):
    """
    Setup function to add the extension classes / nodes to Sphinx.
    """
    workchain.setup_aiida_workchain(app)

    return {'version': __version__, 'parallel_read_safe': True}
