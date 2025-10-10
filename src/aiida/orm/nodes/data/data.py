###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class `Data` to be used as a base class for data structures."""

from collections.abc import Iterable
from typing import Dict, Optional

from aiida.common import exceptions
from aiida.common.lang import override
from aiida.common.links import LinkType
from aiida.common.pydantic import MetadataField
from aiida.orm.entities import from_backend_entity

from ..node import Node

__all__ = ('Data',)


class UnhandledDataAttributesError(Exception):
    """Exception raised when any data attributes are not handled prior to the Data constructor."""

    def __init__(self, attributes: Iterable[str], class_name: str) -> None:
        bullet_list = '\n'.join(f'  • {attr}' for attr in attributes)
        message = (
            f'\nThe following attributes must be handled in a constructor prior to the Data class:\n'
            f'{bullet_list}\n\n'
            f'Consider implementing a constructor in {class_name} to handle the listed attributes.'
        )
        super().__init__(message)


class Data(Node):
    """The base class for all Data nodes.

    AiiDA Data classes are subclasses of Node and must support multiple inheritance.

    Architecture note:
    Calculation plugins are responsible for converting raw output data from simulation codes to Data nodes.
    Nodes are responsible for validating their content (see _validate method).
    """

    _source_attributes = ['db_name', 'db_uri', 'uri', 'id', 'version', 'extras', 'source_md5', 'description', 'license']

    # Replace this with a dictionary in each subclass that, given a file
    # extension, returns the corresponding fileformat string.
    #
    # This is used in the self.export() method.
    # By default, if not found here,
    # The fileformat string is assumed to match the extension.
    # Example: {'dat': 'dat_multicolumn'}
    _export_format_replacements: Dict[str, str] = {}

    # Data nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    class Model(Node.Model):
        source: Optional[dict] = MetadataField(
            None,
            description='Source of the data.',
            is_subscriptable=True,
            exclude_to_orm=True,
            exclude_from_cli=True,
        )

    def __init__(self, *args, source=None, **kwargs):
        """Construct a new instance, setting the ``source`` attribute if provided as a keyword argument."""

        # We verify here that all attributes of Data plugins are handled in a constructor prior to the root
        # Data class (here), gracefully rejecting them otherwise.
        node_keys = set(Node.Model.model_fields.keys())
        unhandled_keys = {key for key in kwargs if key not in node_keys}
        if unhandled_keys:
            raise UnhandledDataAttributesError(unhandled_keys, self.__class__.__name__)

        super().__init__(*args, **kwargs)

        if source is not None:
            self.source = source

    def __copy__(self):
        """Copying a Data node is not supported, use copy.deepcopy or call Data.clone()."""
        raise exceptions.InvalidOperation('copying a Data node is not supported, use copy.deepcopy')

    def __deepcopy__(self, memo):
        """Create a clone of the Data node by piping through to the clone method and return the result.

        :returns: an unstored clone of this Data node
        """
        return self.clone()

    def clone(self):
        """Create a clone of the Data node.

        :returns: an unstored clone of this Data node
        """
        import copy

        backend_clone = self.backend_entity.clone()
        clone = from_backend_entity(self.__class__, backend_clone)
        clone.base.attributes.reset(copy.deepcopy(self.base.attributes.all))
        clone.base.repository._clone(self.base.repository)

        return clone

    @property
    def source(self) -> Optional[dict]:
        """Gets the dictionary describing the source of Data object. Possible fields:

        * **db_name**: name of the source database.
        * **db_uri**: URI of the source database.
        * **uri**: URI of the object's source. Should be a permanent link.
        * **id**: object's source identifier in the source database.
        * **version**: version of the object's source.
        * **extras**: a dictionary with other fields for source description.
        * **source_md5**: MD5 checksum of object's source.
        * **description**: human-readable free form description of the object's source.
        * **license**: a string with a type of license.

        .. note:: some limitations for setting the data source exist, see ``_validate`` method.

        :return: dictionary describing the source of Data object.
        """
        return self.base.attributes.get('source', None)

    @source.setter
    def source(self, source):
        """Sets the dictionary describing the source of Data object.

        :raise KeyError: if dictionary contains unknown field.
        :raise ValueError: if supplied source description is not a dictionary.
        """
        if not isinstance(source, dict):
            raise ValueError('Source must be supplied as a dictionary')
        unknown_attrs = tuple(set(source.keys()) - set(self._source_attributes))
        if unknown_attrs:
            raise KeyError(f"Unknown source parameters: {', '.join(unknown_attrs)}")

        self.base.attributes.set('source', source)

    def set_source(self, source):
        """Sets the dictionary describing the source of Data object."""
        self.source = source

    @property
    def creator(self):
        """Return the creator of this node or None if it does not exist.

        :return: the creating node or None
        """
        inputs = self.base.links.get_incoming(link_type=LinkType.CREATE)
        link = inputs.first()
        if link:
            return link.node

        return None

    @override
    def _exportcontent(self, fileformat, main_file_name='', **kwargs):
        """Converts a Data node to one (or multiple) files.

        Note: Export plugins should return utf8-encoded **bytes**, which can be
        directly dumped to file.

        :param fileformat: the extension, uniquely specifying the file format.
        :type fileformat: str
        :param main_file_name: (empty by default) Can be used by plugin to
            infer sensible names for additional files, if necessary.  E.g. if the
            main file is '../myplot.gnu', the plugin may decide to store the dat
            file under '../myplot_data.dat'.
        :type main_file_name: str
        :param kwargs: other parameters are passed down to the plugin
        :returns: a tuple of length 2. The first element is the content of the
            otuput file. The second is a dictionary (possibly empty) in the format
            {filename: filecontent} for any additional file that should be produced.
        :rtype: (bytes, dict)
        """
        exporters = self._get_exporters()

        try:
            func = exporters[fileformat]
        except KeyError:
            if exporters.keys():
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'Currently implemented are: {}.'.format(
                        fileformat, self.__class__.__name__, ','.join(exporters.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'No formats are implemented yet.'.format(
                        fileformat, self.__class__.__name__
                    )
                )

        string, dictionary = func(main_file_name=main_file_name, **kwargs)
        assert isinstance(string, bytes), 'export function `{}` did not return the content as a byte string.'

        return string, dictionary

    @override
    def export(self, path, fileformat=None, overwrite=False, **kwargs):
        """Save a Data object to a file.

        :param fname: string with file name. Can be an absolute or relative path.
        :param fileformat: kind of format to use for the export. If not present,
            it will try to use the extension of the file name.
        :param overwrite: if set to True, overwrites file found at path. Default=False
        :param kwargs: additional parameters to be passed to the
            _exportcontent method
        :return: the list of files created
        """
        import os

        if not path:
            raise ValueError('Path not recognized')

        if os.path.exists(path) and not overwrite:
            raise OSError(f'A file was already found at {path}')

        if fileformat is None:
            extension = os.path.splitext(path)[1]
            if extension.startswith(os.path.extsep):
                extension = extension[len(os.path.extsep) :]
            if not extension:
                raise ValueError('Cannot recognized the fileformat from the extension')

            # Replace the fileformat using the replacements specified in the
            # _export_format_replacements dictionary. If not found there,
            # by default assume the fileformat string is identical to the extension
            fileformat = self._export_format_replacements.get(extension, extension)

        retlist = []

        filetext, extra_files = self._exportcontent(fileformat, main_file_name=path, **kwargs)

        if not overwrite:
            for fname in extra_files:
                if os.path.exists(fname):
                    raise OSError(f'The file {fname} already exists, stopping.')

            if os.path.exists(path):
                raise OSError(f'The file {path} already exists, stopping.')

        for additional_fname, additional_fcontent in extra_files.items():
            retlist.append(additional_fname)
            with open(additional_fname, 'wb', encoding=None) as fhandle:
                fhandle.write(additional_fcontent)  # This is up to each specific plugin
        retlist.append(path)
        with open(path, 'wb', encoding=None) as fhandle:
            fhandle.write(filetext)

        return retlist

    def _get_exporters(self):
        """Get all implemented export formats.
        The convention is to find all _prepare_... methods.
        Returns a dictionary of method_name: method_function
        """
        # NOTE: To add support for a new format, write a new function called as
        # _prepare_"" with the name of the new format
        exporter_prefix = '_prepare_'
        valid_format_names = self.get_export_formats()
        valid_formats = {k: getattr(self, exporter_prefix + k) for k in valid_format_names}
        return valid_formats

    @classmethod
    def get_export_formats(cls):
        """Get the list of valid export format strings

        :return: a list of valid formats
        """
        exporter_prefix = '_prepare_'
        method_names = dir(cls)  # get list of class methods names
        valid_format_names = [
            i[len(exporter_prefix) :] for i in method_names if i.startswith(exporter_prefix)
        ]  # filter them
        return sorted(valid_format_names)

    def importstring(self, inputstring, fileformat, **kwargs):
        """Converts a Data object to other text format.

        :param fileformat: a string (the extension) to describe the file format.
        :returns: a string with the structure description.
        """
        importers = self._get_importers()

        try:
            func = importers[fileformat]
        except KeyError:
            if importers.keys():
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'Currently implemented are: {}.'.format(
                        fileformat, self.__class__.__name__, ','.join(importers.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'No formats are implemented yet.'.format(
                        fileformat, self.__class__.__name__
                    )
                )

        # func is bound to self by getattr in _get_importers()
        func(inputstring, **kwargs)

    def importfile(self, fname, fileformat=None):
        """Populate a Data object from a file.

        :param fname: string with file name. Can be an absolute or relative path.
        :param fileformat: kind of format to use for the export. If not present,
            it will try to use the extension of the file name.
        """
        if fileformat is None:
            fileformat = fname.split('.')[-1]
        with open(fname, 'r', encoding='utf8') as fhandle:  # reads in cwd, if fname is not absolute
            self.importstring(fhandle.read(), fileformat)

    def _get_importers(self):
        """Get all implemented import formats.
        The convention is to find all _parse_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        # _parse_"" with the name of the new format
        importer_prefix = '_parse_'
        method_names = dir(self)  # get list of class methods names
        valid_format_names = [i[len(importer_prefix) :] for i in method_names if i.startswith(importer_prefix)]
        valid_formats = {k: getattr(self, importer_prefix + k) for k in valid_format_names}
        return valid_formats

    def convert(self, object_format=None, *args):
        """Convert the AiiDA StructureData into another python object

        :param object_format: Specify the output format
        """
        if object_format is None:
            raise ValueError('object_format must be provided')

        if not isinstance(object_format, str):
            raise ValueError('object_format should be a string')

        converters = self._get_converters()

        try:
            func = converters[object_format]
        except KeyError:
            if converters.keys():
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'Currently implemented are: {}.'.format(
                        object_format, self.__class__.__name__, ','.join(converters.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. ' 'No formats are implemented yet.'.format(
                        object_format, self.__class__.__name__
                    )
                )

        return func(*args)

    def _get_converters(self):
        """Get all implemented converter formats.
        The convention is to find all _get_object_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        # _prepare_"" with the name of the new format
        exporter_prefix = '_get_object_'
        method_names = dir(self)  # get list of class methods names
        valid_format_names = [i[len(exporter_prefix) :] for i in method_names if i.startswith(exporter_prefix)]
        valid_formats = {k: getattr(self, exporter_prefix + k) for k in valid_format_names}
        return valid_formats
