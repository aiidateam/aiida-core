from aida.common.extendeddicts import DefaultFieldsAttributeDict

class CalcInfo(DefaultFieldsAttributeDict):
    _default_fields = (
        'job_environment',
        'email',
        'emailOnStarted',
        'emailOnTerminated',
        'uuid',
        'prependText', # (both from computer and code)
        'appendText',  # (both from computer and code)
        'argv',         # (including everything, also mpirun etc.; argv[0] is
                        #   the executable
        'stdinName',
        'stdoutName',
        'stderrName',
        'joinFiles',
        'queueName', 
        'numNodes',
        'numCpusPerNode',
        'priority',
        'resourceLimits',
        'rerunnable',
        )

