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

        ## calculation schema
        # All the values from column_order must present in additional info dict
        # Note: final schema will contain details for only the fields present in column order
        self._schema_projections = {
            "column_order": [
                "id",
                "label",
                "type",
                "ctime",
                "mtime",
                "uuid",
                "user_id",
                "user_email",
                "attributes.state",
                "attributes",
                "extras"
            ],
            "additional_info": {
                "id": {"is_display": True},
                "label": {"is_display": False},
                "type": {"is_display": True},
                "ctime": {"is_display": True},
                "mtime": {"is_display": True},
                "uuid": {"is_display": False},
                "user_id": {"is_display": False},
                "user_email": {"is_display": True},
                "attributes.state": {"is_display": True},
                "attributes": {"is_display": False},
                "extras": {"is_display": False}
            }
        }

    @staticmethod
    def get_files_list(dirobj, files=None, prefix=None):
        if files is None:
            files = []
        if prefix is None:
            prefix = []
        for fname in dirobj.get_content_list():
            if dirobj.isfile(fname):
                filename = os.path.join(*(prefix + [fname]))
                files.append(filename)
            elif dirobj.isdir(fname):
                CalculationTranslator.get_files_list(dirobj.get_subfolder(fname), files, prefix + [fname])
        return files


    @staticmethod
    def get_retrieved_inputs(node, filename=None, rtype=None):
        """
        Get the submitted input files for job calculation
        :param node: aiida node
        :return: the retrieved input files for job calculation
        """

        if node.type.startswith("calculation.job."):

            input_folder = node._raw_input_folder

            if filename is not None:
                response = {}

                if rtype is None:
                    rtype = "download"

                if rtype == "download":
                    try:
                        content = NodeTranslator.get_file_content(input_folder, filename)
                    except IOError as e:
                        error = "Error in getting {} content".format(filename)
                        raise RestInputValidationError (error)

                    response["status"] = 200
                    response["data"] = content
                    response["filename"] = filename.replace("/", "_")

                else:
                    raise RestInputValidationError("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            retrieved = CalculationTranslator.get_files_list(input_folder)
            return retrieved

        return []

    @staticmethod
    def get_retrieved_outputs(node, filename=None, rtype=None):
        """
        Get the retrieved output files for job calculation
        :param node: aiida node
        :return: the retrieved output files for job calculation
        """

        if node.type.startswith("calculation.job."):

            retrieved_folder = node.out.retrieved
            response = {}

            if retrieved_folder is None:
                response["status"] = 200
                response["data"] = "This node does not have retrieved folder"
                return response

            output_folder = retrieved_folder._get_folder_pathsubfolder

            if filename is not None:


                if rtype is None:
                    rtype = "download"

                if rtype == "download":
                    try:
                        content = NodeTranslator.get_file_content(output_folder, filename)
                    except IOError as e:
                        error = "Error in getting {} content".format(filename)
                        raise RestInputValidationError (error)

                    response["status"] = 200
                    response["data"] = content
                    response["filename"] = filename.replace("/", "_")

                else:
                    raise RestInputValidationError ("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            retrieved = CalculationTranslator.get_files_list(output_folder)
            return retrieved

        return []


