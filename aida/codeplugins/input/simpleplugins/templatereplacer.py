"""
This is a simple plugin that takes two node inputs, both of type ParameterData,
with the following labels: template and parameters
* parameters: a set of parameters that will be used for substitution.
  You can 
* template: can contain three parameters:
    * input_file_template: a string with substitutions to be managed with the format()
      function of python, i.e. if you want to substitute a variable called 'varname', you write
      {varname} in the text. See http://www.python.org/dev/peps/pep-3101/ for more
      details. The replaced file will be the input file.
    * input_file_name: a string with the file name for the input. If it is not provided, no
      file will be created.
    * output_file_name: a string with the file name for the output. If it is not provided, no
      redirection will be done and the output will go in the scheduler output file.
    * cmdline_params: a list of strings, to be passed as command line parameters.
      Each one is substituted with the same rule of input_file_template. Optional
    * input_through_stdin: if True, the input file name is passed via stdin. Default is
      False if missing.

TODO: probably use Python's Template strings instead??
TODO: catch exceptions
"""
from aida.codeplugins.input import InputPlugin
from aida.codeplugins.exceptions import InputValidationError
from aida.common.datastructures import CalcInfo

# TODO: write a 'input_type_checker' routine to automatically check the existence
# and type of inputs + default values etc.
class TemplatereplacerInputPlugin(InputPlugin):
    _logger = InputPlugin._logger.getChild("templatereplacer")
    
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
        from aida.orm.dataplugins.parameter import ParameterData
        import StringIO
        
        inputdict = dict(inputdata)

        parameters_node = inputdict.pop('parameters', None)
        if parameters_node is None:
            parameters = {}
        else:
            if not isinstance(parameters_node,ParameterData):
                raise InputValidationError("'parameters' data is not of type ParameterData")
            parameters = dict(parameters_node.iterattrs())

        template_node = inputdict.pop('template', None)
        if template_node is None:
            raise InputValidationError("No 'template' input data")
        if not isinstance(parameters_node,ParameterData):
            raise InputValidationError("'parameters' data is not of type ParameterData")
        template = dict(template_node.iterattrs())

        if len(inputdict) > 0:
            raise InputValidationError("The input nodes with the following labels could not be "
                                       "used by the templatereplacer plugin: {}".format(
                                       inputdict.keys()))

        input_file_template = template.pop('input_file_template', "")
        input_file_name = template.pop('input_file_name', None)
        output_file_name = template.pop('output_file_name', None)
        cmdline_params_tmpl = template.pop('cmdline_params', [])
        input_through_stdin = template.pop('input_through_stdin', False)

        if input_through_stdin and input_file_name is None:
            raise InputValidationError("If you ask for input_through_stdin you have to "
                                       "specify a input_file_name")

        if template:
            raise InputValidationError("The following keys could not be "
                                       "used in the template node: {}".format(
                                       template.keys()))
            
        input_file = StringIO.StringIO(input_file_template.format(**parameters))
        if input_file_name:
            tempfolder.create_file_from_filelike(input_file_content)
        else:
            if input_file_template:
                self.logger.warning("No input file name passed, but a input file template is present")
        
        cmdline_params = [i.format(**parameters) for i in cmdline_params_tmpl]

        calcinfo = CalcInfo()

        calcinfo.uuid = calculation.uuid
        calcinfo.argv = cmdline_params # This will be enriched outside
        if input_through_stdin is not None:
            calcinfo.stdinName = input_file_name
        if output_file_name:
            calcinfo.stdoutName = output_file_name

        #        'job_environment',
        #        'prependText', # (both from computer and code)
        #        'appendText',  # (both from computer and code)
        #        'stderrName',
        #        'joinFiles',

        # TODO: implement in the CalcInfo objects the fields for 
        
        return calcinfo
