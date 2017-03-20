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


        """
        Strategy: I take advantage of the export functionality of BandsData
        objects. The raw export has to be filtered for string escape characters.
        this is done by decoding the string returned by node._exportstring.

        TODO: modify the function exportstring (or add another function in
        BandsData) so that it returns a python object rather than a string.
        """

        import ujson as uj
        json_string = node._exportstring('json', comments=False)
        json_content = uj.decode(json_string)

        return json_content

