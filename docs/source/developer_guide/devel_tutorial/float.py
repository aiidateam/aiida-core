from aiida.orm.data import Data

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"

class FloatData(Data):

    @property
    def value(self):
        """
        The value of the Float
        """
        return self.get_attr('number')

    @value.setter
    def value(self,value):
        """
        Set the value of the Float
        """
        self._set_attr('number', float(value))

