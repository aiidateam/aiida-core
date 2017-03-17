from aiida.restapi.translator.data import DataTranslator

class BandsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'bands' and aiida class BandsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "bands"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "data.array.bands.BandsData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(BandsDataTranslator, self).__init__(Class=self.__class__,
                                                  **kwargs)


    def get_visualization_data(self, node):
        """

        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        """

        import numpy as np




        return json_content

