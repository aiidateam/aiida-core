# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,invalid-name
"""
Tests for the migrations of the attributes, extras and settings from EAV to JSONB
Migration 0037_attributes_extras_settings_json
"""

import copy

from django.db import transaction

from .test_migrations_common import TestMigrations

# The following sample dictionary can be used for the conversion test of attributes and extras
SAMPLE_DICT = {
    'bool': True,
    '001': 2,
    '17': 'string',
    'integer': 12,
    'float': 26.2,
    'string': 'a string',
    'dict': {
        '25': [True, False],
        'a': 'b',
        'sublist': [1, 2, 3],
        'subdict': {
            'c': 'd'
        }
    },
    'list': [1, True, 'ggg', {
        'h': 'j'
    }, [9, 8, 7]],
}

# The following base classes contain just model declaration for DbAttributes
# and DbExtras and are needed for the methods found at the
# DbAttributeFunctionality and DbExtraFunctionality and used for the deserialization
# of attribute and extras dictionaries
db_attribute_base_model = None
db_extra_base_model = None


class TestAttributesExtrasToJSONMigrationSimple(TestMigrations):
    """
    A "simple" test for the attributes and extra migration from EAV to JSONB.
    It stores a sample dictionary using the EAV deserialization of AiiDA Django
    for the attributes and extras. Then the test checks that they are corerctly
    converted to JSONB.
    """
    migrate_from = '0036_drop_computer_transport_params'
    migrate_to = '0037_attributes_extras_settings_json'

    # In the following dictionary we store the generated nodes (ids, attributes and extras)
    # The correct migration of these nodes will be checked at the test
    nodes_to_verify = dict()

    def setUpBeforeMigration(self):
        global db_attribute_base_model, db_extra_base_model  # pylint: disable=global-statement

        db_node_model = self.apps.get_model('db', 'DbNode')
        db_computer_model = self.apps.get_model('db', 'DbComputer')
        # The following base models are initialized here since the model at this point
        # it has the corresponding EAV tables
        db_attribute_base_model = self.apps.get_model('db', 'DbAttribute')
        db_extra_base_model = self.apps.get_model('db', 'DbExtra')

        computer = db_computer_model(
            name='localhost_migration',
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro',
            metadata={'workdir': '/tmp/aiida'}
        )
        computer.save()

        node = db_node_model(node_type='data.Data.', dbcomputer_id=computer.id, user_id=self.default_user.id)
        node.save()

        for key, value in SAMPLE_DICT.items():
            DbAttributeFunctionality.set_value_for_node(node, key, value)

        for key, value in SAMPLE_DICT.items():
            DbExtraFunctionality.set_value_for_node(node, key, value)

        self.nodes_to_verify[node.id] = dict()
        self.nodes_to_verify[node.id]['attr'] = copy.deepcopy(SAMPLE_DICT)
        self.nodes_to_verify[node.id]['extr'] = copy.deepcopy(SAMPLE_DICT)

    def test_attributes_extras_migration(self):
        """Verify that the attributes and extras were migrated correctly"""
        db_node_model = self.apps.get_model('db', 'DbNode')
        for curr_dbnode in db_node_model.objects.all():
            self.assertEqual(curr_dbnode.attributes, self.nodes_to_verify[curr_dbnode.id]['attr'])
            self.assertEqual(curr_dbnode.extras, self.nodes_to_verify[curr_dbnode.id]['extr'])


