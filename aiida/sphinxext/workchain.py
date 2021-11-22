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
Defines an rst directive to auto-document AiiDA workchains.
"""
import inspect

from aiida.engine import WorkChain

from .process import AiidaProcessDirective, AiidaProcessDocumenter


def setup_extension(app):
    app.add_directive_to_domain('py', AiidaWorkChainDocumenter.directivetype, AiidaWorkchainDirective)
    # app.add_autodocumenter(AiidaWorkChainDocumenter)


class AiidaWorkChainDocumenter(AiidaProcessDocumenter):
    """Sphinx Documenter class for AiiDA WorkChains."""
    directivetype = 'aiida-workchain'
    objtype = 'workchain'
    priority = 20

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return inspect.isclass(member) and issubclass(member, WorkChain)


class AiidaWorkchainDirective(AiidaProcessDirective):
    signature = 'WorkChain'
    annotation = 'workchain'
