# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Module that defines db models."""
import contextlib

from django.contrib.postgres.fields import JSONField
from django.db import models as m
from django.db.models.query import QuerySet
from pytz import UTC

import aiida.backends.djsite.db.migrations as migrations
from aiida.common import timezone
from aiida.common.utils import get_new_uuid

# This variable identifies the schema version of this file.
# Every time you change the schema below in *ANY* way, REMEMBER TO CHANGE
# the version here in the migration file and update migrations/__init__.py.
# See the documentation for how to do all this.
#
# The version is checked at code load time to verify that the code schema
# version and the DB schema version are the same. (The DB schema version
# is stored in the DbSetting table and the check is done in the
# load_dbenv() function).
SCHEMA_VERSION = migrations.current_schema_version()


class AiidaQuerySet(QuerySet):
    """Represent a lazy database lookup for a set of objects."""

    def iterator(self, chunk_size=2000):
        from aiida.orm.implementation.django import convert
        for obj in super().iterator(chunk_size=chunk_size):
            yield convert.get_backend_entity(obj, None)

    def __iter__(self):
        """Iterate for list comprehensions.

        Note: used to rely on the iterator in django 1.8 but does no longer in django 1.11.
        """
        from aiida.orm.implementation.django import convert
        return (convert.get_backend_entity(model, None) for model in super().__iter__())

    def __getitem__(self, key):
        """Get item for [] operator

        Note: used to rely on the iterator in django 1.8 but does no longer in django 1.11."""
        from aiida.orm.implementation.django import convert
        res = super().__getitem__(key)
        return convert.get_backend_entity(res, None)


class AiidaObjectManager(m.Manager):

    def get_queryset(self):
        return AiidaQuerySet(self.model, using=self._db)


class DbUser(m.Model):  # pylint: disable=too-few-public-methods
    """Class that represents a user as the owner of a specific Node."""

    is_anonymous = False
    is_authenticated = True

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ()

    # Set unique email field
    email = m.EmailField(unique=True, db_index=True)
    first_name = m.CharField(max_length=254, blank=True)
    last_name = m.CharField(max_length=254, blank=True)
    institution = m.CharField(max_length=254, blank=True)


class DbNode(m.Model):
    """Generic node: data or calculation or code.

    Nodes can be linked (DbLink table)
    Naming convention for Node relationships: A --> C --> B.

    * A is 'input' of C.
    * C is 'output' of A.

    Internal attributes, that define the node itself,
    are stored in the DbAttribute table; further user-defined attributes,
    called 'extra', are stored in the DbExtra table (same schema and methods
    of the DbAttribute table, but the code does not rely on the content of the
    table, therefore the user can use it at his will to tag or annotate nodes.

    :note: Attributes in the DbAttribute table have to be thought as belonging
       to the DbNode, (this is the reason for which there is no 'user' field
       in the DbAttribute field). Moreover, Attributes define uniquely the
       Node so should be immutable."""

    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # in the form data.upffile., data.structure., calculation., ...
    # Note that there is always a final dot, to allow to do queries of the
    # type (node_type__startswith="calculation.") and avoid problems with classes
    # starting with the same string
    # max_length required for index by MySql
    node_type = m.CharField(max_length=255, db_index=True)
    process_type = m.CharField(max_length=255, db_index=True, null=True)
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # creation time
    ctime = m.DateTimeField(default=timezone.now, db_index=True, editable=False)
    mtime = m.DateTimeField(auto_now=True, db_index=True, editable=False)
    # Cannot delete a user if something is associated to it
    user = m.ForeignKey(DbUser, on_delete=m.PROTECT, related_name='dbnodes')

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False, related_name='inputs', through='DbLink')

    # Used only if dbnode is a calculation, or remotedata
    # Avoid that computers can be deleted if at least a node exists pointing
    # to it.
    dbcomputer = m.ForeignKey('DbComputer', null=True, on_delete=m.PROTECT, related_name='dbnodes')

    # JSON Attributes
    attributes = JSONField(default=dict, null=True)
    # JSON Extras
    extras = JSONField(default=dict, null=True)

    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()

    def get_simple_name(self, invalid_result=None):
        """Return a string with the last part of the type name.

        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.

        :param invalid_result: The value to be returned if the node type is
            not recognized."""
        thistype = self.node_type
        # Fix for base class
        if thistype == '':
            thistype = 'node.Node.'
        if not thistype.endswith('.'):
            return invalid_result
        thistype = thistype[:-1]  # Strip final dot
        return thistype.rpartition('.')[2]

    def __str__(self):
        simplename = self.get_simple_name(invalid_result='Unknown')
        # node pk + type
        if self.label:
            return '{} node [{}]: {}'.format(simplename, self.pk, self.label)
        return '{} node [{}]'.format(simplename, self.pk)


