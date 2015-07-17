# -*- coding: utf-8 -*-
from aiida.orm import Node

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

'''
Specifications of the Data class:
AiiDA Data objects are subclasses of Node and should have 

Multiple inheritance must be suppoted, i.e. Data should have methods for querying and
be able to inherit other library objects such as ASE for structures.

Architecture note:
The code plugin is responsible for converting a raw data object produced by code
to AiiDA standard object format. The data object then validates itself according to its
method. This is done independently in order to allow cross-validation of plugins.

'''


class Data(Node):
    _updatable_attributes = tuple()

    _source_attributes = ['db_name', 'db_uri', 'uri', 'id', 'version',
                          'extras', 'source_md5', 'description', 'license']

    @property
    def source(self):
        """
        :return: dictionary describing the source of Data object.
        """
        return self.get_attr('source', None)

    @source.setter
    def source(self, source):
        """
        Sets the dictionary describing the source of Data object.

        :raise AttributeError: if dictionary contains unknown field.
        :raise ValueError: if supplied source description is not a
            dictionary.
        """
        if not isinstance(source, dict):
            raise ValueError("Source must be supplied as a dictionary")
        unknown_attrs = list(set(source.keys()) - set(self._source_attributes))
        if unknown_attrs:
            raise AttributeError("Unknown source parameters: "
                                 "{}".format(", ".join(unknown_attrs)))

        self._set_attr('source', source)

    def set_source(self, source):
        """
        Sets the dictionary describing the source of Data object.
        """
        self.source = source

    def _add_link_from(self, src, label=None):
        from aiida.orm.calculation import Calculation

        if len(self.get_inputs()) > 0:
            raise ValueError("At most one node can enter a data node")

        if not isinstance(src, Calculation):
            raise ValueError("Links entering a data object can only be of type calculation")

        return super(Data, self)._add_link_from(src, label)

    def _can_link_as_output(self, dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        
        An output of a data can only be a calculation
        """
        from aiida.orm import Calculation

        if not isinstance(dest, Calculation):
            raise ValueError("The output of a data node can only be a calculation")

        return super(Data, self)._can_link_as_output(dest)

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
                raise ValueError("The format is not accepted. "
                                 "Currently implemented are: {}.".format(
                    ",".join(exporters.keys())))
            else:
                raise ValueError("The format is not accepted. "
                                 "No formats are implemented yet.")

        return func(**kwargs)

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
            if len(exporters.keys()) > 0:
                raise ValueError("The format is not accepted. "
                                 "Currently implemented are: {}.".format(
                    ",".join(exporters.keys())))
            else:
                raise ValueError("The format is not accepted. "
                                 "No formats are implemented yet.")

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
        """
        from aiida.common.exceptions import ValidationError

        super(Data, self)._validate()

        if self.source is not None and \
           self.source.get('license', None) and \
           self.source['license'].startswith('CC-BY') and \
           self.source.get('description', None) is None:
            raise ValidationError("License of the object ({}) requires "
                                  "attribution, while none is given in the "
                                  "description".format(self.source['license']))