class TestAttributesExtrasToJSONMigrationManyNodes(TestMigrations):
    """
    This test comparing to the previous one (TestAttributesExtrasToJSONMigrationSimple), it
    creates several nodes with different atributes and extras and checks their correct
    migration one-by-one.
    """
    migrate_from = '0036_drop_computer_transport_params'
    migrate_to = '0037_attributes_extras_settings_json'

    # In the following dictionary we store the generated nodes (ids, attributes and extras)
    # The correct migration of these nodes will be checked at the test
    nodes_to_verify = dict()

    # Number of nodes to create
    nodes_no_to_create = 20

    def setUpBeforeMigration(self):
        global db_attribute_base_model, db_extra_base_model  # pylint: disable=global-statement

        db_node_model = self.apps.get_model('db', 'DbNode')
        db_computer_model = self.apps.get_model('db', 'DbComputer')
        # The following base models are initialized here since the model at this point
        # it has the corresponding EAV tables
        db_attribute_base_model = self.apps.get_model('db', 'DbAttribute')
        db_extra_base_model = self.apps.get_model('db', 'DbExtra')

        computer = db_computer_model(
            name='localhost_migration',
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro',
            metadata={'workdir': '/tmp/aiida'}
        )
        computer.save()

        with transaction.atomic():
            for _ in range(self.nodes_no_to_create):
                node = db_node_model(node_type='data.Data.', dbcomputer_id=computer.id, user_id=self.default_user.id)
                node.save()

                attr_copy = copy.deepcopy(SAMPLE_DICT)
                attr_copy['type_of_json'] = 'attr'
                attr_copy['node_id'] = node.id

                # Setting the attributes as it used to be set (with the same methods)
                for key in attr_copy.keys():
                    DbAttributeFunctionality.set_value_for_node(node, key, attr_copy[key])

                extr_copy = copy.deepcopy(SAMPLE_DICT)
                extr_copy['type_of_json'] = 'extr'
                extr_copy['node_id'] = node.id

                # Setting the extras as it used to be set (with the same methods)
                for key in extr_copy.keys():
                    DbExtraFunctionality.set_value_for_node(node, key, extr_copy[key])

                self.nodes_to_verify[node.id] = dict()
                self.nodes_to_verify[node.id]['attr'] = attr_copy
                self.nodes_to_verify[node.id]['extr'] = extr_copy

    def test_attributes_extras_migration_many(self):
        """Verify that the attributes and extras were migrated correctly"""
        db_node_model = self.apps.get_model('db', 'DbNode')
        for curr_dbnode in db_node_model.objects.all():
            self.assertEqual(curr_dbnode.attributes, self.nodes_to_verify[curr_dbnode.id]['attr'])
            self.assertEqual(curr_dbnode.extras, self.nodes_to_verify[curr_dbnode.id]['extr'])


class TestSettingsToJSONMigration(TestMigrations):
    """
    This test checks the correct migration of the settings. Setting records were used as an
    example from a typical settings table of Django EAV.
    """
    migrate_from = '0036_drop_computer_transport_params'
    migrate_to = '0037_attributes_extras_settings_json'

    # The settings to create and verify
    settings_info = dict()

    def setUpBeforeMigration(self):
        from aiida.common import timezone

        db_setting_model = self.apps.get_model('db', 'DbSetting')

        self.settings_info['2daemon|task_stop|updater2'] = dict(
            key='2daemon|task_stop|updater2',
            datatype='date',
            dval=timezone.datetime_to_isoformat(timezone.now()),
            description='The last time the daemon finished to run '
            'the task \'updater\' (updater)'
        )
        self.settings_info['2daemon|task_start|updater2'] = dict(
            key='2daemon|task_start|updater2',
            datatype='date',
            dval=timezone.datetime_to_isoformat(timezone.now()),
            description='The last time the daemon started to run '
            'the task \'updater\' (updater)'
        )
        self.settings_info['2db|backend2'] = dict(
            key='2db|backend2',
            datatype='txt',
            tval='django',
            description='The backend used to communicate with the database.'
        )
        self.settings_info['2daemon|user2'] = dict(
            key='2daemon|user2',
            datatype='txt',
            tval='aiida@theossrv5.epfl.ch',
            description='The only user that is allowed to run the AiiDA daemon on '
            'this DB instance'
        )
        self.settings_info['2db|schemaversion2'] = dict(
            key='2db|schemaversion2',
            datatype='txt',
            tval=' 1.0.8',
            description='The version of the schema used in this database.'
        )

        with transaction.atomic():
            for setting_info in self.settings_info.values():
                setting = db_setting_model(**setting_info)
                setting.save()

    def test_settings_migration(self):
        """Verify that the settings were migrated correctly"""
        db_setting_model = self.apps.get_model('db', 'DbSetting')
        for curr_setting in db_setting_model.objects.filter(key__in=self.settings_info.keys()).all():
            curr_setting_info = self.settings_info[curr_setting.key]
            self.assertEqual(curr_setting.description, curr_setting_info['description'])
            if curr_setting_info['datatype'] == 'txt':
                self.assertEqual(curr_setting.val, curr_setting_info['tval'])
            elif curr_setting_info['datatype'] == 'date':
                self.assertEqual(curr_setting.val, curr_setting_info['dval'])

    def tearDown(self):
        """
        Deletion of settings - this is needed because settings are not deleted by the
        typical test cleanup methods.
        """
        db_setting_model = self.apps.get_model('db', 'DbSetting')
        db_setting_model.objects.filter(key__in=self.settings_info.keys()).delete()
        super().tearDown()


