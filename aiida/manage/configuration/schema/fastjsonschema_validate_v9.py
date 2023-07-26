# -*- coding: utf-8 -*-
# pylint: disable=W,C,R
# pylint: disable=too-many-lines
# Generated as:
# python3 -m fastjsonschema < config-v9.schema.json > fastjsonschema_validate_v9.py
# WARNING: Must be regenerated up each schema version update!
VERSION = '2.17.1'
from decimal import Decimal
import re


class JsonSchemaException(ValueError):
    """
    Base exception of ``fastjsonschema`` library.
    """


class JsonSchemaValueException(JsonSchemaException):
    """
    Exception raised by validation function. Available properties:

     * ``message`` containing human-readable information what is wrong (e.g. ``data.property[index] must be smaller than or equal to 42``),
     * invalid ``value`` (e.g. ``60``),
     * ``name`` of a path in the data structure (e.g. ``data.property[index]``),
     * ``path`` as an array in the data structure (e.g. ``['data', 'property', 'index']``),
     * the whole ``definition`` which the ``value`` has to fulfil (e.g. ``{'type': 'number', 'maximum': 42}``),
     * ``rule`` which the ``value`` is breaking (e.g. ``maximum``)
     * and ``rule_definition`` (e.g. ``42``).

    .. versionchanged:: 2.14.0
        Added all extra properties.
    """

    def __init__(self, message, value=None, name=None, definition=None, rule=None):
        super().__init__(message)
        self.message = message
        self.value = value
        self.name = name
        self.definition = definition
        self.rule = rule

    @property
    def path(self):
        return [item for item in SPLIT_RE.split(self.name) if item != '']

    @property
    def rule_definition(self):
        if not self.rule or not self.definition:
            return None
        return self.definition.get(self.rule)


class JsonSchemaDefinitionException(JsonSchemaException):
    """
    Exception raised by generator of validation function.
    """

REGEX_PATTERNS = {'.+': re.compile('.+'), '\\d+': re.compile('\\d+')}

NoneType = type(None)


