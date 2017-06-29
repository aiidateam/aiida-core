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

