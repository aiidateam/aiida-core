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

from __future__ import absolute_import
from sphinx import addnodes
from sphinx.ext.autodoc import ClassDocumenter
from aiida.sphinxext.base import AiidaProcessDirective


def setup_aiida_calcjob(app):
    app.add_directive_to_domain('py', 'aiida-calcjob', AiidaCalcJobDirective)
    app.add_autodocumenter(CalcJobDocumenter)


class CalcJobDocumenter(ClassDocumenter):
    """
    A Documenter for CalcJob processes.
    """
    directivetype = 'aiida-workchain'
    objtype = 'workchain'
    priority = 20

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            from aiida.manage.configuration import load_profile
            load_profile()
            from aiida.engine import WorkChain
            return issubclass(member, WorkChain)
        except Exception:  # pylint: disable=broad-except
            return False


class AiidaCalcJobDirective(AiidaProcessDirective):
    """
    Directive to auto-document AiiDA workchains.
    """

    def build_signature(self):
        """Returns the signature of the workchain."""
        signature = addnodes.desc_signature(first=False, fullname='CalcJob')
        signature += addnodes.desc_annotation(text='calcjob')
        signature += addnodes.desc_addname(text=self.module_name + '.')
        signature += addnodes.desc_name(text=self.class_name)
        return signature
