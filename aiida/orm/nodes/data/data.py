# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class `Data` to be used as a base class for data structures."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.common.lang import override

from ..node import Node

__all__ = ('Data',)


class Data(Node):
    """
    This class is base class for all data objects.

    Specifications of the Data class:
    AiiDA Data objects are subclasses of Node and should have

    Multiple inheritance must be supported, i.e. Data should have methods for
    querying and be able to inherit other library objects such as ASE for
    structures.

    Architecture note:
    The code plugin is responsible for converting a raw data object produced by
    code to AiiDA standard object format. The data object then validates itself
    according to its method. This is done independently in order to allow
    cross-validation of plugins.
    """
    _source_attributes = ['db_name', 'db_uri', 'uri', 'id', 'version', 'extras', 'source_md5', 'description', 'license']

    # Replace this with a dictionary in each subclass that, given a file
    # extension, returns the corresponding fileformat string.
    #
    # This is used in the self.export() method.
    # By default, if not found here,
    # The fileformat string is assumed to match the extension.
    # Example: {'dat': 'dat_multicolumn'}
    _export_format_replacements = {}

    # Data nodes are storable
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    def __copy__(self):
        """Copying a Data node is not supported, use copy.deepcopy or call Data.clone()."""
        raise exceptions.InvalidOperation('copying a Data node is not supported, use copy.deepcopy')

    def __deepcopy__(self, memo):
        """
        Create a clone of the Data node by pipiong through to the clone method and return the result.

        :returns: an unstored clone of this Data node
        """
        return self.clone()

    def clone(self):
        """
        Create a clone of the Data node.

        :returns: an unstored clone of this Data node
        """
        # pylint: disable=no-member
        import copy

        backend_clone = self.backend_entity.clone()
        clone = self.__class__.from_backend_entity(backend_clone)

        clone.reset_attributes(copy.deepcopy(self.attributes))
        clone.put_object_from_tree(self._repository._get_base_folder().abspath)  # pylint: disable=protected-access

        return clone

    @property
    def source(self):
        """
        Gets the dictionary describing the source of Data object. Possible fields:

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
        return self.get_attribute('source', None)

    @source.setter
    def source(self, source):
        """
        Sets the dictionary describing the source of Data object.

        :raise KeyError: if dictionary contains unknown field.
        :raise ValueError: if supplied source description is not a dictionary.
        """
        if not isinstance(source, dict):
            raise ValueError('Source must be supplied as a dictionary')
        unknown_attrs = tuple(set(source.keys()) - set(self._source_attributes))
        if unknown_attrs:
            raise KeyError('Unknown source parameters: {}'.format(', '.join(unknown_attrs)))

        self.set_attribute('source', source)

    def set_source(self, source):
        """
        Sets the dictionary describing the source of Data object.
        """
        self.source = source

    @property
    def creator(self):
        """Return the creator of this node or None if it does not exist.

        :return: the creating node or None
        """
        inputs = self.get_incoming(link_type=LinkType.CREATE)
        if inputs:
            return inputs.first().node

        return None

    @override
    def _exportcontent(self, fileformat, main_file_name='', **kwargs):
        """
        Converts a Data node to one (or multiple) files.

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
                    'The format {} is not implemented for {}. '
                    'Currently implemented are: {}.'.format(
                        fileformat, self.__class__.__name__, ','.join(exporters.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. '
                    'No formats are implemented yet.'.format(fileformat, self.__class__.__name__)
                )

        string, dictionary = func(main_file_name=main_file_name, **kwargs)
        assert isinstance(string, bytes), 'export function `{}` did not return the content as a byte string.'

        return string, dictionary

    @override
    def export(self, path, fileformat=None, overwrite=False, **kwargs):
        """
        Save a Data object to a file.

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
            raise OSError('A file was already found at {}'.format(path))

        if fileformat is None:
            extension = os.path.splitext(path)[1]
            if extension.startswith(os.path.extsep):
                extension = extension[len(os.path.extsep):]
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
                    raise OSError('The file {} already exists, stopping.'.format(fname))

            if os.path.exists(path):
                raise OSError('The file {} already exists, stopping.'.format(path))

        for additional_fname, additional_fcontent in extra_files.items():
            retlist.append(additional_fname)
            with io.open(additional_fname, 'wb', encoding=None) as fhandle:
                fhandle.write(additional_fcontent)  # This is up to each specific plugin
        retlist.append(path)
        with io.open(path, 'wb', encoding=None) as fhandle:
            fhandle.write(filetext)

        return retlist

    def _get_exporters(self):
        """
        Get all implemented export formats.
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
        """
        Get the list of valid export format strings

        :return: a list of valid formats
        """
        exporter_prefix = '_prepare_'
        method_names = dir(cls)  # get list of class methods names
        valid_format_names = [
            i[len(exporter_prefix):] for i in method_names if i.startswith(exporter_prefix)
        ]  # filter them
        return sorted(valid_format_names)

    def importstring(self, inputstring, fileformat, **kwargs):
        """
        Converts a Data object to other text format.

        :param fileformat: a string (the extension) to describe the file format.
        :returns: a string with the structure description.
        """
        importers = self._get_importers()

        try:
            func = importers[fileformat]
        except KeyError:
            if importers.keys():
                raise ValueError(
                    'The format {} is not implemented for {}. '
                    'Currently implemented are: {}.'.format(
                        fileformat, self.__class__.__name__, ','.join(importers.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. '
                    'No formats are implemented yet.'.format(fileformat, self.__class__.__name__)
                )

        # func is bound to self by getattr in _get_importers()
        func(inputstring, **kwargs)

    def importfile(self, fname, fileformat=None):
        """
        Populate a Data object from a file.

        :param fname: string with file name. Can be an absolute or relative path.
        :param fileformat: kind of format to use for the export. If not present,
            it will try to use the extension of the file name.
        """
        if fileformat is None:
            fileformat = fname.split('.')[-1]
        with io.open(fname, 'r', encoding='utf8') as fhandle:  # reads in cwd, if fname is not absolute
            self.importstring(fhandle.read(), fileformat)

    def _get_importers(self):
        """
        Get all implemented import formats.
        The convention is to find all _parse_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        # _parse_"" with the name of the new format
        importer_prefix = '_parse_'
        method_names = dir(self)  # get list of class methods names
        valid_format_names = [i[len(importer_prefix):] for i in method_names if i.startswith(importer_prefix)]
        valid_formats = {k: getattr(self, importer_prefix + k) for k in valid_format_names}
        return valid_formats

    def convert(self, object_format=None, *args):
        """
        Convert the AiiDA StructureData into another python object

        :param object_format: Specify the output format
        """
        # pylint: disable=keyword-arg-before-vararg
        import six

        if object_format is None:
            raise ValueError('object_format must be provided')

        if not isinstance(object_format, six.string_types):
            raise ValueError('object_format should be a string')

        converters = self._get_converters()

        try:
            func = converters[object_format]
        except KeyError:
            if converters.keys():
                raise ValueError(
                    'The format {} is not implemented for {}. '
                    'Currently implemented are: {}.'.format(
                        object_format, self.__class__.__name__, ','.join(converters.keys())
                    )
                )
            else:
                raise ValueError(
                    'The format {} is not implemented for {}. '
                    'No formats are implemented yet.'.format(object_format, self.__class__.__name__)
                )

        return func(*args)

    def _get_converters(self):
        """
        Get all implemented converter formats.
        The convention is to find all _get_object_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        # _prepare_"" with the name of the new format
        exporter_prefix = '_get_object_'
        method_names = dir(self)  # get list of class methods names
        valid_format_names = [i[len(exporter_prefix):] for i in method_names if i.startswith(exporter_prefix)]
        valid_formats = {k: getattr(self, exporter_prefix + k) for k in valid_format_names}
        return valid_formats

    def _validate(self):
        """
        Perform validation of the Data object.

        .. note:: validation of data source checks license and requires
            attribution to be provided in field 'description' of source in
            the case of any CC-BY* license. If such requirement is too
            strict, one can remove/comment it out.
        """
        # Validation of ``source`` is commented out due to Issue #9
        # (https://bitbucket.org/epfl_theos/aiida_epfl/issues/9/)
        # super(Data, self)._validate()
        # if self.source is not None and \
        #    self.source.get('license', None) and \
        #    self.source['license'].startswith('CC-BY') and \
        #    self.source.get('description', None) is None:
        #     raise ValidationError("License of the object ({}) requires "
        #                           "attribution, while none is given in the "
        #                           "description".format(self.source['license']))
