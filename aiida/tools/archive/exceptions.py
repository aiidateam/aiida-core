# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines the exceptions thrown by AiiDA's archive module.

Note: In order to not override the built-in `ImportError`,
    both `ImportError` and `ExportError` are prefixed with `Archive`.
"""

from aiida.common.exceptions import AiidaException

__all__ = (
    'ExportImportException',
    'ArchiveExportError',
    'ExportValidationError',
    'ArchiveImportError',
    'ImportValidationError',
    'ImportUniquenessError',
    'ImportTestRun',
)


class ExportImportException(AiidaException):
    """Base class for all AiiDA export/import module exceptions."""


class ArchiveExportError(ExportImportException):
    """Base class for all AiiDA export exceptions."""


class ExportValidationError(ArchiveExportError):
    """Raised when validation fails during export, e.g. for non-sealed ``ProcessNode`` s."""


class ArchiveImportError(ExportImportException):
    """Base class for all AiiDA import exceptions."""


class ImportUniquenessError(ArchiveImportError):
    """Raised when the user tries to violate a uniqueness constraint.

    Similar to :py:class:`~aiida.common.exceptions.UniquenessError`.
    """


class ImportValidationError(ArchiveImportError):
    """Raised when validation fails during import, e.g. for parameter types and values."""


class ImportTestRun(ArchiveImportError):
    """Raised during an import, before the transaction is commited."""
