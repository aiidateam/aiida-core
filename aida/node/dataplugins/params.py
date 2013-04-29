"""
Implements a data type which is a list of parameters (possibly nested): 
basically, a json-compatible dictionary.

files = []
jsons = {
  'parameters': {the parameter dict}
  }
"""
class Params(Data):


    def template(self):
        '''
        Django template string which will substitute and {{ITEM}} with an attr called 'ITEM' if it exists.
        '''
        pass
        
        
    def store(self):
        '''
        Will use the template to create a text file if defined.
        '''
        pass