# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that define the exceptions that are thrown by AiiDA's internal code."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__all__ = ('AiidaException', 'NotExistent', 'MultipleObjectsError', 'RemoteOperationError', 'ContentNotExistent',
           'FailedError', 'StoringNotAllowed', 'ModificationNotAllowed', 'IntegrityError', 'UniquenessError',
           'MissingEntryPointError', 'MultipleEntryPointError', 'LoadingEntryPointError', 'MissingPluginError',
           'LoadingPluginFailed', 'InvalidOperation', 'ParsingError', 'InternalError', 'PluginInternalError',
           'ValidationError', 'ConfigurationError', 'ProfileConfigurationError', 'MissingConfigurationError',
           'ConfigurationVersionError', 'DbContentError', 'InputValidationError', 'FeatureNotAvailable',
           'FeatureDisabled', 'LicensingException', 'TestsNotAllowedError', 'UnsupportedSpeciesError',
           'DanglingLinkError', 'TransportTaskException', 'IncompatibleArchiveVersionError', 'OutputParsingError')


class AiidaException(Exception):
    """
    Base class for all AiiDA exceptions.

    Each module will have its own subclass, inherited from this
    (e.g. ExecManagerException, TransportException, ...)
    """


class NotExistent(AiidaException):
    """
    Raised when the required entity does not exist.
    """


class MultipleObjectsError(AiidaException):
    """
    Raised when more than one entity is found in the DB, but only one was
    expected.
    """


class RemoteOperationError(AiidaException):
    """
    Raised when an error in a remote operation occurs, as in a failed kill()
    of a scheduler job.
    """


class ContentNotExistent(NotExistent):
    """
    Raised when trying to access an attribute, a key or a file in the result
    nodes that is not present
    """


class FailedError(AiidaException):
    """
    Raised when accessing a calculation that is in the FAILED status
    """


class StoringNotAllowed(AiidaException):
    """
    Raised when the user tries to store an unstorable node (e.g. a base Node class)
    """


class ModificationNotAllowed(AiidaException):
    """
    Raised when the user tries to modify a field, object, property, ... that should not
    be modified.
    """


class IntegrityError(AiidaException):
    """
    Raised when there is an underlying data integrity error.  This can be database related
    or a general data integrity error.  This can happen if, e.g., a foreign key check fails.
    See PEP 249 for details.
    """


class UniquenessError(AiidaException):
    """
    Raised when the user tries to violate a uniqueness constraint (on the
    DB, for instance).
    """


class MissingEntryPointError(AiidaException):
    """
    Raised when the requested entry point is not registered with the entry point manager
    """


class MultipleEntryPointError(AiidaException):
    """
    Raised when the requested entry point cannot uniquely be resolved by the entry point manager
    """


class LoadingEntryPointError(AiidaException):
    """
    Raised when the class corresponding to requested entry point cannot be loaded
    """


class MissingPluginError(AiidaException):
    """
    Raised when the user tries to use a plugin that is not available or does not exist.
    """


class LoadingPluginFailed(AiidaException):
    """
    Raised when loading a plugin through the plugin loader fails
    """


class InvalidOperation(AiidaException):
    """
    The allowed operation is not valid (e.g., when trying to add a non-internal attribute
    before saving the entry), or deleting an entry that is protected (e.g.,
    because it is referenced by foreign keys)
    """


class ParsingError(AiidaException):
    """
    Generic error raised when there is a parsing error
    """


class InternalError(AiidaException):
    """
    Error raised when there is an internal error of AiiDA.
    """


class PluginInternalError(InternalError):
    """
    Error raised when there is an internal error which is due to a plugin
    and not to the AiiDA infrastructure.
    """


class ValidationError(AiidaException):
    """
    Error raised when there is an error during the validation phase
    of a property.
    """


class ConfigurationError(AiidaException):
    """
    Error raised when there is a configuration error in AiiDA.
    """


class ProfileConfigurationError(ConfigurationError):
    """
    Configuration error raised when a wrong/inexistent profile is requested.
    """


class MissingConfigurationError(ConfigurationError):
    """
    Configuration error raised when the configuration file is missing.
    """


class ConfigurationVersionError(ConfigurationError):
    """
    Configuration error raised when the configuration file version is not
    compatible with the current version.
    """


class DbContentError(AiidaException):
    """
    Raised when the content of the DB is not valid.
    This should never happen if the user does not play directly
    with the DB.
    """


class InputValidationError(ValidationError):
    """
    The input data for a calculation did not validate (e.g., missing
    required input data, wrong data, ...)
    """


class FeatureNotAvailable(AiidaException):
    """
    Raised when a feature is requested from a plugin, that is not available.
    """


class FeatureDisabled(AiidaException):
    """
    Raised when a feature is requested, but the user has chosen to disable
    it (e.g., for submissions on disabled computers).
    """


class LicensingException(AiidaException):
    """
    Raised when requirements for data licensing are not met.
    """


class TestsNotAllowedError(AiidaException):
    """
    Raised when tests are required to be run/loaded, but we are not in a testing environment.

    This is to prevent data loss.
    """


class UnsupportedSpeciesError(ValueError):
    """
    Raised when StructureData operations are fed species that are not supported by AiiDA such as Deuterium
    """


class DanglingLinkError(Exception):
    """
    Raised when an export archive is detected to contain dangling links when importing
    """


class TransportTaskException(Exception):
    """
    Raised when a TransportTask, an task to be completed by the engine that requires transport, fails
    """


class IncompatibleArchiveVersionError(Exception):
    """
    Raised when trying to import an export archive with an incompatible schema version.
    """


class OutputParsingError(ParsingError):
    """
    Can be raised by a Parser when it fails to parse the output generated by a `CalcJob` process.
    """
