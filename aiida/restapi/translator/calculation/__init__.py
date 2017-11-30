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
    def get_retrived_inputs(node):
        """
        Get the retrieved input files for job calculation
        :param node: aiida node
        :return: the retrieved input files for job calculation
        """
        if node.dbnode.type.startswith("calculation.job."):
            try:
                fullpath = os.path.join(node.get_abs_path(), "raw_input")
                length = len(fullpath) + 1
                retrieved = []

                for (dirpath, dirnames, filenames) in os.walk(fullpath):
                    retrieved.extend([os.path.join(dirpath, f)[length:] for f in filenames])

                return retrieved

            except Exception as e:
                return e

        return []

    @staticmethod
    def get_retrived_outputs(node):
        """
        Get the retrieved output files for job calculation
        :param node: aiida node
        :return: the retrieved output files for job calculation
        """
        if node.dbnode.type.startswith("calculation.job."):
            try:
                fullpath = os.path.join(node.out.retrieved.get_abs_path(), "path")
                length = len(fullpath) + 1
                retrieved = []

                for (dirpath, dirnames, filenames) in os.walk(fullpath):
                    retrieved.extend([os.path.join(dirpath, f)[length:] for f in filenames])

                return retrieved

            except Exception as e:
                return e
        return []


