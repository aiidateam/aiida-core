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
Defines an rst directive to auto-document AiiDA calculation job.
"""
import inspect

from aiida.engine import CalcJob

from .process import AiidaProcessDirective, AiidaProcessDocumenter


def setup_extension(app):
    app.add_directive_to_domain('py', AiidaCalcJobDocumenter.directivetype, AiidaCalcJobDirective)
    # app.add_autodocumenter(AiidaCalcJobDocumenter)


class AiidaCalcJobDocumenter(AiidaProcessDocumenter):
    """Sphinx Documenter for AiiDA CalcJobs."""
    directivetype = 'aiida-calcjob'
    objtype = 'calcjob'
    priority = 20

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return inspect.isclass(member) and issubclass(member, CalcJob)


class AiidaCalcJobDirective(AiidaProcessDirective):
    signature = 'CalcJob'
    annotation = 'calcjob'
