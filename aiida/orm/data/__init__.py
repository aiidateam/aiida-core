# -*- coding: utf-8 -*-
from aiida.orm import Node

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

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
               
    def _add_link_from(self,src,label=None):
        from aiida.orm.calculation import Calculation

        if len(self.get_inputs()) > 0:
            raise ValueError("At most one node can enter a data node")
        
        if not isinstance(src, Calculation):
            raise ValueError("Links entering a data object can only be of type calculation")
        
        return super(Data,self)._add_link_from(src,label)
    
    def _can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        
        An output of a data can only be a calculation
        """
        from aiida.orm import Calculation
        
        if not isinstance(dest, Calculation):
            raise ValueError("The output of a data node can only be a calculation")

        return super(Data, self)._can_link_as_output(dest)
    
    def _exportstring(self, fileformat):
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
                                    ",".join(exporters.keys())) )
            else:
                raise ValueError("The format is not accepted. "
                                 "No formats are implemented yed.")

        return func()

    def export(self,fname,fileformat=None):
        """
        Save a Data object to a file.

        :param fname: string with file name. Can be an absolute or relative path.
        :param fileformat: kind of format to use for the export. If not present,
            it will try to use the extension of the file name.
        """
        if fileformat is None:
            fileformat = fname.split('.')[-1]
        filecontent = self._exportstring(fileformat)
        with open(fname,'w') as f:  # writes in cwd, if fname is not absolute
            f.write( filecontent )

    def _get_exporters(self):
        """
        Get all implemented export formats.
        The convention is to find all _prepare_... methods.
        Returns a list of strings.
        """
        # NOTE: To add support for a new format, write a new function called as
        #       _prepare_"" with the name of the new format
        exporter_prefix = '_prepare_'
        method_names = dir(self) # get list of class methods names
        valid_format_names = [ i[len(exporter_prefix):] for i in method_names
                         if i.startswith(exporter_prefix) ] # filter them
        valid_formats = {k: getattr(self,exporter_prefix + k)
                         for k in valid_format_names}
        return valid_formats
