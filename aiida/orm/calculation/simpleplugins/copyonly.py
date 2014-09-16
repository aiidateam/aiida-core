# -*- coding: utf-8 -*-
"""
Plugin to create a fake calculation, that only copies files and folders.
"""
import os, copy
from aiida.orm import Calculation
from aiida.common.exceptions import InputValidationError,ValidationError
from aiida.common.datastructures import CalcInfo
from aiida.orm.calculation.quantumespresso import get_input_data_text,_lowercase_dict,_uppercase_dict
from aiida.common.exceptions import UniquenessError
from aiida.common.utils import classproperty
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.remote import RemoteData 

# List of namelists (uppercase) that are allowed to be found in the
# input_data, in the correct order

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

    
# in restarts, will not copy but use symlinks
_default_symlink_usage = False

class CopyonlyCalculation(Calculation):
    '''
    Fake calculation class to copy some files or folders from several 
    parent calculations, onto a new remote destination.
    '''
    
    def __init__(self,**kwargs):
        
        super(CopyonlyCalculation, self).__init__(**kwargs)
    
    def _init_internal_params(self):

        super(CopyonlyCalculation, self)._init_internal_params()
        # no parser
        self._default_parser = None

    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the class.
        """
        retdict = Calculation._use_methods
        retdict.update({
            "copy_list": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'copy_list',
               'docstring': ("Use a ParameterData of the form {'INPUT': copy_list}"
                             " with copy_list a list of length-3 tuples of the form"
                             " (parent_label, remote_folder_or_file_to_copy_from_parent, "
                             "relative_destination_in_output_remote_folder )."
                             "NOTE: if destination is a folder, it should end with /"),
               },
            "parent_folder": {
               'valid_types': RemoteData,
               'additional_parameter': "label",
               'linkname': cls._get_linkname_parent,
               'docstring': ("Use a remote folder as parent folder"),
               },
            })
        return retdict
    
    @classmethod
    def _get_linkname_parent_prefix(cls):
        """
        The prefix for the name of the links used for the parent folders
        """
        return "parent_folder_"

    @classmethod
    def _get_linkname_parent(cls, label):
        """
        The name of the link used for the pseudo for kind 'kind'. 
        It appends the pseudo name to the pseudo_prefix, as returned by the
        _get_linkname_pseudo_prefix() method.
        
        :param label: a string to identify the link name
        """
        return "{}{}".format(cls._get_linkname_parent_prefix(),label)

    def use_parent_calculation(self,parent_calc,label):
        """
        Set a parent calculation of the current CopyonlyCalculation, 
        from which it will inherit the output subfolder.
        The link will be created from parent RemoteData to CopyonlyCalculation.
        :param calc: the parent calculation.
        :param label: a string to identify it (will be used as part of linkname)
        """
        from aiida.common.exceptions import NotExistent
        
        if ( not isinstance(parent_calc,Calculation)):
            raise ValueError("Parent calculation must be a Calculation")
        
        remotedatas = parent_calc.get_outputs(type=RemoteData)
        if not remotedatas:
            raise NotExistent("No output remotedata found in "
                                  "the parent (pk={})".format(parent_calc.pk))
        if len(remotedatas) != 1:
            raise UniquenessError("More than one output remotedata found in "
                                  "the parent (pk={})".format(parent_calc.pk))
        remotedata = remotedatas[0]
        
        self.use_parent_folder(remotedata,label)

    def _prepare_for_submission(self,tempfolder,inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """

        remote_copy_list = []
        
        input_param = inputdict.pop(self.get_linkname('copy_list'),None)
        if input_param is None:
            raise InputValidationError("No copy_list found in input parameters.")
        
        list_of_files_to_copy = input_param.get_dict().get('INPUT',None)
        
        if ( ( not isinstance(list_of_files_to_copy, list)
               or any(not isinstance(elem,list) and not isinstance(elem,tuple) for elem in list_of_files_to_copy) )
               or any(len(elem)!=3 for elem in list_of_files_to_copy) ):
            raise InputValidationError("Parameters dictionary in copy_list must "
                                       "be of the form: "
                                       "{'INPUT': list of length-3 tuples}")

        # getting computer of the current fake calculation
        new_comp = self.get_computer()
        # list of parent labels
        parent_label_list=[]
        
        # build remote_copy_list
        for parent_label,origin,destination in list_of_files_to_copy:

            # get parent remote data
            parent_folder = inputdict.get(self.get_linkname('parent_folder',
                                                                parent_label))
            if parent_folder is None:
                raise InputValidationError("Parent calculation with label {} "
                                           "not found in the input parent "
                                           "calculations".format(parent_label))
            
            # check that this parent calculation is on the same computer as the
            # copyonlycalculation
            parent_comp = parent_folder.get_computer()
            if ( not new_comp.uuid == parent_comp.uuid ):
                raise InputValidationError("Parent (pk={0}) of CopyonlyCalculation "
                                           "should be on computer {1}".format(parent_folder.pk,
                                                                 new_comp.get_name))
            
            # split destination to extract potential subfolders to be created
            subfolder_name = os.path.split(destination)[0]
            if len(subfolder_name)>0:
                # create subfolder
                tempfolder.get_subfolder(subfolder_name, create=True)
            
            # here I add to the remote copy list
            remote_copy_list.append(
                (parent_comp.uuid,
                 os.path.join(parent_folder.get_remote_path(),origin),
                 destination))
            
            # add the current parent label to the list of already used labels
            if parent_label not in parent_label_list:
                parent_label_list.append(parent_label)
        
        # pop all used parents from inputdict
        for parent_label in parent_label_list:
            inputdict.pop(self.get_linkname('parent_folder', parent_label))
        
        # Here, there should be no other inputs leftS
        if inputdict:
            raise InputValidationError("The following input data nodes are "
                "not recognized: {}".format(inputdict.keys()))
        
        calcinfo = CalcInfo()
        
        calcinfo.uuid = self.uuid
        # Empty command line by default
        calcinfo.cmdline_params = None
        calcinfo.local_copy_list = None
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = None
        calcinfo.stdin_name = ""
        calcinfo.stdout_name = ""
        
        return calcinfo
