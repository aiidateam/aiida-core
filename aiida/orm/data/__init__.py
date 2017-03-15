# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.node import Node
from aiida.common.links import LinkType
from aiida.common.lang import override
from aiida.common.exceptions import ModificationNotAllowed



class Data(Node):
    """
    This class is base class for all data objects.

    Specifications of the Data class:
    AiiDA Data objects are subclasses of Node and should have

    Multiple inheritance must be suppoted, i.e. Data should have methods for
    querying and be able to inherit other library objects such as ASE for
    structures.

    Architecture note:
    The code plugin is responsible for converting a raw data object produced by
    code to AiiDA standard object format. The data object then validates itself
    according to its method. This is done independently in order to allow
    cross-validation of plugins.
    """
    _source_attributes = ['db_name', 'db_uri', 'uri', 'id', 'version',
                          'extras', 'source_md5', 'description', 'license']

    @property
    def source(self):
        """
        Gets the dictionary describing the source of Data object. Possible
        fields:

        * **db_name**: name of the source database.
        * **db_uri**: URI of the source database.
        * **uri**: URI of the object's source. Should be a permanent link.
        * **id**: object's source identifier in the source database.
        * **version**: version of the object's source.
        * **extras**: a dictionary with other fields for source description.
        * **source_md5**: MD5 checksum of object's source.
        * **description**: human-readable free form description of the
            object's source.
        * **license**: a string with a type of license.

        .. note:: some limitations for setting the data source exist, see
            ``_validate`` method.

        :return: dictionary describing the source of Data object.
        """
        return self.get_attr('source', None)

    @source.setter
    def source(self, source):
        """
        Sets the dictionary describing the source of Data object.

        :raise KeyError: if dictionary contains unknown field.
        :raise ValueError: if supplied source description is not a
            dictionary.
        """
        if not isinstance(source, dict):
            raise ValueError("Source must be supplied as a dictionary")
        unknown_attrs = list(set(source.keys()) - set(self._source_attributes))
        if unknown_attrs:
            raise KeyError("Unknown source parameters: "
                           "{}".format(", ".join(unknown_attrs)))

        self._set_attr('source', source)

    def set_source(self, source):
        """
        Sets the dictionary describing the source of Data object.
        """
        self.source = source

    @override
    def _set_attr(self, key, value):
        """
        Set a new attribute to the Node (in the DbAttribute table).

        :param str key: key name
        :param value: its value
        :raise ModificationNotAllowed: if such attribute cannot be added (e.g.
            because the node was already stored)

        :raise ValidationError: if the key is not valid (e.g. it contains the
            separator symbol).
        """
        if self.is_stored:
            raise ModificationNotAllowed(
                "Cannot change the attributes of a stored data node.")
        super(Data, self)._set_attr(key, value)

    @override
    def _del_attr(self, key):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if the Node was already stored.
        """
        if self.is_stored:
            raise ModificationNotAllowed(
                "Cannot delete the attributes of a stored data node.")
        super(Data, self)._del_attr(key)

    @override
    def add_link_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        from aiida.orm.calculation import Calculation

        if link_type is LinkType.CREATE and \
                        len(self.get_inputs(link_type=LinkType.CREATE)) > 0:
            raise ValueError("At most one CREATE node can enter a data node")

        if not isinstance(src, Calculation):
            raise ValueError(
                "Links entering a data object can only be of type calculation")

        return super(Data, self).add_link_from(src, label, link_type)

    @override
    def _linking_as_output(self, dest, link_type):
        """
        Raise a ValueError if a link from self to dest is not allowed.

        An output of a data can only be a calculation
        """
        from aiida.orm.calculation import Calculation
        if not isinstance(dest, Calculation):
            raise ValueError(
                "The output of a data node can only be a calculation")

        return super(Data, self)._linking_as_output(dest, link_type)

    @override
    def _exportstring(self, fileformat, **kwargs):
        """
        Converts a Data object to other text format.

        :param fileformat: a string (the extension) to describe the file format.
        :returns: a string with the structure description.
        """
        exporters = self._get_exporters()

        try:
            func = exporters[fileformat]
        except KeyError:
            if len(exporters.keys()) > 0:
                raise ValueError("The format {} is not implemented for {}. "
                                 "Currently implemented are: {}.".format(
                    fileformat, self.__class__.__name__,
                    ",".join(exporters.keys())))
            else:
                raise ValueError("The format {} is not implemented for {}. "
                                 "No formats are implemented yet.".format(
                    fileformat, self.__class__.__name__))

        return func(**kwargs)

    @override
    def export(self, fname, fileformat=None):
        """
        Save a Data object to a file.

        :param fname: string with file name. Can be an absolute or relative path.
        :param fileformat: kind of format to use for the export. If not present,
            it will try to use the extension of the file name.
        """
        if fileformat is None:
            fileformat = fname.split('.')[-1]
        filecontent = self._exportstring(fileformat)
        with open(fname, 'w') as f:  # writes in cwd, if fname is not absolute
            f.write(filecontent)

    def _get_exporters(self):
        """
        Get all implemented export formats.
        The convention is to find all _prepare_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        # _prepare_"" with the name of the new format
        exporter_prefix = '_prepare_'
        method_names = dir(self)  # get list of class methods names
        valid_format_names = [i[len(exporter_prefix):] for i in method_names
                              if i.startswith(exporter_prefix)]  # filter them
        valid_formats = {k: getattr(self, exporter_prefix + k)
                         for k in valid_format_names}
        return valid_formats

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
            if len(importers.keys()) > 0:
                raise ValueError("The format {} is not implemented for {}. "
                                 "Currently implemented are: {}.".format(
                    fileformat, self.__class__.__name__,
                    ",".join(importers.keys())))
            else:
                raise ValueError("The format {} is not implemented for {}. "
                                 "No formats are implemented yet.".format(
                    fileformat, self.__class__.__name__))

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
        with open(fname, 'r') as f:  # reads in cwd, if fname is not absolute
            self.importstring(f.read(), fileformat)

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
        valid_format_names = [i[len(importer_prefix):] for i in method_names
                              if i.startswith(importer_prefix)]  # filter them
        valid_formats = {k: getattr(self, importer_prefix + k)
                         for k in valid_format_names}
        return valid_formats

    def convert(self, object_format=None, *args):
        """
        Convert the AiiDA StructureData into another python object

        :param object_format: Specify the output format
        """
        if object_format is None:
            raise ValueError("object_format must be provided")
        if not isinstance(object_format, basestring):
            raise ValueError('object_format should be a string')

        converters = self._get_converters()

        try:
            func = converters[object_format]
        except KeyError:
            if len(converters.keys()) > 0:
                raise ValueError(
                    "The format {} is not implemented for {}. "
                    "Currently implemented are: {}.".format(
                        object_format, self.__class__.__name__,
                        ",".join(converters.keys())))
            else:
                raise ValueError("The format {} is not implemented for {}. "
                                 "No formats are implemented yet.".format(
                    object_format, self.__class__.__name__))

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
        valid_format_names = [i[len(exporter_prefix):] for i in method_names
                              if i.startswith(exporter_prefix)]  # filter them
        valid_formats = {k: getattr(self, exporter_prefix + k)
                         for k in valid_format_names}
        return valid_formats

    def _validate(self):
        """
        Perform validation of the Data object.

        .. note:: validation of data source checks license and requires
            attribution to be provided in field 'description' of source in
            the case of any CC-BY* license. If such requirement is too
            strict, one can remove/comment it out.
        """

        super(Data, self)._validate()

        ## Validation of ``source`` is commented out due to Issue #9
        ## (https://bitbucket.org/epfl_theos/aiida_epfl/issues/9/)
        ##
        ## if self.source is not None and \
        ##    self.source.get('license', None) and \
        ##    self.source['license'].startswith('CC-BY') and \
        ##    self.source.get('description', None) is None:
        ##     raise ValidationError("License of the object ({}) requires "
        ##                           "attribution, while none is given in the "
        ##                           "description".format(self.source['license']))