class DbLink(m.Model):
    """Direct connection between two dbnodes. The label is identifying thelink type."""

    # If I delete an output, delete also the link; if I delete an input, stop
    # NOTE: this will in most cases render a DbNode.objects.filter(...).delete()
    # call unusable because some nodes will be inputs; Nodes will have to
    #    be deleted in the proper order (or links will need to be deleted first)
    # The `input` and `output` columns do not need an explicit `db_index` as it is `True` by default for foreign keys
    input = m.ForeignKey('DbNode', related_name='output_links', on_delete=m.PROTECT)
    output = m.ForeignKey('DbNode', related_name='input_links', on_delete=m.CASCADE)
    label = m.CharField(max_length=255, db_index=True, blank=False)
    type = m.CharField(max_length=255, db_index=True, blank=True)

    def __str__(self):
        return '{} ({}) --> {} ({})'.format(
            self.input.get_simple_name(invalid_result='Unknown node'),
            self.input.pk,
            self.output.get_simple_name(invalid_result='Unknown node'),
            self.output.pk,
        )


class DbSetting(m.Model):
    """This will store generic settings that should be database-wide."""
    key = m.CharField(max_length=1024, db_index=True, blank=False, unique=True)
    val = JSONField(default=None, null=True)
    # I also add a description field for the variables
    description = m.TextField(blank=True)
    # Modification time of this attribute
    time = m.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "'{}'={}".format(self.key, self.getvalue())

    @classmethod
    def set_value(
        cls, key, value, with_transaction=True, subspecifier_value=None, other_attribs=None, stop_if_existing=False
    ):
        """Delete a setting value."""
        other_attribs = other_attribs if other_attribs is not None else {}
        setting = DbSetting.objects.filter(key=key).first()
        if setting is not None:
            if stop_if_existing:
                return
        else:
            setting = cls()

        setting.key = key
        setting.val = value
        setting.time = timezone.datetime.now(tz=UTC)
        if 'description' in other_attribs.keys():
            setting.description = other_attribs['description']
        setting.save()

    def getvalue(self):
        """This can be called on a given row and will get the corresponding value."""
        return self.val

    def get_description(self):
        """This can be called on a given row and will get the corresponding description."""
        return self.description

    @classmethod
    def del_value(cls, key, only_children=False, subspecifier_value=None):
        """Set a setting value."""

        setting = DbSetting.objects.filter(key=key).first()
        if setting is not None:
            setting.val = None
            setting.time = timezone.datetime.utcnow()
            setting.save()
        else:
            raise KeyError()


class DbGroup(m.Model):
    """
    A group of nodes.

    Any group of nodes can be created, but some groups may have specific meaning
    if they satisfy specific rules (for instance, groups of UpdData objects are
    pseudopotential families - if no two pseudos are included for the same
    atomic element).
    """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # max_length is required by MySql to have indexes and unique constraints
    label = m.CharField(max_length=255, db_index=True)
    # The type_string of group: a user group, a pseudopotential group,...
    # User groups have type_string equal to an empty string
    type_string = m.CharField(default='', max_length=255, db_index=True)
    dbnodes = m.ManyToManyField('DbNode', related_name='dbgroups')
    # Creation time
    time = m.DateTimeField(default=timezone.now, editable=False)
    description = m.TextField(blank=True)
    # The owner of the group, not of the calculations
    # On user deletion, remove his/her groups too (not the calcuations, only
    # the groups
    user = m.ForeignKey(DbUser, on_delete=m.CASCADE, related_name='dbgroups')

    class Meta:  # pylint: disable=too-few-public-methods
        unique_together = (('label', 'type_string'),)

    def __str__(self):
        return '<DbGroup [type_string: {}] "{}">'.format(self.type_string, self.label)


class DbComputer(m.Model):
    """
    Table of computers or clusters.

    Attributes:
    * name: A name to be used to refer to this computer. Must be unique.
    * hostname: Fully-qualified hostname of the host
    * transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:

        * mpirun command

        * num cores per node

        * max num cores

        * workdir: Full path of the aiida folder on the host. It can contain\
            the string {username} that will be substituted by the username\
            of the user on that machine.\
            The actual workdir is then obtained as\
            workdir.format(username=THE_ACTUAL_USERNAME)\
            Example: \
            workdir = "/scratch/{username}/aiida/"


        * allocate full node = True or False

        * ... (further limits per user etc.)

    """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    name = m.CharField(max_length=255, unique=True, blank=False)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    # TODO: next three fields should not be blank...
    scheduler_type = m.CharField(max_length=255)
    transport_type = m.CharField(max_length=255)
    metadata = JSONField(default=dict)

    def __str__(self):
        return '{} ({})'.format(self.name, self.hostname)


