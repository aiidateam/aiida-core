# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared resources for the archive."""
import dataclasses
import os
from typing import Dict, List, Optional, Set

__all__ = ('ArchiveMetadata', 'detect_archive_type')


@dataclasses.dataclass
class ArchiveMetadata:
    """Class for storing metadata about this archive.

    Required fields are necessary for importing the data back into AiiDA,
    whereas optional fields capture information about the export/migration process(es)
    """
    export_version: str
    aiida_version: str
    # Entity type -> database ID key
    unique_identifiers: Dict[str, str] = dataclasses.field(repr=False)
    # Entity type -> database key -> meta parameters
    all_fields_info: Dict[str, Dict[str, Dict[str, str]]] = dataclasses.field(repr=False)

    # optional data
    graph_traversal_rules: Optional[Dict[str, bool]] = dataclasses.field(default=None)
    # Entity type -> UUID list
    entities_starting_set: Optional[Dict[str, Set[str]]] = dataclasses.field(default=None)
    include_comments: Optional[bool] = dataclasses.field(default=None)
    include_logs: Optional[bool] = dataclasses.field(default=None)
    # list of migration event notifications
    conversion_info: List[str] = dataclasses.field(default_factory=list, repr=False)


def detect_archive_type(in_path: str) -> str:
    """For back-compatibility, but should be replaced with direct comparison of classes.
    
    :param in_path: the path to the file
    :returns: the archive type identifier (currently one of 'zip', 'tar.gz', 'folder')

    """
    import tarfile
    import zipfile
    from aiida.tools.importexport.common.config import ExportFileFormat
    from aiida.tools.importexport.common.exceptions import ImportValidationError

    if os.path.isdir(in_path):
        return 'folder'
    if tarfile.is_tarfile(in_path):
        return ExportFileFormat.TAR_GZIPPED
    if zipfile.is_zipfile(in_path):
        return ExportFileFormat.ZIP
    raise ImportValidationError(
        'Unable to detect the input file format, it is neither a '
        'folder, tar file, nor a (possibly compressed) zip file.'
    )
