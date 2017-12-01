# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



from aiida.restapi.translator.node import NodeTranslator
from aiida.restapi.common.exceptions import RestInputValidationError
from flask import send_from_directory
import os

class CalculationTranslator(NodeTranslator):
    """
    Translator relative to resource 'calculations' and aiida class Calculation
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "calculations"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm.calculation import Calculation
    _aiida_class = Calculation
    # The string name of the AiiDA class
    _aiida_type = "calculation.Calculation"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(CalculationTranslator, self).__init__(
            Class=self.__class__, **kwargs)

    @staticmethod
    def get_files_list(base_path_length, dirobj, files=[]):
        for fname in dirobj.get_content_list():
            if dirobj.isfile(fname):
                filename = os.path.join(dirobj.abspath, fname)[base_path_length:]
                files.append(filename)
            elif dirobj.isdir(fname):
                CalculationTranslator.get_files_list(base_path_length, dirobj.get_subfolder(fname), files)
        return files

    @staticmethod
    def get_retrieved_inputs(node, filename=None, rtype=None):
        """
        Get the retrieved input files for job calculation
        :param node: aiida node
        :return: the retrieved input files for job calculation
        """

        if node.dbnode.type.startswith("calculation.job."):

            input_folder = node.folder.get_subfolder("raw_input")
            input_folder_path = input_folder.abspath

            if filename is not None:
                response = {}

                if rtype is None:
                    rtype = "download"

                if rtype == "download":
                    filepath = os.path.join(input_folder_path, filename)
                    dirpath = os.path.dirname(filepath)
                    fname = os.path.basename(filepath)

                    if os.path.isfile(filepath):
                        response["status"] = 200
                        response["data"] = send_from_directory(dirpath, fname)
                        response["filename"] = filename.replace("/", "_")
                    else:
                        error = "file {} does not exist".format(filename)
                        raise RestInputValidationError (error)

                else:
                    raise RestInputValidationError ("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            base_path_length = len(input_folder_path) + 1
            retrieved = CalculationTranslator.get_files_list(base_path_length, input_folder, [])
            return retrieved

        return []

    @staticmethod
    def get_retrieved_outputs(node, filename=None, rtype=None):
        """
        Get the retrieved output files for job calculation
        :param node: aiida node
        :return: the retrieved output files for job calculation
        """
        if node.dbnode.type.startswith("calculation.job."):
            response = {}

            try:
                fullpath = os.path.join(node.out.retrieved.get_abs_path(), "path")
            except AttributeError:
                response["status"] = 500
                response["data"] = "This node does not have an output with link retrieved"
                return response

            if filename is not None:
                if rtype is None:
                    rtype = "download"

                if rtype == "download":

                    filepath = os.path.join(fullpath, filename)
                    dirpath = os.path.dirname(filepath)
                    fname = os.path.basename(filepath)

                    if os.path.isfile(filepath):
                        response["status"] = 200
                        response["data"] = send_from_directory(dirpath, fname)
                        response["filename"] = filename.replace("/", "_")
                    else:
                        error = "file {} does not exist".format(filename)
                        raise RestInputValidationError (error)

                else:
                    raise RestInputValidationError ("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            retrieved = node.out.retrieved.get_folder_list()
            return retrieved

        return []


