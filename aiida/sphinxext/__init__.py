# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Defines reStructuredText directives to simplify documenting AiiDA and its plugins."""
from sphinx.application import Sphinx


def setup(app: Sphinx):
    """Setup function to add the extension classes / nodes to Sphinx."""
    import aiida

    from . import autodoc_aliases, calcjob, process, workchain

    app.setup_extension('sphinxcontrib.details.directive')
    process.setup_extension(app)
    workchain.setup_extension(app)
    calcjob.setup_extension(app)

    # add autodoc aliases
    app.add_transform(autodoc_aliases.AutodocAliases)

    return {'version': aiida.__version__, 'parallel_read_safe': True}