# pylint: disable=no-init, old-style-class, too-few-public-methods, dangerous-default-value, too-many-statements
# pylint: disable= no-else-return, too-many-arguments, too-many-branches, fixme
class DbMultipleValueAttributeBaseClass():
    """
    Abstract base class for tables storing attribute + value data, of
    different data types (without any association to a Node).
    """
    # separator for subfields
    _sep = '.'  # The AIIDA_ATTRIBUTE_SEP

    class Meta:
        abstract = True
        unique_together = (('key',),)

    # There are no subspecifiers. If instead you want to group attributes
    # (e.g. by node, as it is done in the DbAttributeBaseClass), specify here
    # the field name
    _subspecifier_field_name = None

    @property
    def subspecifier_pk(self):
        """
        Return the subspecifier PK in the database (or None, if no
        subspecifier should be used)
        """
        if self._subspecifier_field_name is None:
            return None
        else:
            return getattr(self, self._subspecifier_field_name).pk

    @classmethod
    def validate_key(cls, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.).

        :return: None if the key is valid
        :raise aiida.common.ValidationError: if the key is not valid
        """
        from aiida.backends.utils import AIIDA_ATTRIBUTE_SEP
        from aiida.common.exceptions import ValidationError

        if not isinstance(key, str):
            raise ValidationError('The key must be a string.')
        if not key:
            raise ValidationError('The key cannot be an empty string.')
        if AIIDA_ATTRIBUTE_SEP in key:
            raise ValidationError(
                "The separator symbol '{}' cannot be present "
                'in the key of attributes, extras, etc.'.format(AIIDA_ATTRIBUTE_SEP)
            )

    @classmethod
    def set_value(
        cls, key, value, with_transaction=True, subspecifier_value=None, other_attribs={}, stop_if_existing=False
    ):
        """
        Set a new value in the DB, possibly associated to the given subspecifier.

        :note: This method also stored directly in the DB.

        :param key: a string with the key to create (must be a level-0
          attribute, that is it cannot contain the separator cls._sep).
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param with_transaction: True if you want this function to be managed
          with transactions. Set to False if you already have a manual
          management of transactions in the block where you are calling this
          function (useful for speed improvements to avoid recursive
          transactions)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the new entry would violate an
           uniqueness constraint in the DB (same key, or same key+node,
           depending on the specific subclass). Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.
        """
        cls.validate_key(key)

        try:
            if with_transaction:
                sid = transaction.savepoint()

            # create_value returns a list of nodes to store
            to_store = cls.create_value(key, value, subspecifier_value=subspecifier_value, other_attribs=other_attribs)

            if to_store:
                # if not stop_if_existing:
                #     # Delete the olf values if stop_if_existing is False,
                #     # otherwise don't delete them and hope they don't
                #     # exist. If they exist, I'll get an UniquenessError
                #
                #     ## NOTE! Be careful in case the extra/attribute to
                #     ## store is not a simple attribute but a list or dict:
                #     ## like this, it should be ok because if we are
                #     ## overwriting an entry it will stop anyway to avoid
                #     ## to overwrite the main entry, but otherwise
                #     ## there is the risk that trailing pieces remain
                #     ## so in general it is good to recursively clean
                #     ## all sub-items.
                #     cls.del_value(key,
                #                   subspecifier_value=subspecifier_value)
                for my_obj in to_store:
                    my_obj.save()

                # cls.objects.bulk_create(to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except BaseException as exc:  # All exceptions including CTRL+C, ...
            from django.db.utils import IntegrityError
            from aiida.common.exceptions import UniquenessError

            if with_transaction:
                transaction.savepoint_rollback(sid)
            if isinstance(exc, IntegrityError) and stop_if_existing:
                raise UniquenessError(
                    'Impossible to create the required '
                    'entry '
                    "in table '{}', "
                    'another entry already exists and the creation would '
                    'violate an uniqueness constraint.\nFurther details: '
                    '{}'.format(cls.__name__, exc)
                )
            raise

    @classmethod
    def create_value(cls, key, value, subspecifier_value=None, other_attribs={}):
        """
        Create a new list of attributes, without storing them, associated
        with the current key/value pair (and to the given subspecifier,
        e.g. the DbNode for DbAttributes and DbExtras).

        :note: No hits are done on the DB, in particular no check is done
          on the existence of the given nodes.

        :param key: a string with the key to create (can contain the
          separator cls._sep if this is a sub-attribute: indeed, this
          function calls itself recursively)
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).

        :return: always a list of class instances; it is the user
          responsibility to store such entries (typically with a Django
          bulk_create() call).
        """
        import datetime

        from aiida.common import json
        from aiida.common.timezone import is_naive, make_aware, get_current_timezone

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError(
                    'You cannot specify a subspecifier value for '
                    'class {} because it has no subspecifiers'
                    ''.format(cls.__name__)
                )
            if issubclass(cls, DbAttributeFunctionality):
                new_entry = db_attribute_base_model(key=key, **other_attribs)
            else:
                new_entry = db_extra_base_model(key=key, **other_attribs)
        else:
            if subspecifier_value is None:
                raise ValueError(
                    'You also have to specify a subspecifier value '
                    'for class {} (the {})'.format(cls.__name__, cls._subspecifier_field_name)
                )
            further_params = other_attribs.copy()
            further_params.update({cls._subspecifier_field_name: subspecifier_value})
            # new_entry = cls(key=key, **further_params)
            if issubclass(cls, DbAttributeFunctionality):
                new_entry = db_attribute_base_model(key=key, **further_params)
            else:
                new_entry = db_extra_base_model(key=key, **further_params)

        list_to_return = [new_entry]

        if value is None:
            new_entry.datatype = 'none'
            new_entry.bval = None
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, bool):
            new_entry.datatype = 'bool'
            new_entry.bval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, int):
            new_entry.datatype = 'int'
            new_entry.ival = value
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, float):
            new_entry.datatype = 'float'
            new_entry.fval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.bval = None
            new_entry.dval = None

        elif isinstance(value, str):
            new_entry.datatype = 'txt'
            new_entry.tval = value
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, datetime.datetime):

            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value

            new_entry.datatype = 'date'
            # TODO: time-aware and time-naive datetime objects, see
            # https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#naive-and-aware-datetime-objects
            new_entry.dval = value_to_set
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        elif isinstance(value, (list, tuple)):

            new_entry.datatype = 'list'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for i, subv in enumerate(value):
                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(
                    cls.create_value(
                        key=('{}{}{:d}'.format(key, cls._sep, i)), value=subv, subspecifier_value=subspecifier_value
                    )
                )

        elif isinstance(value, dict):

            new_entry.datatype = 'dict'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for subk, subv in value.items():
                cls.validate_key(subk)

                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(
                    cls.create_value(
                        key='{}{}{}'.format(key, cls._sep, subk), value=subv, subspecifier_value=subspecifier_value
                    )
                )
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError(
                    'Unable to store the value: it must be either a basic datatype, or json-serializable: {}'.
                    format(value)
                )

            new_entry.datatype = 'json'
            new_entry.tval = jsondata
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        return list_to_return


class DbAttributeBaseClass(DbMultipleValueAttributeBaseClass):
    """
    Abstract base class for tables storing element-attribute-value data.
    Element is the dbnode; attribute is the key name.
    Value is the specific value to store.

    This table had different SQL columns to store different types of data, and
    a datatype field to know the actual datatype.

    Moreover, this class unpacks dictionaries and lists when possible, so that
    it is possible to query inside recursive lists and dicts.
    """

    # In this way, the related name for the DbAttribute inherited class will be
    # 'dbattributes' and for 'dbextra' will be 'dbextras'
    # Moreover, automatically destroy attributes and extras if the parent
    # node is deleted
    # dbnode = m.ForeignKey('DbNode', related_name='%(class)ss', on_delete=m.CASCADE)
    # max_length is required by MySql to have indexes and unique constraints

    _subspecifier_field_name = 'dbnode'

    @classmethod
    def set_value_for_node(cls, dbnode, key, value, with_transaction=True, stop_if_existing=False):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key.
        To be used only internally.

        :todo: there may be some error on concurrent write;
           not checked in this unlucky case!

        :param dbnode: the dbnode for which the attribute should be stored;
          if an integer is passed, it will raise, since this functionality is not
          supported in the models for the migrations.
        :param key: the key of the attribute to store; must be a level-zero
          attribute (i.e., no separators in the key)
        :param value: the value of the attribute to store
        :param with_transaction: if True (default), do this within a transaction,
           so that nothing gets stored if a subitem cannot be created.
           Otherwise, if this parameter is False, no transaction management
           is performed.
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the key already exists
           for the given node. Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.

        :raise ValueError: if the key contains the separator symbol used
            internally to unpack dictionaries and lists (defined in cls._sep).
        """
        if isinstance(dbnode, int):
            raise ValueError('Integers (the dbnode pk) are not supported as input.')
        else:
            dbnode_node = dbnode

        cls.set_value(
            key,
            value,
            with_transaction=with_transaction,
            subspecifier_value=dbnode_node,
            stop_if_existing=stop_if_existing
        )

    def __str__(self):
        # pylint: disable=no-member
        return '[{} ({})].{} ({})'.format(
            self.dbnode.get_simple_name(invalid_result='Unknown node'),
            self.dbnode.pk,
            self.key,
            self.datatype,
        )


class DbAttributeFunctionality(DbAttributeBaseClass):  # pylint: disable=no-init
    """
    This class defines all the methods that are needed for the correct
    deserialization of given attribute dictionaries to the EAV table.
    It is a stripped-down Django EAV schema to the absolutely necessary
    methods for this deserialization.
    """
    pass  # pylint: disable=unnecessary-pass


class DbExtraFunctionality(DbAttributeBaseClass):  # pylint: disable=no-init
    """
    This class defines all the methods that are needed for the correct
    deserialization of given extras dictionaries to the EAV table.
    It is a stripped-down Django EAV schema to the absolutely necessary
    methods for this deserialization.
    """
    pass  # pylint: disable=unnecessary-pass
