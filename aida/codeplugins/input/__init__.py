import aida.common

class InputPlugin(object):
    _logger = aida.common.aidalogger.getChild('inputplugin')
    
    def create(self,calculation,inputdata,tempfolder):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        Args:
            calculation: a aida.orm.Calculation object for the
                calculation to be submitted
            inputdata: a list of pairs ('label', DataObject)
                where 'label' is the label of the input link
                for this data object, and DataObject is (a subclass 
                of) the aida.orm.Data class.
            tempfolder: a aida.common.folders.Folder subclass where
                the plugin should put all its files.

        TODO: document what it has to return (probably a CalcInfo object)
              and what is the behavior on the tempfolder
        """
        raise NotImplementedError

    @property
    def logger(self):
        return self._logger
    
