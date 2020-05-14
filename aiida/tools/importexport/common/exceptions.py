# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines the exceptions thrown by AiiDA's export/import module.

Note: In order to not override the built-in `ImportError`, both `ImportError` and `ExportError` are prefixed with
    `Archive`.
"""

from aiida.common.exceptions import AiidaException

__all__ = (
    'ExportImportException', 'ArchiveExportError', 'ArchiveImportError', 'CorruptArchive',
    'IncompatibleArchiveVersionError', 'ExportValidationError', 'ImportUniquenessError', 'ImportValidationError',
    'ArchiveMigrationError', 'MigrationValidationError', 'DanglingLinkError', 'ProgressBarError'
)


class ExportImportException(AiidaException):
    """Base class for all AiiDA export/import module exceptions."""


class ArchiveExportError(ExportImportException):
    """Base class for all AiiDA export exceptions."""


class ArchiveImportError(ExportImportException):
    """Base class for all AiiDA import exceptions."""


class CorruptArchive(ExportImportException):
    """Raised when an operation is applied to a corrupt export archive, e.g. missing files or invalid formats."""


class IncompatibleArchiveVersionError(ExportImportException):
    """Raised when trying to import an export archive with an incompatible schema version."""


class ExportValidationError(ArchiveExportError):
    """Raised when validation fails during export, e.g. for non-sealed ``ProcessNode`` s."""


class ImportUniquenessError(ArchiveImportError):
    """Raised when the user tries to violate a uniqueness constraint.

    Similar to :py:class:`~aiida.common.exceptions.UniquenessError`.
    """


class ImportValidationError(ArchiveImportError):
    """Raised when validation fails during import, e.g. for parameter types and values."""


class ArchiveMigrationError(ExportImportException):
    """Base class for all AiiDA export archive migration exceptions."""


class MigrationValidationError(ArchiveMigrationError):
    """Raised when validation fails during migration of export archives."""


class DanglingLinkError(MigrationValidationError):
    """Raised when an export archive is detected to contain dangling links when importing."""


class ProgressBarError(ExportImportException):
    """Something is wrong with setting up the tqdm progress bar"""