def validate(data, custom_formats={}, name_prefix=None):
    if not isinstance(data, (dict)):
        raise JsonSchemaValueException(
            '' + (name_prefix or 'data') + ' must be object',
            value=data,
            name='' + (name_prefix or 'data') + '',
            definition={
                '$schema': 'http://json-schema.org/draft-07/schema',
                'description': 'Schema for AiiDA configuration files, format version 9',
                'type': 'object',
                'definitions': {
                    'options': {
                        'type': 'object',
                        'properties': {
                            'runner.poll.interval': {
                                'type': 'integer',
                                'default': 60,
                                'minimum': 0,
                                'description': 'Polling interval in seconds to be used by process runners'
                            },
                            'daemon.default_workers': {
                                'type': 'integer',
                                'default': 1,
                                'minimum': 1,
                                'description': 'Default number of workers to be launched by `verdi daemon start`'
                            },
                            'daemon.timeout': {
                                'type': 'integer',
                                'default': 2,
                                'minimum': 0,
                                'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                            },
                            'daemon.worker_process_slots': {
                                'type': 'integer',
                                'default': 200,
                                'minimum': 1,
                                'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                            },
                            'daemon.recursion_limit': {
                                'type': 'integer',
                                'default': 3000,
                                'maximum': 100000,
                                'minimum': 1,
                                'description': 'Maximum recursion depth for the daemon workers'
                            },
                            'db.batch_size': {
                                'type': 'integer',
                                'default': 100000,
                                'minimum': 1,
                                'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                            },
                            'verdi.shell.auto_import': {
                                'type': 'string',
                                'default': '',
                                'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                            },
                            'logging.aiida_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                            },
                            'logging.verdi_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to console when running a `verdi` command'
                            },
                            'logging.db_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to the DbLog table'
                            },
                            'logging.plumpy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                            },
                            'logging.kiwipy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                            },
                            'logging.paramiko_loglevel': {
                                'key': 'logging_paramiko_log_level',
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                            },
                            'logging.alembic_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                            },
                            'logging.sqlalchemy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                            },
                            'logging.circus_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'INFO',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                            },
                            'logging.aiopika_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                            },
                            'warnings.showdeprecations': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print AiiDA deprecation warnings'
                            },
                            'warnings.development_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                'global_only': True
                            },
                            'warnings.rabbitmq_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                            },
                            'transport.task_retry_initial_interval': {
                                'type': 'integer',
                                'default': 20,
                                'minimum': 1,
                                'description': 'Initial time interval for the exponential backoff mechanism.'
                            },
                            'transport.task_maximum_attempts': {
                                'type': 'integer',
                                'default': 5,
                                'minimum': 1,
                                'description': 'Maximum number of transport task attempts before a Process is Paused.'
                            },
                            'rest_api.profile_switching': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                'global_only': True
                            },
                            'rmq.task_timeout': {
                                'type': 'integer',
                                'default': 10,
                                'minimum': 1,
                                'description': 'Timeout in seconds for communications with RabbitMQ'
                            },
                            'storage.sandbox': {
                                'type': 'string',
                                'description': 'Absolute path to the directory to store sandbox folders.'
                            },
                            'caching.default_enabled': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Enable calculation caching by default'
                            },
                            'caching.enabled_for': {
                                'description': 'Calculation entry points to enable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'caching.disabled_for': {
                                'description': 'Calculation entry points to disable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'autofill.user.email': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user email to use when creating new profiles.'
                            },
                            'autofill.user.first_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user first name to use when creating new profiles.'
                            },
                            'autofill.user.last_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user last name to use when creating new profiles.'
                            },
                            'autofill.user.institution': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user institution to use when creating new profiles.'
                            }
                        }
                    },
                    'profile': {
                        'type': 'object',
                        'required': ['storage', 'process_control'],
                        'properties': {
                            'PROFILE_UUID': {
                                'description': "The profile's unique key",
                                'type': 'string'
                            },
                            'storage': {
                                'description': 'The storage configuration',
                                'type': 'object',
                                'required': ['backend', 'config'],
                                'properties': {
                                    'backend': {
                                        'description': 'The storage backend type to use',
                                        'type': 'string',
                                        'default': 'psql_dos'
                                    },
                                    'config': {
                                        'description': 'The configuration to pass to the storage backend',
                                        'type': 'object',
                                        'properties': {
                                            'database_engine': {
                                                'type': 'string',
                                                'default': 'postgresql_psycopg2'
                                            },
                                            'database_port': {
                                                'type': ['integer', 'string'],
                                                'minimum': 1,
                                                'pattern': '\\d+',
                                                'default': 5432
                                            },
                                            'database_hostname': {
                                                'type': ['string', 'null'],
                                                'default': None
                                            },
                                            'database_username': {
                                                'type': 'string'
                                            },
                                            'database_password': {
                                                'type': ['string', 'null'],
                                                'default': None
                                            },
                                            'database_name': {
                                                'type': 'string'
                                            },
                                            'repository_uri': {
                                                'description': 'URI to the AiiDA object store',
                                                'type': 'string'
                                            }
                                        }
                                    }
                                }
                            },
                            'process_control': {
                                'description': 'The process control configuration',
                                'type': 'object',
                                'required': ['backend', 'config'],
                                'properties': {
                                    'backend': {
                                        'description': 'The process execution backend type to use',
                                        'type': 'string',
                                        'default': 'rabbitmq'
                                    },
                                    'config': {
                                        'description': 'The configuration to pass to the process execution backend',
                                        'type': 'object',
                                        'parameters': {
                                            'broker_protocol': {
                                                'description': 'Protocol for connecting to the RabbitMQ server',
                                                'type': 'string',
                                                'enum': ['amqp', 'amqps'],
                                                'default': 'amqp'
                                            },
                                            'broker_username': {
                                                'description': 'Username for RabbitMQ authentication',
                                                'type': 'string',
                                                'default': 'guest'
                                            },
                                            'broker_password': {
                                                'description': 'Password for RabbitMQ authentication',
                                                'type': 'string',
                                                'default': 'guest'
                                            },
                                            'broker_host': {
                                                'description': 'Hostname of the RabbitMQ server',
                                                'type': 'string',
                                                'default': '127.0.0.1'
                                            },
                                            'broker_port': {
                                                'description': 'Port of the RabbitMQ server',
                                                'type': 'integer',
                                                'minimum': 1,
                                                'default': 5672
                                            },
                                            'broker_virtual_host': {
                                                'description': 'RabbitMQ virtual host to connect to',
                                                'type': 'string',
                                                'default': ''
                                            },
                                            'broker_parameters': {
                                                'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                                'type': 'object',
                                                'default': {
                                                    'heartbeat': 600
                                                },
                                                'properties': {
                                                    'heartbeat': {
                                                        'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                        'type': 'integer',
                                                        'default': 600,
                                                        'minimum': 0
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            'default_user_email': {
                                'type': ['string', 'null'],
                                'default': None
                            },
                            'test_profile': {
                                'type': 'boolean',
                                'default': False
                            },
                            'options': {
                                'type': 'object',
                                'properties': {
                                    'runner.poll.interval': {
                                        'type': 'integer',
                                        'default': 60,
                                        'minimum': 0,
                                        'description': 'Polling interval in seconds to be used by process runners'
                                    },
                                    'daemon.default_workers': {
                                        'type': 'integer',
                                        'default': 1,
                                        'minimum': 1,
                                        'description': 'Default number of workers to be launched by `verdi daemon start`'
                                    },
                                    'daemon.timeout': {
                                        'type': 'integer',
                                        'default': 2,
                                        'minimum': 0,
                                        'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                                    },
                                    'daemon.worker_process_slots': {
                                        'type': 'integer',
                                        'default': 200,
                                        'minimum': 1,
                                        'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                                    },
                                    'daemon.recursion_limit': {
                                        'type': 'integer',
                                        'default': 3000,
                                        'maximum': 100000,
                                        'minimum': 1,
                                        'description': 'Maximum recursion depth for the daemon workers'
                                    },
                                    'db.batch_size': {
                                        'type': 'integer',
                                        'default': 100000,
                                        'minimum': 1,
                                        'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                                    },
                                    'verdi.shell.auto_import': {
                                        'type': 'string',
                                        'default': '',
                                        'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                                    },
                                    'logging.aiida_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'REPORT',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                                    },
                                    'logging.verdi_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'REPORT',
                                        'description': 'Minimum level to log to console when running a `verdi` command'
                                    },
                                    'logging.db_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'REPORT',
                                        'description': 'Minimum level to log to the DbLog table'
                                    },
                                    'logging.plumpy_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                                    },
                                    'logging.kiwipy_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                                    },
                                    'logging.paramiko_loglevel': {
                                        'key': 'logging_paramiko_log_level',
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                                    },
                                    'logging.alembic_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                                    },
                                    'logging.sqlalchemy_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                                    },
                                    'logging.circus_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'INFO',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                                    },
                                    'logging.aiopika_loglevel': {
                                        'type': 'string',
                                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                        'default': 'WARNING',
                                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                                    },
                                    'warnings.showdeprecations': {
                                        'type': 'boolean',
                                        'default': True,
                                        'description': 'Whether to print AiiDA deprecation warnings'
                                    },
                                    'warnings.development_version': {
                                        'type': 'boolean',
                                        'default': True,
                                        'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                        'global_only': True
                                    },
                                    'warnings.rabbitmq_version': {
                                        'type': 'boolean',
                                        'default': True,
                                        'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                                    },
                                    'transport.task_retry_initial_interval': {
                                        'type': 'integer',
                                        'default': 20,
                                        'minimum': 1,
                                        'description': 'Initial time interval for the exponential backoff mechanism.'
                                    },
                                    'transport.task_maximum_attempts': {
                                        'type': 'integer',
                                        'default': 5,
                                        'minimum': 1,
                                        'description': 'Maximum number of transport task attempts before a Process is Paused.'
                                    },
                                    'rest_api.profile_switching': {
                                        'type': 'boolean',
                                        'default': False,
                                        'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                        'global_only': True
                                    },
                                    'rmq.task_timeout': {
                                        'type': 'integer',
                                        'default': 10,
                                        'minimum': 1,
                                        'description': 'Timeout in seconds for communications with RabbitMQ'
                                    },
                                    'storage.sandbox': {
                                        'type': 'string',
                                        'description': 'Absolute path to the directory to store sandbox folders.'
                                    },
                                    'caching.default_enabled': {
                                        'type': 'boolean',
                                        'default': False,
                                        'description': 'Enable calculation caching by default'
                                    },
                                    'caching.enabled_for': {
                                        'description': 'Calculation entry points to enable caching on',
                                        'type': 'array',
                                        'default': [],
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'caching.disabled_for': {
                                        'description': 'Calculation entry points to disable caching on',
                                        'type': 'array',
                                        'default': [],
                                        'items': {
                                            'type': 'string'
                                        }
                                    },
                                    'autofill.user.email': {
                                        'type': 'string',
                                        'global_only': True,
                                        'description': 'Default user email to use when creating new profiles.'
                                    },
                                    'autofill.user.first_name': {
                                        'type': 'string',
                                        'global_only': True,
                                        'description': 'Default user first name to use when creating new profiles.'
                                    },
                                    'autofill.user.last_name': {
                                        'type': 'string',
                                        'global_only': True,
                                        'description': 'Default user last name to use when creating new profiles.'
                                    },
                                    'autofill.user.institution': {
                                        'type': 'string',
                                        'global_only': True,
                                        'description': 'Default user institution to use when creating new profiles.'
                                    }
                                }
                            }
                        }
                    }
                },
                'required': [],
                'properties': {
                    'CONFIG_VERSION': {
                        'description': 'The configuration version',
                        'type': 'object',
                        'required': ['CURRENT', 'OLDEST_COMPATIBLE'],
                        'properties': {
                            'CURRENT': {
                                'description': 'Version number of configuration file format',
                                'type': 'integer',
                                'const': 9
                            },
                            'OLDEST_COMPATIBLE': {
                                'description': 'Version number of oldest configuration file format this file is compatible with',
                                'type': 'integer',
                                'const': 9
                            }
                        }
                    },
                    'profiles': {
                        'description': 'Configured profiles',
                        'type': 'object',
                        'patternProperties': {
                            '.+': {
                                'type': 'object',
                                'required': ['storage', 'process_control'],
                                'properties': {
                                    'PROFILE_UUID': {
                                        'description': "The profile's unique key",
                                        'type': 'string'
                                    },
                                    'storage': {
                                        'description': 'The storage configuration',
                                        'type': 'object',
                                        'required': ['backend', 'config'],
                                        'properties': {
                                            'backend': {
                                                'description': 'The storage backend type to use',
                                                'type': 'string',
                                                'default': 'psql_dos'
                                            },
                                            'config': {
                                                'description': 'The configuration to pass to the storage backend',
                                                'type': 'object',
                                                'properties': {
                                                    'database_engine': {
                                                        'type': 'string',
                                                        'default': 'postgresql_psycopg2'
                                                    },
                                                    'database_port': {
                                                        'type': ['integer', 'string'],
                                                        'minimum': 1,
                                                        'pattern': '\\d+',
                                                        'default': 5432
                                                    },
                                                    'database_hostname': {
                                                        'type': ['string', 'null'],
                                                        'default': None
                                                    },
                                                    'database_username': {
                                                        'type': 'string'
                                                    },
                                                    'database_password': {
                                                        'type': ['string', 'null'],
                                                        'default': None
                                                    },
                                                    'database_name': {
                                                        'type': 'string'
                                                    },
                                                    'repository_uri': {
                                                        'description': 'URI to the AiiDA object store',
                                                        'type': 'string'
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'process_control': {
                                        'description': 'The process control configuration',
                                        'type': 'object',
                                        'required': ['backend', 'config'],
                                        'properties': {
                                            'backend': {
                                                'description': 'The process execution backend type to use',
                                                'type': 'string',
                                                'default': 'rabbitmq'
                                            },
                                            'config': {
                                                'description': 'The configuration to pass to the process execution backend',
                                                'type': 'object',
                                                'parameters': {
                                                    'broker_protocol': {
                                                        'description': 'Protocol for connecting to the RabbitMQ server',
                                                        'type': 'string',
                                                        'enum': ['amqp', 'amqps'],
                                                        'default': 'amqp'
                                                    },
                                                    'broker_username': {
                                                        'description': 'Username for RabbitMQ authentication',
                                                        'type': 'string',
                                                        'default': 'guest'
                                                    },
                                                    'broker_password': {
                                                        'description': 'Password for RabbitMQ authentication',
                                                        'type': 'string',
                                                        'default': 'guest'
                                                    },
                                                    'broker_host': {
                                                        'description': 'Hostname of the RabbitMQ server',
                                                        'type': 'string',
                                                        'default': '127.0.0.1'
                                                    },
                                                    'broker_port': {
                                                        'description': 'Port of the RabbitMQ server',
                                                        'type': 'integer',
                                                        'minimum': 1,
                                                        'default': 5672
                                                    },
                                                    'broker_virtual_host': {
                                                        'description': 'RabbitMQ virtual host to connect to',
                                                        'type': 'string',
                                                        'default': ''
                                                    },
                                                    'broker_parameters': {
                                                        'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                                        'type': 'object',
                                                        'default': {
                                                            'heartbeat': 600
                                                        },
                                                        'properties': {
                                                            'heartbeat': {
                                                                'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                                'type': 'integer',
                                                                'default': 600,
                                                                'minimum': 0
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'default_user_email': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'test_profile': {
                                        'type': 'boolean',
                                        'default': False
                                    },
                                    'options': {
                                        'description': 'Profile specific options',
                                        '$ref': '#/definitions/options'
                                    }
                                }
                            }
                        }
                    },
                    'default_profile': {
                        'description': 'Default profile to use',
                        'type': 'string'
                    },
                    'options': {
                        'type': 'object',
                        'properties': {
                            'runner.poll.interval': {
                                'type': 'integer',
                                'default': 60,
                                'minimum': 0,
                                'description': 'Polling interval in seconds to be used by process runners'
                            },
                            'daemon.default_workers': {
                                'type': 'integer',
                                'default': 1,
                                'minimum': 1,
                                'description': 'Default number of workers to be launched by `verdi daemon start`'
                            },
                            'daemon.timeout': {
                                'type': 'integer',
                                'default': 2,
                                'minimum': 0,
                                'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                            },
                            'daemon.worker_process_slots': {
                                'type': 'integer',
                                'default': 200,
                                'minimum': 1,
                                'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                            },
                            'daemon.recursion_limit': {
                                'type': 'integer',
                                'default': 3000,
                                'maximum': 100000,
                                'minimum': 1,
                                'description': 'Maximum recursion depth for the daemon workers'
                            },
                            'db.batch_size': {
                                'type': 'integer',
                                'default': 100000,
                                'minimum': 1,
                                'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                            },
                            'verdi.shell.auto_import': {
                                'type': 'string',
                                'default': '',
                                'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                            },
                            'logging.aiida_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                            },
                            'logging.verdi_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to console when running a `verdi` command'
                            },
                            'logging.db_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to the DbLog table'
                            },
                            'logging.plumpy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                            },
                            'logging.kiwipy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                            },
                            'logging.paramiko_loglevel': {
                                'key': 'logging_paramiko_log_level',
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                            },
                            'logging.alembic_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                            },
                            'logging.sqlalchemy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                            },
                            'logging.circus_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'INFO',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                            },
                            'logging.aiopika_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                            },
                            'warnings.showdeprecations': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print AiiDA deprecation warnings'
                            },
                            'warnings.development_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                'global_only': True
                            },
                            'warnings.rabbitmq_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                            },
                            'transport.task_retry_initial_interval': {
                                'type': 'integer',
                                'default': 20,
                                'minimum': 1,
                                'description': 'Initial time interval for the exponential backoff mechanism.'
                            },
                            'transport.task_maximum_attempts': {
                                'type': 'integer',
                                'default': 5,
                                'minimum': 1,
                                'description': 'Maximum number of transport task attempts before a Process is Paused.'
                            },
                            'rest_api.profile_switching': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                'global_only': True
                            },
                            'rmq.task_timeout': {
                                'type': 'integer',
                                'default': 10,
                                'minimum': 1,
                                'description': 'Timeout in seconds for communications with RabbitMQ'
                            },
                            'storage.sandbox': {
                                'type': 'string',
                                'description': 'Absolute path to the directory to store sandbox folders.'
                            },
                            'caching.default_enabled': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Enable calculation caching by default'
                            },
                            'caching.enabled_for': {
                                'description': 'Calculation entry points to enable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'caching.disabled_for': {
                                'description': 'Calculation entry points to disable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'autofill.user.email': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user email to use when creating new profiles.'
                            },
                            'autofill.user.first_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user first name to use when creating new profiles.'
                            },
                            'autofill.user.last_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user last name to use when creating new profiles.'
                            },
                            'autofill.user.institution': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user institution to use when creating new profiles.'
                            }
                        }
                    }
                }
            },
            rule='type'
        )
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_len = len(data)
        if not all(prop in data for prop in []):
            raise JsonSchemaValueException(
                '' + (name_prefix or 'data') + ' must contain [] properties',
                value=data,
                name='' + (name_prefix or 'data') + '',
                definition={
                    '$schema': 'http://json-schema.org/draft-07/schema',
                    'description': 'Schema for AiiDA configuration files, format version 9',
                    'type': 'object',
                    'definitions': {
                        'options': {
                            'type': 'object',
                            'properties': {
                                'runner.poll.interval': {
                                    'type': 'integer',
                                    'default': 60,
                                    'minimum': 0,
                                    'description': 'Polling interval in seconds to be used by process runners'
                                },
                                'daemon.default_workers': {
                                    'type': 'integer',
                                    'default': 1,
                                    'minimum': 1,
                                    'description': 'Default number of workers to be launched by `verdi daemon start`'
                                },
                                'daemon.timeout': {
                                    'type': 'integer',
                                    'default': 2,
                                    'minimum': 0,
                                    'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                                },
                                'daemon.worker_process_slots': {
                                    'type': 'integer',
                                    'default': 200,
                                    'minimum': 1,
                                    'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                                },
                                'daemon.recursion_limit': {
                                    'type': 'integer',
                                    'default': 3000,
                                    'maximum': 100000,
                                    'minimum': 1,
                                    'description': 'Maximum recursion depth for the daemon workers'
                                },
                                'db.batch_size': {
                                    'type': 'integer',
                                    'default': 100000,
                                    'minimum': 1,
                                    'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                                },
                                'verdi.shell.auto_import': {
                                    'type': 'string',
                                    'default': '',
                                    'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                                },
                                'logging.aiida_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                                },
                                'logging.verdi_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to console when running a `verdi` command'
                                },
                                'logging.db_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to the DbLog table'
                                },
                                'logging.plumpy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                                },
                                'logging.kiwipy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                                },
                                'logging.paramiko_loglevel': {
                                    'key': 'logging_paramiko_log_level',
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                                },
                                'logging.alembic_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                                },
                                'logging.sqlalchemy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                                },
                                'logging.circus_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'INFO',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                                },
                                'logging.aiopika_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                                },
                                'warnings.showdeprecations': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print AiiDA deprecation warnings'
                                },
                                'warnings.development_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                    'global_only': True
                                },
                                'warnings.rabbitmq_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                                },
                                'transport.task_retry_initial_interval': {
                                    'type': 'integer',
                                    'default': 20,
                                    'minimum': 1,
                                    'description': 'Initial time interval for the exponential backoff mechanism.'
                                },
                                'transport.task_maximum_attempts': {
                                    'type': 'integer',
                                    'default': 5,
                                    'minimum': 1,
                                    'description': 'Maximum number of transport task attempts before a Process is Paused.'
                                },
                                'rest_api.profile_switching': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                    'global_only': True
                                },
                                'rmq.task_timeout': {
                                    'type': 'integer',
                                    'default': 10,
                                    'minimum': 1,
                                    'description': 'Timeout in seconds for communications with RabbitMQ'
                                },
                                'storage.sandbox': {
                                    'type': 'string',
                                    'description': 'Absolute path to the directory to store sandbox folders.'
                                },
                                'caching.default_enabled': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Enable calculation caching by default'
                                },
                                'caching.enabled_for': {
                                    'description': 'Calculation entry points to enable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'caching.disabled_for': {
                                    'description': 'Calculation entry points to disable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'autofill.user.email': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user email to use when creating new profiles.'
                                },
                                'autofill.user.first_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user first name to use when creating new profiles.'
                                },
                                'autofill.user.last_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user last name to use when creating new profiles.'
                                },
                                'autofill.user.institution': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user institution to use when creating new profiles.'
                                }
                            }
                        },
                        'profile': {
                            'type': 'object',
                            'required': ['storage', 'process_control'],
                            'properties': {
                                'PROFILE_UUID': {
                                    'description': "The profile's unique key",
                                    'type': 'string'
                                },
                                'storage': {
                                    'description': 'The storage configuration',
                                    'type': 'object',
                                    'required': ['backend', 'config'],
                                    'properties': {
                                        'backend': {
                                            'description': 'The storage backend type to use',
                                            'type': 'string',
                                            'default': 'psql_dos'
                                        },
                                        'config': {
                                            'description': 'The configuration to pass to the storage backend',
                                            'type': 'object',
                                            'properties': {
                                                'database_engine': {
                                                    'type': 'string',
                                                    'default': 'postgresql_psycopg2'
                                                },
                                                'database_port': {
                                                    'type': ['integer', 'string'],
                                                    'minimum': 1,
                                                    'pattern': '\\d+',
                                                    'default': 5432
                                                },
                                                'database_hostname': {
                                                    'type': ['string', 'null'],
                                                    'default': None
                                                },
                                                'database_username': {
                                                    'type': 'string'
                                                },
                                                'database_password': {
                                                    'type': ['string', 'null'],
                                                    'default': None
                                                },
                                                'database_name': {
                                                    'type': 'string'
                                                },
                                                'repository_uri': {
                                                    'description': 'URI to the AiiDA object store',
                                                    'type': 'string'
                                                }
                                            }
                                        }
                                    }
                                },
                                'process_control': {
                                    'description': 'The process control configuration',
                                    'type': 'object',
                                    'required': ['backend', 'config'],
                                    'properties': {
                                        'backend': {
                                            'description': 'The process execution backend type to use',
                                            'type': 'string',
                                            'default': 'rabbitmq'
                                        },
                                        'config': {
                                            'description': 'The configuration to pass to the process execution backend',
                                            'type': 'object',
                                            'parameters': {
                                                'broker_protocol': {
                                                    'description': 'Protocol for connecting to the RabbitMQ server',
                                                    'type': 'string',
                                                    'enum': ['amqp', 'amqps'],
                                                    'default': 'amqp'
                                                },
                                                'broker_username': {
                                                    'description': 'Username for RabbitMQ authentication',
                                                    'type': 'string',
                                                    'default': 'guest'
                                                },
                                                'broker_password': {
                                                    'description': 'Password for RabbitMQ authentication',
                                                    'type': 'string',
                                                    'default': 'guest'
                                                },
                                                'broker_host': {
                                                    'description': 'Hostname of the RabbitMQ server',
                                                    'type': 'string',
                                                    'default': '127.0.0.1'
                                                },
                                                'broker_port': {
                                                    'description': 'Port of the RabbitMQ server',
                                                    'type': 'integer',
                                                    'minimum': 1,
                                                    'default': 5672
                                                },
                                                'broker_virtual_host': {
                                                    'description': 'RabbitMQ virtual host to connect to',
                                                    'type': 'string',
                                                    'default': ''
                                                },
                                                'broker_parameters': {
                                                    'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                                    'type': 'object',
                                                    'default': {
                                                        'heartbeat': 600
                                                    },
                                                    'properties': {
                                                        'heartbeat': {
                                                            'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                            'type': 'integer',
                                                            'default': 600,
                                                            'minimum': 0
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                'default_user_email': {
                                    'type': ['string', 'null'],
                                    'default': None
                                },
                                'test_profile': {
                                    'type': 'boolean',
                                    'default': False
                                },
                                'options': {
                                    'type': 'object',
                                    'properties': {
                                        'runner.poll.interval': {
                                            'type': 'integer',
                                            'default': 60,
                                            'minimum': 0,
                                            'description': 'Polling interval in seconds to be used by process runners'
                                        },
                                        'daemon.default_workers': {
                                            'type': 'integer',
                                            'default': 1,
                                            'minimum': 1,
                                            'description': 'Default number of workers to be launched by `verdi daemon start`'
                                        },
                                        'daemon.timeout': {
                                            'type': 'integer',
                                            'default': 2,
                                            'minimum': 0,
                                            'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                                        },
                                        'daemon.worker_process_slots': {
                                            'type': 'integer',
                                            'default': 200,
                                            'minimum': 1,
                                            'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                                        },
                                        'daemon.recursion_limit': {
                                            'type': 'integer',
                                            'default': 3000,
                                            'maximum': 100000,
                                            'minimum': 1,
                                            'description': 'Maximum recursion depth for the daemon workers'
                                        },
                                        'db.batch_size': {
                                            'type': 'integer',
                                            'default': 100000,
                                            'minimum': 1,
                                            'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                                        },
                                        'verdi.shell.auto_import': {
                                            'type': 'string',
                                            'default': '',
                                            'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                                        },
                                        'logging.aiida_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'REPORT',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                                        },
                                        'logging.verdi_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'REPORT',
                                            'description': 'Minimum level to log to console when running a `verdi` command'
                                        },
                                        'logging.db_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'REPORT',
                                            'description': 'Minimum level to log to the DbLog table'
                                        },
                                        'logging.plumpy_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                                        },
                                        'logging.kiwipy_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                                        },
                                        'logging.paramiko_loglevel': {
                                            'key': 'logging_paramiko_log_level',
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                                        },
                                        'logging.alembic_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                                        },
                                        'logging.sqlalchemy_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                                        },
                                        'logging.circus_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'INFO',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                                        },
                                        'logging.aiopika_loglevel': {
                                            'type': 'string',
                                            'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                            'default': 'WARNING',
                                            'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                                        },
                                        'warnings.showdeprecations': {
                                            'type': 'boolean',
                                            'default': True,
                                            'description': 'Whether to print AiiDA deprecation warnings'
                                        },
                                        'warnings.development_version': {
                                            'type': 'boolean',
                                            'default': True,
                                            'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                            'global_only': True
                                        },
                                        'warnings.rabbitmq_version': {
                                            'type': 'boolean',
                                            'default': True,
                                            'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                                        },
                                        'transport.task_retry_initial_interval': {
                                            'type': 'integer',
                                            'default': 20,
                                            'minimum': 1,
                                            'description': 'Initial time interval for the exponential backoff mechanism.'
                                        },
                                        'transport.task_maximum_attempts': {
                                            'type': 'integer',
                                            'default': 5,
                                            'minimum': 1,
                                            'description': 'Maximum number of transport task attempts before a Process is Paused.'
                                        },
                                        'rest_api.profile_switching': {
                                            'type': 'boolean',
                                            'default': False,
                                            'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                            'global_only': True
                                        },
                                        'rmq.task_timeout': {
                                            'type': 'integer',
                                            'default': 10,
                                            'minimum': 1,
                                            'description': 'Timeout in seconds for communications with RabbitMQ'
                                        },
                                        'storage.sandbox': {
                                            'type': 'string',
                                            'description': 'Absolute path to the directory to store sandbox folders.'
                                        },
                                        'caching.default_enabled': {
                                            'type': 'boolean',
                                            'default': False,
                                            'description': 'Enable calculation caching by default'
                                        },
                                        'caching.enabled_for': {
                                            'description': 'Calculation entry points to enable caching on',
                                            'type': 'array',
                                            'default': [],
                                            'items': {
                                                'type': 'string'
                                            }
                                        },
                                        'caching.disabled_for': {
                                            'description': 'Calculation entry points to disable caching on',
                                            'type': 'array',
                                            'default': [],
                                            'items': {
                                                'type': 'string'
                                            }
                                        },
                                        'autofill.user.email': {
                                            'type': 'string',
                                            'global_only': True,
                                            'description': 'Default user email to use when creating new profiles.'
                                        },
                                        'autofill.user.first_name': {
                                            'type': 'string',
                                            'global_only': True,
                                            'description': 'Default user first name to use when creating new profiles.'
                                        },
                                        'autofill.user.last_name': {
                                            'type': 'string',
                                            'global_only': True,
                                            'description': 'Default user last name to use when creating new profiles.'
                                        },
                                        'autofill.user.institution': {
                                            'type': 'string',
                                            'global_only': True,
                                            'description': 'Default user institution to use when creating new profiles.'
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'required': [],
                    'properties': {
                        'CONFIG_VERSION': {
                            'description': 'The configuration version',
                            'type': 'object',
                            'required': ['CURRENT', 'OLDEST_COMPATIBLE'],
                            'properties': {
                                'CURRENT': {
                                    'description': 'Version number of configuration file format',
                                    'type': 'integer',
                                    'const': 9
                                },
                                'OLDEST_COMPATIBLE': {
                                    'description': 'Version number of oldest configuration file format this file is compatible with',
                                    'type': 'integer',
                                    'const': 9
                                }
                            }
                        },
                        'profiles': {
                            'description': 'Configured profiles',
                            'type': 'object',
                            'patternProperties': {
                                '.+': {
                                    'type': 'object',
                                    'required': ['storage', 'process_control'],
                                    'properties': {
                                        'PROFILE_UUID': {
                                            'description': "The profile's unique key",
                                            'type': 'string'
                                        },
                                        'storage': {
                                            'description': 'The storage configuration',
                                            'type': 'object',
                                            'required': ['backend', 'config'],
                                            'properties': {
                                                'backend': {
                                                    'description': 'The storage backend type to use',
                                                    'type': 'string',
                                                    'default': 'psql_dos'
                                                },
                                                'config': {
                                                    'description': 'The configuration to pass to the storage backend',
                                                    'type': 'object',
                                                    'properties': {
                                                        'database_engine': {
                                                            'type': 'string',
                                                            'default': 'postgresql_psycopg2'
                                                        },
                                                        'database_port': {
                                                            'type': ['integer', 'string'],
                                                            'minimum': 1,
                                                            'pattern': '\\d+',
                                                            'default': 5432
                                                        },
                                                        'database_hostname': {
                                                            'type': ['string', 'null'],
                                                            'default': None
                                                        },
                                                        'database_username': {
                                                            'type': 'string'
                                                        },
                                                        'database_password': {
                                                            'type': ['string', 'null'],
                                                            'default': None
                                                        },
                                                        'database_name': {
                                                            'type': 'string'
                                                        },
                                                        'repository_uri': {
                                                            'description': 'URI to the AiiDA object store',
                                                            'type': 'string'
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        'process_control': {
                                            'description': 'The process control configuration',
                                            'type': 'object',
                                            'required': ['backend', 'config'],
                                            'properties': {
                                                'backend': {
                                                    'description': 'The process execution backend type to use',
                                                    'type': 'string',
                                                    'default': 'rabbitmq'
                                                },
                                                'config': {
                                                    'description': 'The configuration to pass to the process execution backend',
                                                    'type': 'object',
                                                    'parameters': {
                                                        'broker_protocol': {
                                                            'description': 'Protocol for connecting to the RabbitMQ server',
                                                            'type': 'string',
                                                            'enum': ['amqp', 'amqps'],
                                                            'default': 'amqp'
                                                        },
                                                        'broker_username': {
                                                            'description': 'Username for RabbitMQ authentication',
                                                            'type': 'string',
                                                            'default': 'guest'
                                                        },
                                                        'broker_password': {
                                                            'description': 'Password for RabbitMQ authentication',
                                                            'type': 'string',
                                                            'default': 'guest'
                                                        },
                                                        'broker_host': {
                                                            'description': 'Hostname of the RabbitMQ server',
                                                            'type': 'string',
                                                            'default': '127.0.0.1'
                                                        },
                                                        'broker_port': {
                                                            'description': 'Port of the RabbitMQ server',
                                                            'type': 'integer',
                                                            'minimum': 1,
                                                            'default': 5672
                                                        },
                                                        'broker_virtual_host': {
                                                            'description': 'RabbitMQ virtual host to connect to',
                                                            'type': 'string',
                                                            'default': ''
                                                        },
                                                        'broker_parameters': {
                                                            'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                                            'type': 'object',
                                                            'default': {
                                                                'heartbeat': 600
                                                            },
                                                            'properties': {
                                                                'heartbeat': {
                                                                    'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                                    'type': 'integer',
                                                                    'default': 600,
                                                                    'minimum': 0
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        'default_user_email': {
                                            'type': ['string', 'null'],
                                            'default': None
                                        },
                                        'test_profile': {
                                            'type': 'boolean',
                                            'default': False
                                        },
                                        'options': {
                                            'description': 'Profile specific options',
                                            '$ref': '#/definitions/options'
                                        }
                                    }
                                }
                            }
                        },
                        'default_profile': {
                            'description': 'Default profile to use',
                            'type': 'string'
                        },
                        'options': {
                            'type': 'object',
                            'properties': {
                                'runner.poll.interval': {
                                    'type': 'integer',
                                    'default': 60,
                                    'minimum': 0,
                                    'description': 'Polling interval in seconds to be used by process runners'
                                },
                                'daemon.default_workers': {
                                    'type': 'integer',
                                    'default': 1,
                                    'minimum': 1,
                                    'description': 'Default number of workers to be launched by `verdi daemon start`'
                                },
                                'daemon.timeout': {
                                    'type': 'integer',
                                    'default': 2,
                                    'minimum': 0,
                                    'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                                },
                                'daemon.worker_process_slots': {
                                    'type': 'integer',
                                    'default': 200,
                                    'minimum': 1,
                                    'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                                },
                                'daemon.recursion_limit': {
                                    'type': 'integer',
                                    'default': 3000,
                                    'maximum': 100000,
                                    'minimum': 1,
                                    'description': 'Maximum recursion depth for the daemon workers'
                                },
                                'db.batch_size': {
                                    'type': 'integer',
                                    'default': 100000,
                                    'minimum': 1,
                                    'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                                },
                                'verdi.shell.auto_import': {
                                    'type': 'string',
                                    'default': '',
                                    'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                                },
                                'logging.aiida_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                                },
                                'logging.verdi_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to console when running a `verdi` command'
                                },
                                'logging.db_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to the DbLog table'
                                },
                                'logging.plumpy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                                },
                                'logging.kiwipy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                                },
                                'logging.paramiko_loglevel': {
                                    'key': 'logging_paramiko_log_level',
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                                },
                                'logging.alembic_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                                },
                                'logging.sqlalchemy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                                },
                                'logging.circus_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'INFO',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                                },
                                'logging.aiopika_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                                },
                                'warnings.showdeprecations': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print AiiDA deprecation warnings'
                                },
                                'warnings.development_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                    'global_only': True
                                },
                                'warnings.rabbitmq_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                                },
                                'transport.task_retry_initial_interval': {
                                    'type': 'integer',
                                    'default': 20,
                                    'minimum': 1,
                                    'description': 'Initial time interval for the exponential backoff mechanism.'
                                },
                                'transport.task_maximum_attempts': {
                                    'type': 'integer',
                                    'default': 5,
                                    'minimum': 1,
                                    'description': 'Maximum number of transport task attempts before a Process is Paused.'
                                },
                                'rest_api.profile_switching': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                    'global_only': True
                                },
                                'rmq.task_timeout': {
                                    'type': 'integer',
                                    'default': 10,
                                    'minimum': 1,
                                    'description': 'Timeout in seconds for communications with RabbitMQ'
                                },
                                'storage.sandbox': {
                                    'type': 'string',
                                    'description': 'Absolute path to the directory to store sandbox folders.'
                                },
                                'caching.default_enabled': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Enable calculation caching by default'
                                },
                                'caching.enabled_for': {
                                    'description': 'Calculation entry points to enable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'caching.disabled_for': {
                                    'description': 'Calculation entry points to disable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'autofill.user.email': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user email to use when creating new profiles.'
                                },
                                'autofill.user.first_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user first name to use when creating new profiles.'
                                },
                                'autofill.user.last_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user last name to use when creating new profiles.'
                                },
                                'autofill.user.institution': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user institution to use when creating new profiles.'
                                }
                            }
                        }
                    }
                },
                rule='required'
            )
        data_keys = set(data.keys())
        if 'CONFIG_VERSION' in data_keys:
            data_keys.remove('CONFIG_VERSION')
            data__CONFIGVERSION = data['CONFIG_VERSION']
            if not isinstance(data__CONFIGVERSION, (dict)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.CONFIG_VERSION must be object',
                    value=data__CONFIGVERSION,
                    name='' + (name_prefix or 'data') + '.CONFIG_VERSION',
                    definition={
                        'description': 'The configuration version',
                        'type': 'object',
                        'required': ['CURRENT', 'OLDEST_COMPATIBLE'],
                        'properties': {
                            'CURRENT': {
                                'description': 'Version number of configuration file format',
                                'type': 'integer',
                                'const': 9
                            },
                            'OLDEST_COMPATIBLE': {
                                'description': 'Version number of oldest configuration file format this file is compatible with',
                                'type': 'integer',
                                'const': 9
                            }
                        }
                    },
                    rule='type'
                )
            data__CONFIGVERSION_is_dict = isinstance(data__CONFIGVERSION, dict)
            if data__CONFIGVERSION_is_dict:
                data__CONFIGVERSION_len = len(data__CONFIGVERSION)
                if not all(prop in data__CONFIGVERSION for prop in ['CURRENT', 'OLDEST_COMPATIBLE']):
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') +
                        ".CONFIG_VERSION must contain ['CURRENT', 'OLDEST_COMPATIBLE'] properties",
                        value=data__CONFIGVERSION,
                        name='' + (name_prefix or 'data') + '.CONFIG_VERSION',
                        definition={
                            'description': 'The configuration version',
                            'type': 'object',
                            'required': ['CURRENT', 'OLDEST_COMPATIBLE'],
                            'properties': {
                                'CURRENT': {
                                    'description': 'Version number of configuration file format',
                                    'type': 'integer',
                                    'const': 9
                                },
                                'OLDEST_COMPATIBLE': {
                                    'description': 'Version number of oldest configuration file format this file is compatible with',
                                    'type': 'integer',
                                    'const': 9
                                }
                            }
                        },
                        rule='required'
                    )
                data__CONFIGVERSION_keys = set(data__CONFIGVERSION.keys())
                if 'CURRENT' in data__CONFIGVERSION_keys:
                    data__CONFIGVERSION_keys.remove('CURRENT')
                    data__CONFIGVERSION__CURRENT = data__CONFIGVERSION['CURRENT']
                    if not isinstance(data__CONFIGVERSION__CURRENT, (int)) and not (
                        isinstance(data__CONFIGVERSION__CURRENT, float) and data__CONFIGVERSION__CURRENT.is_integer()
                    ) or isinstance(data__CONFIGVERSION__CURRENT, bool):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.CONFIG_VERSION.CURRENT must be integer',
                            value=data__CONFIGVERSION__CURRENT,
                            name='' + (name_prefix or 'data') + '.CONFIG_VERSION.CURRENT',
                            definition={
                                'description': 'Version number of configuration file format',
                                'type': 'integer',
                                'const': 9
                            },
                            rule='type'
                        )
                    if data__CONFIGVERSION__CURRENT != 9:
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') +
                            '.CONFIG_VERSION.CURRENT must be same as const definition: 9',
                            value=data__CONFIGVERSION__CURRENT,
                            name='' + (name_prefix or 'data') + '.CONFIG_VERSION.CURRENT',
                            definition={
                                'description': 'Version number of configuration file format',
                                'type': 'integer',
                                'const': 9
                            },
                            rule='const'
                        )
                if 'OLDEST_COMPATIBLE' in data__CONFIGVERSION_keys:
                    data__CONFIGVERSION_keys.remove('OLDEST_COMPATIBLE')
                    data__CONFIGVERSION__OLDESTCOMPATIBLE = data__CONFIGVERSION['OLDEST_COMPATIBLE']
                    if not isinstance(data__CONFIGVERSION__OLDESTCOMPATIBLE, (int)) and not (
                        isinstance(data__CONFIGVERSION__OLDESTCOMPATIBLE, float) and
                        data__CONFIGVERSION__OLDESTCOMPATIBLE.is_integer()
                    ) or isinstance(data__CONFIGVERSION__OLDESTCOMPATIBLE, bool):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.CONFIG_VERSION.OLDEST_COMPATIBLE must be integer',
                            value=data__CONFIGVERSION__OLDESTCOMPATIBLE,
                            name='' + (name_prefix or 'data') + '.CONFIG_VERSION.OLDEST_COMPATIBLE',
                            definition={
                                'description': 'Version number of oldest configuration file format this file is compatible with',
                                'type': 'integer',
                                'const': 9
                            },
                            rule='type'
                        )
                    if data__CONFIGVERSION__OLDESTCOMPATIBLE != 9:
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') +
                            '.CONFIG_VERSION.OLDEST_COMPATIBLE must be same as const definition: 9',
                            value=data__CONFIGVERSION__OLDESTCOMPATIBLE,
                            name='' + (name_prefix or 'data') + '.CONFIG_VERSION.OLDEST_COMPATIBLE',
                            definition={
                                'description': 'Version number of oldest configuration file format this file is compatible with',
                                'type': 'integer',
                                'const': 9
                            },
                            rule='const'
                        )
        if 'profiles' in data_keys:
            data_keys.remove('profiles')
            data__profiles = data['profiles']
            if not isinstance(data__profiles, (dict)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.profiles must be object',
                    value=data__profiles,
                    name='' + (name_prefix or 'data') + '.profiles',
                    definition={
                        'description': 'Configured profiles',
                        'type': 'object',
                        'patternProperties': {
                            '.+': {
                                'type': 'object',
                                'required': ['storage', 'process_control'],
                                'properties': {
                                    'PROFILE_UUID': {
                                        'description': "The profile's unique key",
                                        'type': 'string'
                                    },
                                    'storage': {
                                        'description': 'The storage configuration',
                                        'type': 'object',
                                        'required': ['backend', 'config'],
                                        'properties': {
                                            'backend': {
                                                'description': 'The storage backend type to use',
                                                'type': 'string',
                                                'default': 'psql_dos'
                                            },
                                            'config': {
                                                'description': 'The configuration to pass to the storage backend',
                                                'type': 'object',
                                                'properties': {
                                                    'database_engine': {
                                                        'type': 'string',
                                                        'default': 'postgresql_psycopg2'
                                                    },
                                                    'database_port': {
                                                        'type': ['integer', 'string'],
                                                        'minimum': 1,
                                                        'pattern': '\\d+',
                                                        'default': 5432
                                                    },
                                                    'database_hostname': {
                                                        'type': ['string', 'null'],
                                                        'default': None
                                                    },
                                                    'database_username': {
                                                        'type': 'string'
                                                    },
                                                    'database_password': {
                                                        'type': ['string', 'null'],
                                                        'default': None
                                                    },
                                                    'database_name': {
                                                        'type': 'string'
                                                    },
                                                    'repository_uri': {
                                                        'description': 'URI to the AiiDA object store',
                                                        'type': 'string'
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'process_control': {
                                        'description': 'The process control configuration',
                                        'type': 'object',
                                        'required': ['backend', 'config'],
                                        'properties': {
                                            'backend': {
                                                'description': 'The process execution backend type to use',
                                                'type': 'string',
                                                'default': 'rabbitmq'
                                            },
                                            'config': {
                                                'description': 'The configuration to pass to the process execution backend',
                                                'type': 'object',
                                                'parameters': {
                                                    'broker_protocol': {
                                                        'description': 'Protocol for connecting to the RabbitMQ server',
                                                        'type': 'string',
                                                        'enum': ['amqp', 'amqps'],
                                                        'default': 'amqp'
                                                    },
                                                    'broker_username': {
                                                        'description': 'Username for RabbitMQ authentication',
                                                        'type': 'string',
                                                        'default': 'guest'
                                                    },
                                                    'broker_password': {
                                                        'description': 'Password for RabbitMQ authentication',
                                                        'type': 'string',
                                                        'default': 'guest'
                                                    },
                                                    'broker_host': {
                                                        'description': 'Hostname of the RabbitMQ server',
                                                        'type': 'string',
                                                        'default': '127.0.0.1'
                                                    },
                                                    'broker_port': {
                                                        'description': 'Port of the RabbitMQ server',
                                                        'type': 'integer',
                                                        'minimum': 1,
                                                        'default': 5672
                                                    },
                                                    'broker_virtual_host': {
                                                        'description': 'RabbitMQ virtual host to connect to',
                                                        'type': 'string',
                                                        'default': ''
                                                    },
                                                    'broker_parameters': {
                                                        'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                                        'type': 'object',
                                                        'default': {
                                                            'heartbeat': 600
                                                        },
                                                        'properties': {
                                                            'heartbeat': {
                                                                'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                                'type': 'integer',
                                                                'default': 600,
                                                                'minimum': 0
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'default_user_email': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'test_profile': {
                                        'type': 'boolean',
                                        'default': False
                                    },
                                    'options': {
                                        'description': 'Profile specific options',
                                        '$ref': '#/definitions/options'
                                    }
                                }
                            }
                        }
                    },
                    rule='type'
                )
            data__profiles_is_dict = isinstance(data__profiles, dict)
            if data__profiles_is_dict:
                data__profiles_keys = set(data__profiles.keys())
                for data__profiles_key, data__profiles_val in data__profiles.items():
                    if REGEX_PATTERNS['.+'].search(data__profiles_key):
                        if data__profiles_key in data__profiles_keys:
                            data__profiles_keys.remove(data__profiles_key)
                        validate___definitions_profile(
                            data__profiles_val, custom_formats,
                            (name_prefix or 'data') + '.profiles.{data__profiles_key}'.format(**locals())
                        )
        if 'default_profile' in data_keys:
            data_keys.remove('default_profile')
            data__defaultprofile = data['default_profile']
            if not isinstance(data__defaultprofile, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.default_profile must be string',
                    value=data__defaultprofile,
                    name='' + (name_prefix or 'data') + '.default_profile',
                    definition={
                        'description': 'Default profile to use',
                        'type': 'string'
                    },
                    rule='type'
                )
        if 'options' in data_keys:
            data_keys.remove('options')
            data__options = data['options']
            validate___definitions_options(data__options, custom_formats, (name_prefix or 'data') + '.options')
    return data


def validate___definitions_options(data, custom_formats={}, name_prefix=None):
    if not isinstance(data, (dict)):
        raise JsonSchemaValueException(
            '' + (name_prefix or 'data') + ' must be object',
            value=data,
            name='' + (name_prefix or 'data') + '',
            definition={
                'type': 'object',
                'properties': {
                    'runner.poll.interval': {
                        'type': 'integer',
                        'default': 60,
                        'minimum': 0,
                        'description': 'Polling interval in seconds to be used by process runners'
                    },
                    'daemon.default_workers': {
                        'type': 'integer',
                        'default': 1,
                        'minimum': 1,
                        'description': 'Default number of workers to be launched by `verdi daemon start`'
                    },
                    'daemon.timeout': {
                        'type': 'integer',
                        'default': 2,
                        'minimum': 0,
                        'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                    },
                    'daemon.worker_process_slots': {
                        'type': 'integer',
                        'default': 200,
                        'minimum': 1,
                        'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                    },
                    'daemon.recursion_limit': {
                        'type': 'integer',
                        'default': 3000,
                        'maximum': 100000,
                        'minimum': 1,
                        'description': 'Maximum recursion depth for the daemon workers'
                    },
                    'db.batch_size': {
                        'type': 'integer',
                        'default': 100000,
                        'minimum': 1,
                        'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                    },
                    'verdi.shell.auto_import': {
                        'type': 'string',
                        'default': '',
                        'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                    },
                    'logging.aiida_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                    },
                    'logging.verdi_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to console when running a `verdi` command'
                    },
                    'logging.db_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to the DbLog table'
                    },
                    'logging.plumpy_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                    },
                    'logging.kiwipy_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                    },
                    'logging.paramiko_loglevel': {
                        'key': 'logging_paramiko_log_level',
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                    },
                    'logging.alembic_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                    },
                    'logging.sqlalchemy_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                    },
                    'logging.circus_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'INFO',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                    },
                    'logging.aiopika_loglevel': {
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                    },
                    'warnings.showdeprecations': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print AiiDA deprecation warnings'
                    },
                    'warnings.development_version': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                        'global_only': True
                    },
                    'warnings.rabbitmq_version': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                    },
                    'transport.task_retry_initial_interval': {
                        'type': 'integer',
                        'default': 20,
                        'minimum': 1,
                        'description': 'Initial time interval for the exponential backoff mechanism.'
                    },
                    'transport.task_maximum_attempts': {
                        'type': 'integer',
                        'default': 5,
                        'minimum': 1,
                        'description': 'Maximum number of transport task attempts before a Process is Paused.'
                    },
                    'rest_api.profile_switching': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                        'global_only': True
                    },
                    'rmq.task_timeout': {
                        'type': 'integer',
                        'default': 10,
                        'minimum': 1,
                        'description': 'Timeout in seconds for communications with RabbitMQ'
                    },
                    'storage.sandbox': {
                        'type': 'string',
                        'description': 'Absolute path to the directory to store sandbox folders.'
                    },
                    'caching.default_enabled': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Enable calculation caching by default'
                    },
                    'caching.enabled_for': {
                        'description': 'Calculation entry points to enable caching on',
                        'type': 'array',
                        'default': [],
                        'items': {
                            'type': 'string'
                        }
                    },
                    'caching.disabled_for': {
                        'description': 'Calculation entry points to disable caching on',
                        'type': 'array',
                        'default': [],
                        'items': {
                            'type': 'string'
                        }
                    },
                    'autofill.user.email': {
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user email to use when creating new profiles.'
                    },
                    'autofill.user.first_name': {
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user first name to use when creating new profiles.'
                    },
                    'autofill.user.last_name': {
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user last name to use when creating new profiles.'
                    },
                    'autofill.user.institution': {
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user institution to use when creating new profiles.'
                    }
                }
            },
            rule='type'
        )
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_keys = set(data.keys())
        if 'runner.poll.interval' in data_keys:
            data_keys.remove('runner.poll.interval')
            data__runnerpollinterval = data['runner.poll.interval']
            if not isinstance(data__runnerpollinterval, (int)) and not (
                isinstance(data__runnerpollinterval, float) and data__runnerpollinterval.is_integer()
            ) or isinstance(data__runnerpollinterval, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.runner.poll.interval must be integer',
                    value=data__runnerpollinterval,
                    name='' + (name_prefix or 'data') + '.runner.poll.interval',
                    definition={
                        'type': 'integer',
                        'default': 60,
                        'minimum': 0,
                        'description': 'Polling interval in seconds to be used by process runners'
                    },
                    rule='type'
                )
            if isinstance(data__runnerpollinterval, (int, float, Decimal)):
                if data__runnerpollinterval < 0:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.runner.poll.interval must be bigger than or equal to 0',
                        value=data__runnerpollinterval,
                        name='' + (name_prefix or 'data') + '.runner.poll.interval',
                        definition={
                            'type': 'integer',
                            'default': 60,
                            'minimum': 0,
                            'description': 'Polling interval in seconds to be used by process runners'
                        },
                        rule='minimum'
                    )
        else:
            data['runner.poll.interval'] = 60
        if 'daemon.default_workers' in data_keys:
            data_keys.remove('daemon.default_workers')
            data__daemondefaultworkers = data['daemon.default_workers']
            if not isinstance(data__daemondefaultworkers, (int)) and not (
                isinstance(data__daemondefaultworkers, float) and data__daemondefaultworkers.is_integer()
            ) or isinstance(data__daemondefaultworkers, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.daemon.default_workers must be integer',
                    value=data__daemondefaultworkers,
                    name='' + (name_prefix or 'data') + '.daemon.default_workers',
                    definition={
                        'type': 'integer',
                        'default': 1,
                        'minimum': 1,
                        'description': 'Default number of workers to be launched by `verdi daemon start`'
                    },
                    rule='type'
                )
            if isinstance(data__daemondefaultworkers, (int, float, Decimal)):
                if data__daemondefaultworkers < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.daemon.default_workers must be bigger than or equal to 1',
                        value=data__daemondefaultworkers,
                        name='' + (name_prefix or 'data') + '.daemon.default_workers',
                        definition={
                            'type': 'integer',
                            'default': 1,
                            'minimum': 1,
                            'description': 'Default number of workers to be launched by `verdi daemon start`'
                        },
                        rule='minimum'
                    )
        else:
            data['daemon.default_workers'] = 1
        if 'daemon.timeout' in data_keys:
            data_keys.remove('daemon.timeout')
            data__daemontimeout = data['daemon.timeout']
            if not isinstance(data__daemontimeout,
                              (int
                               )) and not (isinstance(data__daemontimeout, float) and
                                           data__daemontimeout.is_integer()) or isinstance(data__daemontimeout, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.daemon.timeout must be integer',
                    value=data__daemontimeout,
                    name='' + (name_prefix or 'data') + '.daemon.timeout',
                    definition={
                        'type': 'integer',
                        'default': 2,
                        'minimum': 0,
                        'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                    },
                    rule='type'
                )
            if isinstance(data__daemontimeout, (int, float, Decimal)):
                if data__daemontimeout < 0:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.daemon.timeout must be bigger than or equal to 0',
                        value=data__daemontimeout,
                        name='' + (name_prefix or 'data') + '.daemon.timeout',
                        definition={
                            'type': 'integer',
                            'default': 2,
                            'minimum': 0,
                            'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                        },
                        rule='minimum'
                    )
        else:
            data['daemon.timeout'] = 2
        if 'daemon.worker_process_slots' in data_keys:
            data_keys.remove('daemon.worker_process_slots')
            data__daemonworkerprocessslots = data['daemon.worker_process_slots']
            if not isinstance(data__daemonworkerprocessslots, (int)) and not (
                isinstance(data__daemonworkerprocessslots, float) and data__daemonworkerprocessslots.is_integer()
            ) or isinstance(data__daemonworkerprocessslots, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.daemon.worker_process_slots must be integer',
                    value=data__daemonworkerprocessslots,
                    name='' + (name_prefix or 'data') + '.daemon.worker_process_slots',
                    definition={
                        'type': 'integer',
                        'default': 200,
                        'minimum': 1,
                        'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                    },
                    rule='type'
                )
            if isinstance(data__daemonworkerprocessslots, (int, float, Decimal)):
                if data__daemonworkerprocessslots < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.daemon.worker_process_slots must be bigger than or equal to 1',
                        value=data__daemonworkerprocessslots,
                        name='' + (name_prefix or 'data') + '.daemon.worker_process_slots',
                        definition={
                            'type': 'integer',
                            'default': 200,
                            'minimum': 1,
                            'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                        },
                        rule='minimum'
                    )
        else:
            data['daemon.worker_process_slots'] = 200
        if 'daemon.recursion_limit' in data_keys:
            data_keys.remove('daemon.recursion_limit')
            data__daemonrecursionlimit = data['daemon.recursion_limit']
            if not isinstance(data__daemonrecursionlimit, (int)) and not (
                isinstance(data__daemonrecursionlimit, float) and data__daemonrecursionlimit.is_integer()
            ) or isinstance(data__daemonrecursionlimit, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.daemon.recursion_limit must be integer',
                    value=data__daemonrecursionlimit,
                    name='' + (name_prefix or 'data') + '.daemon.recursion_limit',
                    definition={
                        'type': 'integer',
                        'default': 3000,
                        'maximum': 100000,
                        'minimum': 1,
                        'description': 'Maximum recursion depth for the daemon workers'
                    },
                    rule='type'
                )
            if isinstance(data__daemonrecursionlimit, (int, float, Decimal)):
                if data__daemonrecursionlimit < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.daemon.recursion_limit must be bigger than or equal to 1',
                        value=data__daemonrecursionlimit,
                        name='' + (name_prefix or 'data') + '.daemon.recursion_limit',
                        definition={
                            'type': 'integer',
                            'default': 3000,
                            'maximum': 100000,
                            'minimum': 1,
                            'description': 'Maximum recursion depth for the daemon workers'
                        },
                        rule='minimum'
                    )
                if data__daemonrecursionlimit > 100000:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') +
                        '.daemon.recursion_limit must be smaller than or equal to 100000',
                        value=data__daemonrecursionlimit,
                        name='' + (name_prefix or 'data') + '.daemon.recursion_limit',
                        definition={
                            'type': 'integer',
                            'default': 3000,
                            'maximum': 100000,
                            'minimum': 1,
                            'description': 'Maximum recursion depth for the daemon workers'
                        },
                        rule='maximum'
                    )
        else:
            data['daemon.recursion_limit'] = 3000
        if 'db.batch_size' in data_keys:
            data_keys.remove('db.batch_size')
            data__dbbatchsize = data['db.batch_size']
            if not isinstance(data__dbbatchsize,
                              (int)) and not (isinstance(data__dbbatchsize, float) and
                                              data__dbbatchsize.is_integer()) or isinstance(data__dbbatchsize, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.db.batch_size must be integer',
                    value=data__dbbatchsize,
                    name='' + (name_prefix or 'data') + '.db.batch_size',
                    definition={
                        'type': 'integer',
                        'default': 100000,
                        'minimum': 1,
                        'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                    },
                    rule='type'
                )
            if isinstance(data__dbbatchsize, (int, float, Decimal)):
                if data__dbbatchsize < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.db.batch_size must be bigger than or equal to 1',
                        value=data__dbbatchsize,
                        name='' + (name_prefix or 'data') + '.db.batch_size',
                        definition={
                            'type': 'integer',
                            'default': 100000,
                            'minimum': 1,
                            'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                        },
                        rule='minimum'
                    )
        else:
            data['db.batch_size'] = 100000
        if 'verdi.shell.auto_import' in data_keys:
            data_keys.remove('verdi.shell.auto_import')
            data__verdishellautoimport = data['verdi.shell.auto_import']
            if not isinstance(data__verdishellautoimport, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.verdi.shell.auto_import must be string',
                    value=data__verdishellautoimport,
                    name='' + (name_prefix or 'data') + '.verdi.shell.auto_import',
                    definition={
                        'type': 'string',
                        'default': '',
                        'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                    },
                    rule='type'
                )
        else:
            data['verdi.shell.auto_import'] = ''
        if 'logging.aiida_loglevel' in data_keys:
            data_keys.remove('logging.aiida_loglevel')
            data__loggingaiidaloglevel = data['logging.aiida_loglevel']
            if not isinstance(data__loggingaiidaloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.aiida_loglevel must be string',
                    value=data__loggingaiidaloglevel,
                    name='' + (name_prefix or 'data') + '.logging.aiida_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                    },
                    rule='type'
                )
            if data__loggingaiidaloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.aiida_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingaiidaloglevel,
                    name='' + (name_prefix or 'data') + '.logging.aiida_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.aiida_loglevel'] = 'REPORT'
        if 'logging.verdi_loglevel' in data_keys:
            data_keys.remove('logging.verdi_loglevel')
            data__loggingverdiloglevel = data['logging.verdi_loglevel']
            if not isinstance(data__loggingverdiloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.verdi_loglevel must be string',
                    value=data__loggingverdiloglevel,
                    name='' + (name_prefix or 'data') + '.logging.verdi_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to console when running a `verdi` command'
                    },
                    rule='type'
                )
            if data__loggingverdiloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.verdi_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingverdiloglevel,
                    name='' + (name_prefix or 'data') + '.logging.verdi_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to console when running a `verdi` command'
                    },
                    rule='enum'
                )
        else:
            data['logging.verdi_loglevel'] = 'REPORT'
        if 'logging.db_loglevel' in data_keys:
            data_keys.remove('logging.db_loglevel')
            data__loggingdbloglevel = data['logging.db_loglevel']
            if not isinstance(data__loggingdbloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.db_loglevel must be string',
                    value=data__loggingdbloglevel,
                    name='' + (name_prefix or 'data') + '.logging.db_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to the DbLog table'
                    },
                    rule='type'
                )
            if data__loggingdbloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.db_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingdbloglevel,
                    name='' + (name_prefix or 'data') + '.logging.db_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'REPORT',
                        'description': 'Minimum level to log to the DbLog table'
                    },
                    rule='enum'
                )
        else:
            data['logging.db_loglevel'] = 'REPORT'
        if 'logging.plumpy_loglevel' in data_keys:
            data_keys.remove('logging.plumpy_loglevel')
            data__loggingplumpyloglevel = data['logging.plumpy_loglevel']
            if not isinstance(data__loggingplumpyloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.plumpy_loglevel must be string',
                    value=data__loggingplumpyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.plumpy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                    },
                    rule='type'
                )
            if data__loggingplumpyloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.plumpy_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingplumpyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.plumpy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.plumpy_loglevel'] = 'WARNING'
        if 'logging.kiwipy_loglevel' in data_keys:
            data_keys.remove('logging.kiwipy_loglevel')
            data__loggingkiwipyloglevel = data['logging.kiwipy_loglevel']
            if not isinstance(data__loggingkiwipyloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.kiwipy_loglevel must be string',
                    value=data__loggingkiwipyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.kiwipy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                    },
                    rule='type'
                )
            if data__loggingkiwipyloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.kiwipy_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingkiwipyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.kiwipy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.kiwipy_loglevel'] = 'WARNING'
        if 'logging.paramiko_loglevel' in data_keys:
            data_keys.remove('logging.paramiko_loglevel')
            data__loggingparamikologlevel = data['logging.paramiko_loglevel']
            if not isinstance(data__loggingparamikologlevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.paramiko_loglevel must be string',
                    value=data__loggingparamikologlevel,
                    name='' + (name_prefix or 'data') + '.logging.paramiko_loglevel',
                    definition={
                        'key': 'logging_paramiko_log_level',
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                    },
                    rule='type'
                )
            if data__loggingparamikologlevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.paramiko_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingparamikologlevel,
                    name='' + (name_prefix or 'data') + '.logging.paramiko_loglevel',
                    definition={
                        'key': 'logging_paramiko_log_level',
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.paramiko_loglevel'] = 'WARNING'
        if 'logging.alembic_loglevel' in data_keys:
            data_keys.remove('logging.alembic_loglevel')
            data__loggingalembicloglevel = data['logging.alembic_loglevel']
            if not isinstance(data__loggingalembicloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.alembic_loglevel must be string',
                    value=data__loggingalembicloglevel,
                    name='' + (name_prefix or 'data') + '.logging.alembic_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                    },
                    rule='type'
                )
            if data__loggingalembicloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.alembic_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingalembicloglevel,
                    name='' + (name_prefix or 'data') + '.logging.alembic_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.alembic_loglevel'] = 'WARNING'
        if 'logging.sqlalchemy_loglevel' in data_keys:
            data_keys.remove('logging.sqlalchemy_loglevel')
            data__loggingsqlalchemyloglevel = data['logging.sqlalchemy_loglevel']
            if not isinstance(data__loggingsqlalchemyloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.sqlalchemy_loglevel must be string',
                    value=data__loggingsqlalchemyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.sqlalchemy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                    },
                    rule='type'
                )
            if data__loggingsqlalchemyloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.sqlalchemy_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingsqlalchemyloglevel,
                    name='' + (name_prefix or 'data') + '.logging.sqlalchemy_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.sqlalchemy_loglevel'] = 'WARNING'
        if 'logging.circus_loglevel' in data_keys:
            data_keys.remove('logging.circus_loglevel')
            data__loggingcircusloglevel = data['logging.circus_loglevel']
            if not isinstance(data__loggingcircusloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.circus_loglevel must be string',
                    value=data__loggingcircusloglevel,
                    name='' + (name_prefix or 'data') + '.logging.circus_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'INFO',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                    },
                    rule='type'
                )
            if data__loggingcircusloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.circus_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingcircusloglevel,
                    name='' + (name_prefix or 'data') + '.logging.circus_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'INFO',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.circus_loglevel'] = 'INFO'
        if 'logging.aiopika_loglevel' in data_keys:
            data_keys.remove('logging.aiopika_loglevel')
            data__loggingaiopikaloglevel = data['logging.aiopika_loglevel']
            if not isinstance(data__loggingaiopikaloglevel, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.logging.aiopika_loglevel must be string',
                    value=data__loggingaiopikaloglevel,
                    name='' + (name_prefix or 'data') + '.logging.aiopika_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                    },
                    rule='type'
                )
            if data__loggingaiopikaloglevel not in ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']:
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') +
                    ".logging.aiopika_loglevel must be one of ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG']",
                    value=data__loggingaiopikaloglevel,
                    name='' + (name_prefix or 'data') + '.logging.aiopika_loglevel',
                    definition={
                        'type': 'string',
                        'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                        'default': 'WARNING',
                        'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                    },
                    rule='enum'
                )
        else:
            data['logging.aiopika_loglevel'] = 'WARNING'
        if 'warnings.showdeprecations' in data_keys:
            data_keys.remove('warnings.showdeprecations')
            data__warningsshowdeprecations = data['warnings.showdeprecations']
            if not isinstance(data__warningsshowdeprecations, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.warnings.showdeprecations must be boolean',
                    value=data__warningsshowdeprecations,
                    name='' + (name_prefix or 'data') + '.warnings.showdeprecations',
                    definition={
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print AiiDA deprecation warnings'
                    },
                    rule='type'
                )
        else:
            data['warnings.showdeprecations'] = True
        if 'warnings.development_version' in data_keys:
            data_keys.remove('warnings.development_version')
            data__warningsdevelopmentversion = data['warnings.development_version']
            if not isinstance(data__warningsdevelopmentversion, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.warnings.development_version must be boolean',
                    value=data__warningsdevelopmentversion,
                    name='' + (name_prefix or 'data') + '.warnings.development_version',
                    definition={
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                        'global_only': True
                    },
                    rule='type'
                )
        else:
            data['warnings.development_version'] = True
        if 'warnings.rabbitmq_version' in data_keys:
            data_keys.remove('warnings.rabbitmq_version')
            data__warningsrabbitmqversion = data['warnings.rabbitmq_version']
            if not isinstance(data__warningsrabbitmqversion, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.warnings.rabbitmq_version must be boolean',
                    value=data__warningsrabbitmqversion,
                    name='' + (name_prefix or 'data') + '.warnings.rabbitmq_version',
                    definition={
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                    },
                    rule='type'
                )
        else:
            data['warnings.rabbitmq_version'] = True
        if 'transport.task_retry_initial_interval' in data_keys:
            data_keys.remove('transport.task_retry_initial_interval')
            data__transporttaskretryinitialinterval = data['transport.task_retry_initial_interval']
            if not isinstance(data__transporttaskretryinitialinterval, (int)) and not (
                isinstance(data__transporttaskretryinitialinterval, float) and
                data__transporttaskretryinitialinterval.is_integer()
            ) or isinstance(data__transporttaskretryinitialinterval, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.transport.task_retry_initial_interval must be integer',
                    value=data__transporttaskretryinitialinterval,
                    name='' + (name_prefix or 'data') + '.transport.task_retry_initial_interval',
                    definition={
                        'type': 'integer',
                        'default': 20,
                        'minimum': 1,
                        'description': 'Initial time interval for the exponential backoff mechanism.'
                    },
                    rule='type'
                )
            if isinstance(data__transporttaskretryinitialinterval, (int, float, Decimal)):
                if data__transporttaskretryinitialinterval < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') +
                        '.transport.task_retry_initial_interval must be bigger than or equal to 1',
                        value=data__transporttaskretryinitialinterval,
                        name='' + (name_prefix or 'data') + '.transport.task_retry_initial_interval',
                        definition={
                            'type': 'integer',
                            'default': 20,
                            'minimum': 1,
                            'description': 'Initial time interval for the exponential backoff mechanism.'
                        },
                        rule='minimum'
                    )
        else:
            data['transport.task_retry_initial_interval'] = 20
        if 'transport.task_maximum_attempts' in data_keys:
            data_keys.remove('transport.task_maximum_attempts')
            data__transporttaskmaximumattempts = data['transport.task_maximum_attempts']
            if not isinstance(data__transporttaskmaximumattempts, (int)) and not (
                isinstance(data__transporttaskmaximumattempts, float) and
                data__transporttaskmaximumattempts.is_integer()
            ) or isinstance(data__transporttaskmaximumattempts, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.transport.task_maximum_attempts must be integer',
                    value=data__transporttaskmaximumattempts,
                    name='' + (name_prefix or 'data') + '.transport.task_maximum_attempts',
                    definition={
                        'type': 'integer',
                        'default': 5,
                        'minimum': 1,
                        'description': 'Maximum number of transport task attempts before a Process is Paused.'
                    },
                    rule='type'
                )
            if isinstance(data__transporttaskmaximumattempts, (int, float, Decimal)):
                if data__transporttaskmaximumattempts < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') +
                        '.transport.task_maximum_attempts must be bigger than or equal to 1',
                        value=data__transporttaskmaximumattempts,
                        name='' + (name_prefix or 'data') + '.transport.task_maximum_attempts',
                        definition={
                            'type': 'integer',
                            'default': 5,
                            'minimum': 1,
                            'description': 'Maximum number of transport task attempts before a Process is Paused.'
                        },
                        rule='minimum'
                    )
        else:
            data['transport.task_maximum_attempts'] = 5
        if 'rest_api.profile_switching' in data_keys:
            data_keys.remove('rest_api.profile_switching')
            data__restapiprofileswitching = data['rest_api.profile_switching']
            if not isinstance(data__restapiprofileswitching, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.rest_api.profile_switching must be boolean',
                    value=data__restapiprofileswitching,
                    name='' + (name_prefix or 'data') + '.rest_api.profile_switching',
                    definition={
                        'type': 'boolean',
                        'default': False,
                        'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                        'global_only': True
                    },
                    rule='type'
                )
        else:
            data['rest_api.profile_switching'] = False
        if 'rmq.task_timeout' in data_keys:
            data_keys.remove('rmq.task_timeout')
            data__rmqtasktimeout = data['rmq.task_timeout']
            if not isinstance(data__rmqtasktimeout, (int)
                              ) and not (isinstance(data__rmqtasktimeout, float) and
                                         data__rmqtasktimeout.is_integer()) or isinstance(data__rmqtasktimeout, bool):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.rmq.task_timeout must be integer',
                    value=data__rmqtasktimeout,
                    name='' + (name_prefix or 'data') + '.rmq.task_timeout',
                    definition={
                        'type': 'integer',
                        'default': 10,
                        'minimum': 1,
                        'description': 'Timeout in seconds for communications with RabbitMQ'
                    },
                    rule='type'
                )
            if isinstance(data__rmqtasktimeout, (int, float, Decimal)):
                if data__rmqtasktimeout < 1:
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + '.rmq.task_timeout must be bigger than or equal to 1',
                        value=data__rmqtasktimeout,
                        name='' + (name_prefix or 'data') + '.rmq.task_timeout',
                        definition={
                            'type': 'integer',
                            'default': 10,
                            'minimum': 1,
                            'description': 'Timeout in seconds for communications with RabbitMQ'
                        },
                        rule='minimum'
                    )
        else:
            data['rmq.task_timeout'] = 10
        if 'storage.sandbox' in data_keys:
            data_keys.remove('storage.sandbox')
            data__storagesandbox = data['storage.sandbox']
            if not isinstance(data__storagesandbox, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.storage.sandbox must be string',
                    value=data__storagesandbox,
                    name='' + (name_prefix or 'data') + '.storage.sandbox',
                    definition={
                        'type': 'string',
                        'description': 'Absolute path to the directory to store sandbox folders.'
                    },
                    rule='type'
                )
        if 'caching.default_enabled' in data_keys:
            data_keys.remove('caching.default_enabled')
            data__cachingdefaultenabled = data['caching.default_enabled']
            if not isinstance(data__cachingdefaultenabled, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.caching.default_enabled must be boolean',
                    value=data__cachingdefaultenabled,
                    name='' + (name_prefix or 'data') + '.caching.default_enabled',
                    definition={
                        'type': 'boolean',
                        'default': False,
                        'description': 'Enable calculation caching by default'
                    },
                    rule='type'
                )
        else:
            data['caching.default_enabled'] = False
        if 'caching.enabled_for' in data_keys:
            data_keys.remove('caching.enabled_for')
            data__cachingenabledfor = data['caching.enabled_for']
            if not isinstance(data__cachingenabledfor, (list, tuple)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.caching.enabled_for must be array',
                    value=data__cachingenabledfor,
                    name='' + (name_prefix or 'data') + '.caching.enabled_for',
                    definition={
                        'description': 'Calculation entry points to enable caching on',
                        'type': 'array',
                        'default': [],
                        'items': {
                            'type': 'string'
                        }
                    },
                    rule='type'
                )
            data__cachingenabledfor_is_list = isinstance(data__cachingenabledfor, (list, tuple))
            if data__cachingenabledfor_is_list:
                data__cachingenabledfor_len = len(data__cachingenabledfor)
                for data__cachingenabledfor_x, data__cachingenabledfor_item in enumerate(data__cachingenabledfor):
                    if not isinstance(data__cachingenabledfor_item, (str)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') +
                            '.caching.enabled_for[{data__cachingenabledfor_x}]'.format(**locals()) + ' must be string',
                            value=data__cachingenabledfor_item,
                            name='' + (name_prefix or 'data') +
                            '.caching.enabled_for[{data__cachingenabledfor_x}]'.format(**locals()) + '',
                            definition={'type': 'string'},
                            rule='type'
                        )
        else:
            data['caching.enabled_for'] = []
        if 'caching.disabled_for' in data_keys:
            data_keys.remove('caching.disabled_for')
            data__cachingdisabledfor = data['caching.disabled_for']
            if not isinstance(data__cachingdisabledfor, (list, tuple)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.caching.disabled_for must be array',
                    value=data__cachingdisabledfor,
                    name='' + (name_prefix or 'data') + '.caching.disabled_for',
                    definition={
                        'description': 'Calculation entry points to disable caching on',
                        'type': 'array',
                        'default': [],
                        'items': {
                            'type': 'string'
                        }
                    },
                    rule='type'
                )
            data__cachingdisabledfor_is_list = isinstance(data__cachingdisabledfor, (list, tuple))
            if data__cachingdisabledfor_is_list:
                data__cachingdisabledfor_len = len(data__cachingdisabledfor)
                for data__cachingdisabledfor_x, data__cachingdisabledfor_item in enumerate(data__cachingdisabledfor):
                    if not isinstance(data__cachingdisabledfor_item, (str)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') +
                            '.caching.disabled_for[{data__cachingdisabledfor_x}]'.format(**locals()) +
                            ' must be string',
                            value=data__cachingdisabledfor_item,
                            name='' + (name_prefix or 'data') +
                            '.caching.disabled_for[{data__cachingdisabledfor_x}]'.format(**locals()) + '',
                            definition={'type': 'string'},
                            rule='type'
                        )
        else:
            data['caching.disabled_for'] = []
        if 'autofill.user.email' in data_keys:
            data_keys.remove('autofill.user.email')
            data__autofilluseremail = data['autofill.user.email']
            if not isinstance(data__autofilluseremail, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.autofill.user.email must be string',
                    value=data__autofilluseremail,
                    name='' + (name_prefix or 'data') + '.autofill.user.email',
                    definition={
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user email to use when creating new profiles.'
                    },
                    rule='type'
                )
        if 'autofill.user.first_name' in data_keys:
            data_keys.remove('autofill.user.first_name')
            data__autofilluserfirstname = data['autofill.user.first_name']
            if not isinstance(data__autofilluserfirstname, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.autofill.user.first_name must be string',
                    value=data__autofilluserfirstname,
                    name='' + (name_prefix or 'data') + '.autofill.user.first_name',
                    definition={
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user first name to use when creating new profiles.'
                    },
                    rule='type'
                )
        if 'autofill.user.last_name' in data_keys:
            data_keys.remove('autofill.user.last_name')
            data__autofilluserlastname = data['autofill.user.last_name']
            if not isinstance(data__autofilluserlastname, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.autofill.user.last_name must be string',
                    value=data__autofilluserlastname,
                    name='' + (name_prefix or 'data') + '.autofill.user.last_name',
                    definition={
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user last name to use when creating new profiles.'
                    },
                    rule='type'
                )
        if 'autofill.user.institution' in data_keys:
            data_keys.remove('autofill.user.institution')
            data__autofilluserinstitution = data['autofill.user.institution']
            if not isinstance(data__autofilluserinstitution, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.autofill.user.institution must be string',
                    value=data__autofilluserinstitution,
                    name='' + (name_prefix or 'data') + '.autofill.user.institution',
                    definition={
                        'type': 'string',
                        'global_only': True,
                        'description': 'Default user institution to use when creating new profiles.'
                    },
                    rule='type'
                )
    return data


def validate___definitions_profile(data, custom_formats={}, name_prefix=None):
    if not isinstance(data, (dict)):
        raise JsonSchemaValueException(
            '' + (name_prefix or 'data') + ' must be object',
            value=data,
            name='' + (name_prefix or 'data') + '',
            definition={
                'type': 'object',
                'required': ['storage', 'process_control'],
                'properties': {
                    'PROFILE_UUID': {
                        'description': "The profile's unique key",
                        'type': 'string'
                    },
                    'storage': {
                        'description': 'The storage configuration',
                        'type': 'object',
                        'required': ['backend', 'config'],
                        'properties': {
                            'backend': {
                                'description': 'The storage backend type to use',
                                'type': 'string',
                                'default': 'psql_dos'
                            },
                            'config': {
                                'description': 'The configuration to pass to the storage backend',
                                'type': 'object',
                                'properties': {
                                    'database_engine': {
                                        'type': 'string',
                                        'default': 'postgresql_psycopg2'
                                    },
                                    'database_port': {
                                        'type': ['integer', 'string'],
                                        'minimum': 1,
                                        'pattern': '\\d+',
                                        'default': 5432
                                    },
                                    'database_hostname': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_username': {
                                        'type': 'string'
                                    },
                                    'database_password': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_name': {
                                        'type': 'string'
                                    },
                                    'repository_uri': {
                                        'description': 'URI to the AiiDA object store',
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    },
                    'process_control': {
                        'description': 'The process control configuration',
                        'type': 'object',
                        'required': ['backend', 'config'],
                        'properties': {
                            'backend': {
                                'description': 'The process execution backend type to use',
                                'type': 'string',
                                'default': 'rabbitmq'
                            },
                            'config': {
                                'description': 'The configuration to pass to the process execution backend',
                                'type': 'object',
                                'parameters': {
                                    'broker_protocol': {
                                        'description': 'Protocol for connecting to the RabbitMQ server',
                                        'type': 'string',
                                        'enum': ['amqp', 'amqps'],
                                        'default': 'amqp'
                                    },
                                    'broker_username': {
                                        'description': 'Username for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_password': {
                                        'description': 'Password for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_host': {
                                        'description': 'Hostname of the RabbitMQ server',
                                        'type': 'string',
                                        'default': '127.0.0.1'
                                    },
                                    'broker_port': {
                                        'description': 'Port of the RabbitMQ server',
                                        'type': 'integer',
                                        'minimum': 1,
                                        'default': 5672
                                    },
                                    'broker_virtual_host': {
                                        'description': 'RabbitMQ virtual host to connect to',
                                        'type': 'string',
                                        'default': ''
                                    },
                                    'broker_parameters': {
                                        'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                        'type': 'object',
                                        'default': {
                                            'heartbeat': 600
                                        },
                                        'properties': {
                                            'heartbeat': {
                                                'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                'type': 'integer',
                                                'default': 600,
                                                'minimum': 0
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'default_user_email': {
                        'type': ['string', 'null'],
                        'default': None
                    },
                    'test_profile': {
                        'type': 'boolean',
                        'default': False
                    },
                    'options': {
                        'type': 'object',
                        'properties': {
                            'runner.poll.interval': {
                                'type': 'integer',
                                'default': 60,
                                'minimum': 0,
                                'description': 'Polling interval in seconds to be used by process runners'
                            },
                            'daemon.default_workers': {
                                'type': 'integer',
                                'default': 1,
                                'minimum': 1,
                                'description': 'Default number of workers to be launched by `verdi daemon start`'
                            },
                            'daemon.timeout': {
                                'type': 'integer',
                                'default': 2,
                                'minimum': 0,
                                'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                            },
                            'daemon.worker_process_slots': {
                                'type': 'integer',
                                'default': 200,
                                'minimum': 1,
                                'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                            },
                            'daemon.recursion_limit': {
                                'type': 'integer',
                                'default': 3000,
                                'maximum': 100000,
                                'minimum': 1,
                                'description': 'Maximum recursion depth for the daemon workers'
                            },
                            'db.batch_size': {
                                'type': 'integer',
                                'default': 100000,
                                'minimum': 1,
                                'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                            },
                            'verdi.shell.auto_import': {
                                'type': 'string',
                                'default': '',
                                'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                            },
                            'logging.aiida_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                            },
                            'logging.verdi_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to console when running a `verdi` command'
                            },
                            'logging.db_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'REPORT',
                                'description': 'Minimum level to log to the DbLog table'
                            },
                            'logging.plumpy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                            },
                            'logging.kiwipy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                            },
                            'logging.paramiko_loglevel': {
                                'key': 'logging_paramiko_log_level',
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                            },
                            'logging.alembic_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                            },
                            'logging.sqlalchemy_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                            },
                            'logging.circus_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'INFO',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                            },
                            'logging.aiopika_loglevel': {
                                'type': 'string',
                                'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                'default': 'WARNING',
                                'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                            },
                            'warnings.showdeprecations': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print AiiDA deprecation warnings'
                            },
                            'warnings.development_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                'global_only': True
                            },
                            'warnings.rabbitmq_version': {
                                'type': 'boolean',
                                'default': True,
                                'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                            },
                            'transport.task_retry_initial_interval': {
                                'type': 'integer',
                                'default': 20,
                                'minimum': 1,
                                'description': 'Initial time interval for the exponential backoff mechanism.'
                            },
                            'transport.task_maximum_attempts': {
                                'type': 'integer',
                                'default': 5,
                                'minimum': 1,
                                'description': 'Maximum number of transport task attempts before a Process is Paused.'
                            },
                            'rest_api.profile_switching': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                'global_only': True
                            },
                            'rmq.task_timeout': {
                                'type': 'integer',
                                'default': 10,
                                'minimum': 1,
                                'description': 'Timeout in seconds for communications with RabbitMQ'
                            },
                            'storage.sandbox': {
                                'type': 'string',
                                'description': 'Absolute path to the directory to store sandbox folders.'
                            },
                            'caching.default_enabled': {
                                'type': 'boolean',
                                'default': False,
                                'description': 'Enable calculation caching by default'
                            },
                            'caching.enabled_for': {
                                'description': 'Calculation entry points to enable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'caching.disabled_for': {
                                'description': 'Calculation entry points to disable caching on',
                                'type': 'array',
                                'default': [],
                                'items': {
                                    'type': 'string'
                                }
                            },
                            'autofill.user.email': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user email to use when creating new profiles.'
                            },
                            'autofill.user.first_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user first name to use when creating new profiles.'
                            },
                            'autofill.user.last_name': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user last name to use when creating new profiles.'
                            },
                            'autofill.user.institution': {
                                'type': 'string',
                                'global_only': True,
                                'description': 'Default user institution to use when creating new profiles.'
                            }
                        }
                    }
                }
            },
            rule='type'
        )
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_len = len(data)
        if not all(prop in data for prop in ['storage', 'process_control']):
            raise JsonSchemaValueException(
                '' + (name_prefix or 'data') + " must contain ['storage', 'process_control'] properties",
                value=data,
                name='' + (name_prefix or 'data') + '',
                definition={
                    'type': 'object',
                    'required': ['storage', 'process_control'],
                    'properties': {
                        'PROFILE_UUID': {
                            'description': "The profile's unique key",
                            'type': 'string'
                        },
                        'storage': {
                            'description': 'The storage configuration',
                            'type': 'object',
                            'required': ['backend', 'config'],
                            'properties': {
                                'backend': {
                                    'description': 'The storage backend type to use',
                                    'type': 'string',
                                    'default': 'psql_dos'
                                },
                                'config': {
                                    'description': 'The configuration to pass to the storage backend',
                                    'type': 'object',
                                    'properties': {
                                        'database_engine': {
                                            'type': 'string',
                                            'default': 'postgresql_psycopg2'
                                        },
                                        'database_port': {
                                            'type': ['integer', 'string'],
                                            'minimum': 1,
                                            'pattern': '\\d+',
                                            'default': 5432
                                        },
                                        'database_hostname': {
                                            'type': ['string', 'null'],
                                            'default': None
                                        },
                                        'database_username': {
                                            'type': 'string'
                                        },
                                        'database_password': {
                                            'type': ['string', 'null'],
                                            'default': None
                                        },
                                        'database_name': {
                                            'type': 'string'
                                        },
                                        'repository_uri': {
                                            'description': 'URI to the AiiDA object store',
                                            'type': 'string'
                                        }
                                    }
                                }
                            }
                        },
                        'process_control': {
                            'description': 'The process control configuration',
                            'type': 'object',
                            'required': ['backend', 'config'],
                            'properties': {
                                'backend': {
                                    'description': 'The process execution backend type to use',
                                    'type': 'string',
                                    'default': 'rabbitmq'
                                },
                                'config': {
                                    'description': 'The configuration to pass to the process execution backend',
                                    'type': 'object',
                                    'parameters': {
                                        'broker_protocol': {
                                            'description': 'Protocol for connecting to the RabbitMQ server',
                                            'type': 'string',
                                            'enum': ['amqp', 'amqps'],
                                            'default': 'amqp'
                                        },
                                        'broker_username': {
                                            'description': 'Username for RabbitMQ authentication',
                                            'type': 'string',
                                            'default': 'guest'
                                        },
                                        'broker_password': {
                                            'description': 'Password for RabbitMQ authentication',
                                            'type': 'string',
                                            'default': 'guest'
                                        },
                                        'broker_host': {
                                            'description': 'Hostname of the RabbitMQ server',
                                            'type': 'string',
                                            'default': '127.0.0.1'
                                        },
                                        'broker_port': {
                                            'description': 'Port of the RabbitMQ server',
                                            'type': 'integer',
                                            'minimum': 1,
                                            'default': 5672
                                        },
                                        'broker_virtual_host': {
                                            'description': 'RabbitMQ virtual host to connect to',
                                            'type': 'string',
                                            'default': ''
                                        },
                                        'broker_parameters': {
                                            'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                            'type': 'object',
                                            'default': {
                                                'heartbeat': 600
                                            },
                                            'properties': {
                                                'heartbeat': {
                                                    'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                    'type': 'integer',
                                                    'default': 600,
                                                    'minimum': 0
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        'default_user_email': {
                            'type': ['string', 'null'],
                            'default': None
                        },
                        'test_profile': {
                            'type': 'boolean',
                            'default': False
                        },
                        'options': {
                            'type': 'object',
                            'properties': {
                                'runner.poll.interval': {
                                    'type': 'integer',
                                    'default': 60,
                                    'minimum': 0,
                                    'description': 'Polling interval in seconds to be used by process runners'
                                },
                                'daemon.default_workers': {
                                    'type': 'integer',
                                    'default': 1,
                                    'minimum': 1,
                                    'description': 'Default number of workers to be launched by `verdi daemon start`'
                                },
                                'daemon.timeout': {
                                    'type': 'integer',
                                    'default': 2,
                                    'minimum': 0,
                                    'description': 'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon'
                                },
                                'daemon.worker_process_slots': {
                                    'type': 'integer',
                                    'default': 200,
                                    'minimum': 1,
                                    'description': 'Maximum number of concurrent process tasks that each daemon worker can handle'
                                },
                                'daemon.recursion_limit': {
                                    'type': 'integer',
                                    'default': 3000,
                                    'maximum': 100000,
                                    'minimum': 1,
                                    'description': 'Maximum recursion depth for the daemon workers'
                                },
                                'db.batch_size': {
                                    'type': 'integer',
                                    'default': 100000,
                                    'minimum': 1,
                                    'description': 'Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL (1GB) when creating large numbers of database records in one go.'
                                },
                                'verdi.shell.auto_import': {
                                    'type': 'string',
                                    'default': '',
                                    'description': "Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by ':'"
                                },
                                'logging.aiida_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger'
                                },
                                'logging.verdi_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to console when running a `verdi` command'
                                },
                                'logging.db_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'REPORT',
                                    'description': 'Minimum level to log to the DbLog table'
                                },
                                'logging.plumpy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger'
                                },
                                'logging.kiwipy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
                                },
                                'logging.paramiko_loglevel': {
                                    'key': 'logging_paramiko_log_level',
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
                                },
                                'logging.alembic_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
                                },
                                'logging.sqlalchemy_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
                                },
                                'logging.circus_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'INFO',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
                                },
                                'logging.aiopika_loglevel': {
                                    'type': 'string',
                                    'enum': ['CRITICAL', 'ERROR', 'WARNING', 'REPORT', 'INFO', 'DEBUG'],
                                    'default': 'WARNING',
                                    'description': 'Minimum level to log to daemon log and the `DbLog` table for the `aio_pika` logger'
                                },
                                'warnings.showdeprecations': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print AiiDA deprecation warnings'
                                },
                                'warnings.development_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when a profile is loaded while a development version is installed',
                                    'global_only': True
                                },
                                'warnings.rabbitmq_version': {
                                    'type': 'boolean',
                                    'default': True,
                                    'description': 'Whether to print a warning when an incompatible version of RabbitMQ is configured'
                                },
                                'transport.task_retry_initial_interval': {
                                    'type': 'integer',
                                    'default': 20,
                                    'minimum': 1,
                                    'description': 'Initial time interval for the exponential backoff mechanism.'
                                },
                                'transport.task_maximum_attempts': {
                                    'type': 'integer',
                                    'default': 5,
                                    'minimum': 1,
                                    'description': 'Maximum number of transport task attempts before a Process is Paused.'
                                },
                                'rest_api.profile_switching': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Toggle whether the profile can be specified in requests submitted to the REST API',
                                    'global_only': True
                                },
                                'rmq.task_timeout': {
                                    'type': 'integer',
                                    'default': 10,
                                    'minimum': 1,
                                    'description': 'Timeout in seconds for communications with RabbitMQ'
                                },
                                'storage.sandbox': {
                                    'type': 'string',
                                    'description': 'Absolute path to the directory to store sandbox folders.'
                                },
                                'caching.default_enabled': {
                                    'type': 'boolean',
                                    'default': False,
                                    'description': 'Enable calculation caching by default'
                                },
                                'caching.enabled_for': {
                                    'description': 'Calculation entry points to enable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'caching.disabled_for': {
                                    'description': 'Calculation entry points to disable caching on',
                                    'type': 'array',
                                    'default': [],
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'autofill.user.email': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user email to use when creating new profiles.'
                                },
                                'autofill.user.first_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user first name to use when creating new profiles.'
                                },
                                'autofill.user.last_name': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user last name to use when creating new profiles.'
                                },
                                'autofill.user.institution': {
                                    'type': 'string',
                                    'global_only': True,
                                    'description': 'Default user institution to use when creating new profiles.'
                                }
                            }
                        }
                    }
                },
                rule='required'
            )
        data_keys = set(data.keys())
        if 'PROFILE_UUID' in data_keys:
            data_keys.remove('PROFILE_UUID')
            data__PROFILEUUID = data['PROFILE_UUID']
            if not isinstance(data__PROFILEUUID, (str)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.PROFILE_UUID must be string',
                    value=data__PROFILEUUID,
                    name='' + (name_prefix or 'data') + '.PROFILE_UUID',
                    definition={
                        'description': "The profile's unique key",
                        'type': 'string'
                    },
                    rule='type'
                )
        if 'storage' in data_keys:
            data_keys.remove('storage')
            data__storage = data['storage']
            if not isinstance(data__storage, (dict)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.storage must be object',
                    value=data__storage,
                    name='' + (name_prefix or 'data') + '.storage',
                    definition={
                        'description': 'The storage configuration',
                        'type': 'object',
                        'required': ['backend', 'config'],
                        'properties': {
                            'backend': {
                                'description': 'The storage backend type to use',
                                'type': 'string',
                                'default': 'psql_dos'
                            },
                            'config': {
                                'description': 'The configuration to pass to the storage backend',
                                'type': 'object',
                                'properties': {
                                    'database_engine': {
                                        'type': 'string',
                                        'default': 'postgresql_psycopg2'
                                    },
                                    'database_port': {
                                        'type': ['integer', 'string'],
                                        'minimum': 1,
                                        'pattern': '\\d+',
                                        'default': 5432
                                    },
                                    'database_hostname': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_username': {
                                        'type': 'string'
                                    },
                                    'database_password': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_name': {
                                        'type': 'string'
                                    },
                                    'repository_uri': {
                                        'description': 'URI to the AiiDA object store',
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    },
                    rule='type'
                )
            data__storage_is_dict = isinstance(data__storage, dict)
            if data__storage_is_dict:
                data__storage_len = len(data__storage)
                if not all(prop in data__storage for prop in ['backend', 'config']):
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + ".storage must contain ['backend', 'config'] properties",
                        value=data__storage,
                        name='' + (name_prefix or 'data') + '.storage',
                        definition={
                            'description': 'The storage configuration',
                            'type': 'object',
                            'required': ['backend', 'config'],
                            'properties': {
                                'backend': {
                                    'description': 'The storage backend type to use',
                                    'type': 'string',
                                    'default': 'psql_dos'
                                },
                                'config': {
                                    'description': 'The configuration to pass to the storage backend',
                                    'type': 'object',
                                    'properties': {
                                        'database_engine': {
                                            'type': 'string',
                                            'default': 'postgresql_psycopg2'
                                        },
                                        'database_port': {
                                            'type': ['integer', 'string'],
                                            'minimum': 1,
                                            'pattern': '\\d+',
                                            'default': 5432
                                        },
                                        'database_hostname': {
                                            'type': ['string', 'null'],
                                            'default': None
                                        },
                                        'database_username': {
                                            'type': 'string'
                                        },
                                        'database_password': {
                                            'type': ['string', 'null'],
                                            'default': None
                                        },
                                        'database_name': {
                                            'type': 'string'
                                        },
                                        'repository_uri': {
                                            'description': 'URI to the AiiDA object store',
                                            'type': 'string'
                                        }
                                    }
                                }
                            }
                        },
                        rule='required'
                    )
                data__storage_keys = set(data__storage.keys())
                if 'backend' in data__storage_keys:
                    data__storage_keys.remove('backend')
                    data__storage__backend = data__storage['backend']
                    if not isinstance(data__storage__backend, (str)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.storage.backend must be string',
                            value=data__storage__backend,
                            name='' + (name_prefix or 'data') + '.storage.backend',
                            definition={
                                'description': 'The storage backend type to use',
                                'type': 'string',
                                'default': 'psql_dos'
                            },
                            rule='type'
                        )
                else:
                    data__storage['backend'] = 'psql_dos'
                if 'config' in data__storage_keys:
                    data__storage_keys.remove('config')
                    data__storage__config = data__storage['config']
                    if not isinstance(data__storage__config, (dict)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.storage.config must be object',
                            value=data__storage__config,
                            name='' + (name_prefix or 'data') + '.storage.config',
                            definition={
                                'description': 'The configuration to pass to the storage backend',
                                'type': 'object',
                                'properties': {
                                    'database_engine': {
                                        'type': 'string',
                                        'default': 'postgresql_psycopg2'
                                    },
                                    'database_port': {
                                        'type': ['integer', 'string'],
                                        'minimum': 1,
                                        'pattern': '\\d+',
                                        'default': 5432
                                    },
                                    'database_hostname': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_username': {
                                        'type': 'string'
                                    },
                                    'database_password': {
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    'database_name': {
                                        'type': 'string'
                                    },
                                    'repository_uri': {
                                        'description': 'URI to the AiiDA object store',
                                        'type': 'string'
                                    }
                                }
                            },
                            rule='type'
                        )
                    data__storage__config_is_dict = isinstance(data__storage__config, dict)
                    if data__storage__config_is_dict:
                        data__storage__config_keys = set(data__storage__config.keys())
                        if 'database_engine' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_engine')
                            data__storage__config__databaseengine = data__storage__config['database_engine']
                            if not isinstance(data__storage__config__databaseengine, (str)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') + '.storage.config.database_engine must be string',
                                    value=data__storage__config__databaseengine,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_engine',
                                    definition={
                                        'type': 'string',
                                        'default': 'postgresql_psycopg2'
                                    },
                                    rule='type'
                                )
                        else:
                            data__storage__config['database_engine'] = 'postgresql_psycopg2'
                        if 'database_port' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_port')
                            data__storage__config__databaseport = data__storage__config['database_port']
                            if not isinstance(data__storage__config__databaseport, (int, str)) and not (
                                isinstance(data__storage__config__databaseport, float) and
                                data__storage__config__databaseport.is_integer()
                            ) or isinstance(data__storage__config__databaseport, bool):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') +
                                    '.storage.config.database_port must be integer or string',
                                    value=data__storage__config__databaseport,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_port',
                                    definition={
                                        'type': ['integer', 'string'],
                                        'minimum': 1,
                                        'pattern': '\\d+',
                                        'default': 5432
                                    },
                                    rule='type'
                                )
                            if isinstance(data__storage__config__databaseport, str):
                                if not REGEX_PATTERNS['\\d+'].search(data__storage__config__databaseport):
                                    raise JsonSchemaValueException(
                                        '' + (name_prefix or 'data') +
                                        '.storage.config.database_port must match pattern \\d+',
                                        value=data__storage__config__databaseport,
                                        name='' + (name_prefix or 'data') + '.storage.config.database_port',
                                        definition={
                                            'type': ['integer', 'string'],
                                            'minimum': 1,
                                            'pattern': '\\d+',
                                            'default': 5432
                                        },
                                        rule='pattern'
                                    )
                            if isinstance(data__storage__config__databaseport, (int, float, Decimal)):
                                if data__storage__config__databaseport < 1:
                                    raise JsonSchemaValueException(
                                        '' + (name_prefix or 'data') +
                                        '.storage.config.database_port must be bigger than or equal to 1',
                                        value=data__storage__config__databaseport,
                                        name='' + (name_prefix or 'data') + '.storage.config.database_port',
                                        definition={
                                            'type': ['integer', 'string'],
                                            'minimum': 1,
                                            'pattern': '\\d+',
                                            'default': 5432
                                        },
                                        rule='minimum'
                                    )
                        else:
                            data__storage__config['database_port'] = 5432
                        if 'database_hostname' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_hostname')
                            data__storage__config__databasehostname = data__storage__config['database_hostname']
                            if not isinstance(data__storage__config__databasehostname, (str, NoneType)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') +
                                    '.storage.config.database_hostname must be string or null',
                                    value=data__storage__config__databasehostname,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_hostname',
                                    definition={
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    rule='type'
                                )
                        else:
                            data__storage__config['database_hostname'] = None
                        if 'database_username' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_username')
                            data__storage__config__databaseusername = data__storage__config['database_username']
                            if not isinstance(data__storage__config__databaseusername, (str)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') + '.storage.config.database_username must be string',
                                    value=data__storage__config__databaseusername,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_username',
                                    definition={'type': 'string'},
                                    rule='type'
                                )
                        if 'database_password' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_password')
                            data__storage__config__databasepassword = data__storage__config['database_password']
                            if not isinstance(data__storage__config__databasepassword, (str, NoneType)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') +
                                    '.storage.config.database_password must be string or null',
                                    value=data__storage__config__databasepassword,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_password',
                                    definition={
                                        'type': ['string', 'null'],
                                        'default': None
                                    },
                                    rule='type'
                                )
                        else:
                            data__storage__config['database_password'] = None
                        if 'database_name' in data__storage__config_keys:
                            data__storage__config_keys.remove('database_name')
                            data__storage__config__databasename = data__storage__config['database_name']
                            if not isinstance(data__storage__config__databasename, (str)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') + '.storage.config.database_name must be string',
                                    value=data__storage__config__databasename,
                                    name='' + (name_prefix or 'data') + '.storage.config.database_name',
                                    definition={'type': 'string'},
                                    rule='type'
                                )
                        if 'repository_uri' in data__storage__config_keys:
                            data__storage__config_keys.remove('repository_uri')
                            data__storage__config__repositoryuri = data__storage__config['repository_uri']
                            if not isinstance(data__storage__config__repositoryuri, (str)):
                                raise JsonSchemaValueException(
                                    '' + (name_prefix or 'data') + '.storage.config.repository_uri must be string',
                                    value=data__storage__config__repositoryuri,
                                    name='' + (name_prefix or 'data') + '.storage.config.repository_uri',
                                    definition={
                                        'description': 'URI to the AiiDA object store',
                                        'type': 'string'
                                    },
                                    rule='type'
                                )
        if 'process_control' in data_keys:
            data_keys.remove('process_control')
            data__processcontrol = data['process_control']
            if not isinstance(data__processcontrol, (dict)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.process_control must be object',
                    value=data__processcontrol,
                    name='' + (name_prefix or 'data') + '.process_control',
                    definition={
                        'description': 'The process control configuration',
                        'type': 'object',
                        'required': ['backend', 'config'],
                        'properties': {
                            'backend': {
                                'description': 'The process execution backend type to use',
                                'type': 'string',
                                'default': 'rabbitmq'
                            },
                            'config': {
                                'description': 'The configuration to pass to the process execution backend',
                                'type': 'object',
                                'parameters': {
                                    'broker_protocol': {
                                        'description': 'Protocol for connecting to the RabbitMQ server',
                                        'type': 'string',
                                        'enum': ['amqp', 'amqps'],
                                        'default': 'amqp'
                                    },
                                    'broker_username': {
                                        'description': 'Username for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_password': {
                                        'description': 'Password for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_host': {
                                        'description': 'Hostname of the RabbitMQ server',
                                        'type': 'string',
                                        'default': '127.0.0.1'
                                    },
                                    'broker_port': {
                                        'description': 'Port of the RabbitMQ server',
                                        'type': 'integer',
                                        'minimum': 1,
                                        'default': 5672
                                    },
                                    'broker_virtual_host': {
                                        'description': 'RabbitMQ virtual host to connect to',
                                        'type': 'string',
                                        'default': ''
                                    },
                                    'broker_parameters': {
                                        'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                        'type': 'object',
                                        'default': {
                                            'heartbeat': 600
                                        },
                                        'properties': {
                                            'heartbeat': {
                                                'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                'type': 'integer',
                                                'default': 600,
                                                'minimum': 0
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    rule='type'
                )
            data__processcontrol_is_dict = isinstance(data__processcontrol, dict)
            if data__processcontrol_is_dict:
                data__processcontrol_len = len(data__processcontrol)
                if not all(prop in data__processcontrol for prop in ['backend', 'config']):
                    raise JsonSchemaValueException(
                        '' + (name_prefix or 'data') + ".process_control must contain ['backend', 'config'] properties",
                        value=data__processcontrol,
                        name='' + (name_prefix or 'data') + '.process_control',
                        definition={
                            'description': 'The process control configuration',
                            'type': 'object',
                            'required': ['backend', 'config'],
                            'properties': {
                                'backend': {
                                    'description': 'The process execution backend type to use',
                                    'type': 'string',
                                    'default': 'rabbitmq'
                                },
                                'config': {
                                    'description': 'The configuration to pass to the process execution backend',
                                    'type': 'object',
                                    'parameters': {
                                        'broker_protocol': {
                                            'description': 'Protocol for connecting to the RabbitMQ server',
                                            'type': 'string',
                                            'enum': ['amqp', 'amqps'],
                                            'default': 'amqp'
                                        },
                                        'broker_username': {
                                            'description': 'Username for RabbitMQ authentication',
                                            'type': 'string',
                                            'default': 'guest'
                                        },
                                        'broker_password': {
                                            'description': 'Password for RabbitMQ authentication',
                                            'type': 'string',
                                            'default': 'guest'
                                        },
                                        'broker_host': {
                                            'description': 'Hostname of the RabbitMQ server',
                                            'type': 'string',
                                            'default': '127.0.0.1'
                                        },
                                        'broker_port': {
                                            'description': 'Port of the RabbitMQ server',
                                            'type': 'integer',
                                            'minimum': 1,
                                            'default': 5672
                                        },
                                        'broker_virtual_host': {
                                            'description': 'RabbitMQ virtual host to connect to',
                                            'type': 'string',
                                            'default': ''
                                        },
                                        'broker_parameters': {
                                            'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                            'type': 'object',
                                            'default': {
                                                'heartbeat': 600
                                            },
                                            'properties': {
                                                'heartbeat': {
                                                    'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                    'type': 'integer',
                                                    'default': 600,
                                                    'minimum': 0
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        rule='required'
                    )
                data__processcontrol_keys = set(data__processcontrol.keys())
                if 'backend' in data__processcontrol_keys:
                    data__processcontrol_keys.remove('backend')
                    data__processcontrol__backend = data__processcontrol['backend']
                    if not isinstance(data__processcontrol__backend, (str)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.process_control.backend must be string',
                            value=data__processcontrol__backend,
                            name='' + (name_prefix or 'data') + '.process_control.backend',
                            definition={
                                'description': 'The process execution backend type to use',
                                'type': 'string',
                                'default': 'rabbitmq'
                            },
                            rule='type'
                        )
                else:
                    data__processcontrol['backend'] = 'rabbitmq'
                if 'config' in data__processcontrol_keys:
                    data__processcontrol_keys.remove('config')
                    data__processcontrol__config = data__processcontrol['config']
                    if not isinstance(data__processcontrol__config, (dict)):
                        raise JsonSchemaValueException(
                            '' + (name_prefix or 'data') + '.process_control.config must be object',
                            value=data__processcontrol__config,
                            name='' + (name_prefix or 'data') + '.process_control.config',
                            definition={
                                'description': 'The configuration to pass to the process execution backend',
                                'type': 'object',
                                'parameters': {
                                    'broker_protocol': {
                                        'description': 'Protocol for connecting to the RabbitMQ server',
                                        'type': 'string',
                                        'enum': ['amqp', 'amqps'],
                                        'default': 'amqp'
                                    },
                                    'broker_username': {
                                        'description': 'Username for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_password': {
                                        'description': 'Password for RabbitMQ authentication',
                                        'type': 'string',
                                        'default': 'guest'
                                    },
                                    'broker_host': {
                                        'description': 'Hostname of the RabbitMQ server',
                                        'type': 'string',
                                        'default': '127.0.0.1'
                                    },
                                    'broker_port': {
                                        'description': 'Port of the RabbitMQ server',
                                        'type': 'integer',
                                        'minimum': 1,
                                        'default': 5672
                                    },
                                    'broker_virtual_host': {
                                        'description': 'RabbitMQ virtual host to connect to',
                                        'type': 'string',
                                        'default': ''
                                    },
                                    'broker_parameters': {
                                        'description': 'RabbitMQ arguments that will be encoded as query parameters',
                                        'type': 'object',
                                        'default': {
                                            'heartbeat': 600
                                        },
                                        'properties': {
                                            'heartbeat': {
                                                'description': 'After how many seconds the peer TCP connection should be considered unreachable',
                                                'type': 'integer',
                                                'default': 600,
                                                'minimum': 0
                                            }
                                        }
                                    }
                                }
                            },
                            rule='type'
                        )
        if 'default_user_email' in data_keys:
            data_keys.remove('default_user_email')
            data__defaultuseremail = data['default_user_email']
            if not isinstance(data__defaultuseremail, (str, NoneType)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.default_user_email must be string or null',
                    value=data__defaultuseremail,
                    name='' + (name_prefix or 'data') + '.default_user_email',
                    definition={
                        'type': ['string', 'null'],
                        'default': None
                    },
                    rule='type'
                )
        else:
            data['default_user_email'] = None
        if 'test_profile' in data_keys:
            data_keys.remove('test_profile')
            data__testprofile = data['test_profile']
            if not isinstance(data__testprofile, (bool)):
                raise JsonSchemaValueException(
                    '' + (name_prefix or 'data') + '.test_profile must be boolean',
                    value=data__testprofile,
                    name='' + (name_prefix or 'data') + '.test_profile',
                    definition={
                        'type': 'boolean',
                        'default': False
                    },
                    rule='type'
                )
        else:
            data['test_profile'] = False
        if 'options' in data_keys:
            data_keys.remove('options')
            data__options = data['options']
            validate___definitions_options(data__options, custom_formats, (name_prefix or 'data') + '.options')
    return data
