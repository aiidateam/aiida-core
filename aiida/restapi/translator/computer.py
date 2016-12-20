from aiida.restapi.translator.base import BaseTranslator
from aiida.restapi.common.config import custom_schema

class ComputerTranslator(BaseTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Computers or the
    details of one computer

    Supported REST requests:
    - http://base_url/computer?filters
    - http://base_url/computer/pk

    **Please NOTE that filters are not allowed to get computer details

    Pk         : pk of the computer
    Filters    : filters dictionary to apply on
                 computer list. Not applicable to single computer.
    order_by   : used to sort computer list. Not applicable to
                 single computer
    end_points : NA
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of computers or details of single computer

    EXAMPLES:
    ex1::
    ct = ComputerTranslator()
    ct.add_filters(node_pk)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    ex2::
    ct = ComputerTranslator()
    ct.add_filters(filters_dict)
    query_help = ct.get_query_help()
    qb = QueryBuilder(**query_help)
    data = ct.formatted_result(qb)

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "computers"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "computer.Computer"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'computer'

    _result_type = __label__

    _default_projections = custom_schema['columns'][__label__]

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(ComputerTranslator, self).__init__()

    def get_schema(self):
        return {
            "fields": {
                "description": {
                    "is_display": True,
                    "display_name": "Description",
                    "help_text": "short description of the Computer",
                    "type": "string",
                },
                "enabled": {
                    "is_display": True,
                    "display_name": "Enabled",
                    "help_text": "Is the computer enabled to run jobs",
                    "type": "boolean",
                },
                "hostname": {
                    "is_display": True,
                    "display_name": "Hostname",
                    "help_text": "Host name of the computer",
                    "type": "string",
                },
                "id": {
                    "is_display": True,
                    "display_name": "ID",
                    "help_text": "Id of the computer",
                    "type": "integer",
                },
                "metadata": {
                    "is_display": False,
                    "display_name": "Metadata",
                    "help_text": "Additional metadata information of the computer",
                    "type": "dictionary",
                },
                "name": {
                    "is_display": False,
                    "display_name": "Name",
                    "help_text": "Name of the computer",
                    "type": "string",
                },
                "resource_uri": {
                    "is_display": False,
                    "display_name": "Resource URI",
                    "help_text": "Resource URI (REST url)",
                    "type": "string",
                },
                "scheduler_type": {
                    "is_display": True,
                    "display_name": "Scheduler Type",
                    "help_text": "Scheduler type",
                    "type": "string",
                    "valid_choices": {
                        "direct": {
                            "doc": "Support for the direct execution bypassing schedulers."
                        },
                        "pbsbaseclasses.PbsBaseClass": {
                            "doc": "Base class with support for the PBSPro scheduler"
                        },
                        "pbspro": {
                            "doc": "Subclass to support the PBSPro scheduler"
                        },
                        "sge": {
                            "doc": "Support for the Sun Grid Engine scheduler and its variants/forks (Son of Grid Engine, Oracle Grid Engine, ...)"
                        },
                        "slurm": {
                            "doc": "Support for the SLURM scheduler (http://slurm.schedmd.com/)."
                        },
                        "torque": {
                            "doc": "Subclass to support the Torque scheduler.."
                        }
                    }
                },
                "transport_params": {
                    "is_display": False,
                    "display_name": "Transport Parameters",
                    "help_text": "Transport Parameters",
                    "type": "dictionary",
                },
                "transport_type": {
                    "is_display": True,
                    "display_name": "Transport Type",
                    "help_text": "Transport Type",
                    "type": "string",
                    "valid_choices": {
                        "local": {
                            "doc": "Support copy and command execution on the same host on which AiiDA is running via direct file copy and execution commands."
                        },
                        "ssh": {
                            "doc": "Support connection, command execution and data transfer to remote computers via SSH+SFTP."
                        }
                    }
                },
                "uuid": {
                    "is_display": False,
                    "display_name": "Unique ID",
                    "help_text": "Unique ID",
                    "type": "string",
                }
            },
            "ordering": [
                "id",
                "name",
                "hostname",
                "description",
                "transport_type",
                "scheduler_type",
                "enabled",
                "uuid",
            ]
        }