class DbAuthInfo(m.Model):
    """
    Table that pairs aiida users and computers, with all required authentication
    information.
    """
    # Delete the DbAuthInfo if either the user or the computer are removed
    aiidauser = m.ForeignKey(DbUser, on_delete=m.CASCADE)
    dbcomputer = m.ForeignKey(DbComputer, on_delete=m.CASCADE)
    auth_params = JSONField(default=dict)  # contains mainly the remoteuser and the private_key

    # The keys defined in the metadata of the DbAuthInfo will override the
    # keys with the same name defined in the DbComputer (using a dict.update()
    # call of python).
    metadata = JSONField(default=dict)
    # Whether this computer is enabled (user-level enabling feature)
    enabled = m.BooleanField(default=True)

    class Meta:  # pylint: disable=too-few-public-methods
        unique_together = (('aiidauser', 'dbcomputer'),)

    def __str__(self):
        if self.enabled:
            return 'DB authorization info for {} on {}'.format(self.aiidauser.email, self.dbcomputer.name)
        return 'DB authorization info for {} on {} [DISABLED]'.format(self.aiidauser.email, self.dbcomputer.name)


class DbComment(m.Model):
    """Class to store comments. """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # Delete comments if the node is removed
    dbnode = m.ForeignKey(DbNode, related_name='dbcomments', on_delete=m.CASCADE)
    ctime = m.DateTimeField(default=timezone.now, editable=False)
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Delete the comments of a deleted user (TODO: check if this is a good policy)
    user = m.ForeignKey(DbUser, on_delete=m.CASCADE)
    content = m.TextField(blank=True)

    def __str__(self):
        return 'DbComment for [{} {}] on {}'.format(
            self.dbnode.get_simple_name(), self.dbnode.pk,
            timezone.localtime(self.ctime).strftime('%Y-%m-%d')
        )


class DbLog(m.Model):
    """Class to store logs."""
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    time = m.DateTimeField(default=timezone.now, editable=False)
    loggername = m.CharField(max_length=255, db_index=True)
    levelname = m.CharField(max_length=50, db_index=True)
    dbnode = m.ForeignKey(DbNode, related_name='dblogs', on_delete=m.CASCADE)
    message = m.TextField(blank=True)
    metadata = JSONField(default=dict)

    def __str__(self):
        return 'DbLog: {} for node {}: {}'.format(self.levelname, self.dbnode.id, self.message)


@contextlib.contextmanager
def suppress_auto_now(list_of_models_fields):
    """
    This context manager disables the auto_now & editable flags for the
    fields of the given models.
    This is useful when we would like to update the datetime fields of an
    entry bypassing the automatic set of the date (with the current time).
    This is very useful when entries are imported and we would like to keep e.g.
    the modification time that we set during the import and not allow Django
    to set it to the datetime that corresponds to when the entry was saved.
    In the end the flags are returned to their original value.
    :param list_of_models_fields: A list of (model, fields) tuples for
    which the flags will be updated. The model is an object that corresponds
    to the model objects and fields is a list of strings with the field names.
    """
    # Here we store the original values of the fields of the models that will
    # be updated
    # E.g.
    # _original_model_values = {
    #   ModelA: [fieldA: {
    #                       'auto_now': orig_valA1
    #                       'editable': orig_valA2
    #            },
    #            fieldB: {
    #                       'auto_now': orig_valB1
    #                       'editable': orig_valB2
    #            }
    #    ]
    #   ...
    # }
    _original_model_values = dict()
    for model, fields in list_of_models_fields:
        _original_field_values = dict()
        for field in model._meta.local_fields:  # pylint: disable=protected-access
            if field.name in fields:
                _original_field_values[field] = {
                    'auto_now': field.auto_now,
                    'editable': field.editable,
                }
                field.auto_now = False
                field.editable = True
        _original_model_values[model] = _original_field_values
    try:
        yield
    finally:
        for model in _original_model_values:
            for field in _original_model_values[model]:
                field.auto_now = _original_model_values[model][field]['auto_now']
                field.editable = _original_model_values[model][field]['editable']
