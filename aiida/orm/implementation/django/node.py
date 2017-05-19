# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import copy

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import F

from aiida.backends.djsite.db.models import DbLink
from aiida.backends.djsite.utils import get_automatic_user
from aiida.common.exceptions import (InternalError, ModificationNotAllowed,
                                     NotExistent, UniquenessError)
from aiida.common.folders import RepositoryFolder
from aiida.common.links import LinkType
from aiida.common.utils import get_new_uuid
from aiida.orm.implementation.general.node import AbstractNode, _NO_DEFAULT
from aiida.orm.mixins import Sealable
from aiida.orm.implementation.django.utils import get_db_columns



class Node(AbstractNode):
    @classmethod
    def get_subclass_from_uuid(cls, uuid):
        from aiida.backends.djsite.db.models import DbNode
        try:
            node = DbNode.objects.get(uuid=uuid).get_aiida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with UUID={} found".format(uuid))
        if not isinstance(node, cls):
            raise NotExistent("UUID={} is not an instance of {}".format(
                uuid, cls.__name__))
        return node

    @staticmethod
    def get_db_columns():
        from aiida.backends.djsite.db.models import DbNode
        return get_db_columns(DbNode)

    @classmethod
    def get_subclass_from_pk(cls, pk):
        from aiida.backends.djsite.db.models import DbNode
        try:
            node = DbNode.objects.get(pk=pk).get_aiida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with pk= {} found".format(pk))
        if not isinstance(node, cls):
            raise NotExistent("pk= {} is not an instance of {}".format(
                pk, cls.__name__))
        return node

    def __init__(self, **kwargs):
        from aiida.backends.djsite.db.models import DbNode
        super(Node, self).__init__()

        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            if not isinstance(dbnode, DbNode):
                raise TypeError("dbnode is not a DbNode instance")
            if dbnode.pk is None:
                raise ValueError("If cannot load an aiida.orm.Node instance "
                                 "from an unsaved Django DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any "
                                 "further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name,
                                                 uuid=self._dbnode.uuid)

        # NO VALIDATION ON __init__ BY DEFAULT, IT IS TOO SLOW SINCE IT OFTEN
        # REQUIRES MULTIPLE DB HITS
        # try:
        #                # Note: the validation often requires to load at least one
        #                # attribute, and therefore it will take a lot of time
        #                # because it has to cache every attribute.
        #                self._validate()
        #            except ValidationError as e:
        #                raise DbContentError("The data in the DB with UUID={} is not "
        #                                     "valid for class {}: {}".format(
        #                    uuid, self.__class__.__name__, e.message))
        else:
            # TODO: allow to get the user from the parameters
            user = get_automatic_user()
            self._dbnode = DbNode(user=user,
                                  uuid=get_new_uuid(),
                                  type=self._plugin_type_string)

            self._to_be_stored = True

            # As creating the temp folder may require some time on slow
            # filesystems, we defer its creation
            self._temp_folder = None
            # Used only before the first save
            self._attrs_cache = {}
            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name,
                                                 uuid=self.uuid)

            # Automatically set all *other* attributes, if possible, otherwise
            # stop
            self._set_with_defaults(**kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        from aiida.backends.djsite.db.models import DbNode
        if cls._plugin_type_string:
            if not cls._plugin_type_string.endswith('.'):
                raise InternalError("The plugin type string does not "
                                    "finish with a dot??")

            # If it is 'calculation.Calculation.', we want to filter
            # for things that start with 'calculation.' and so on
            plug_type = cls._plugin_type_string

            # Remove the implementation.django or sqla part.
            if plug_type.startswith('implementation.'):
                plug_type = '.'.join(plug_type.split('.')[2:])
            pre, sep, _ = plug_type[:-1].rpartition('.')
            superclass_string = "".join([pre, sep])
            return DbNode.aiidaobjects.filter(
                *args, type__startswith=superclass_string, **kwargs)
        else:
            # Base Node class, with empty string
            return DbNode.aiidaobjects.filter(*args, **kwargs)

    def _update_db_label_field(self, field_value):
        self.dbnode.label = field_value
        if not self._to_be_stored:
            with transaction.atomic():
                self._dbnode.save()
                self._increment_version_number_db()

    def _update_db_description_field(self, field_value):
        self.dbnode.description = field_value
        if not self._to_be_stored:
            with transaction.atomic():
                self._dbnode.save()
                self._increment_version_number_db()

    def _replace_dblink_from(self, src, label, link_type):
        try:
            self._add_dblink_from(src, label, link_type)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            with transaction.atomic():
                self._remove_dblink_from(label)
                self._add_dblink_from(src, label, link_type)

    def _remove_dblink_from(self, label):
        DbLink.objects.filter(output=self.dbnode, label=label).delete()

    def _add_dblink_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        from aiida.backends.djsite.db.models import DbPath
        if not isinstance(src, Node):
            raise ValueError("src must be a Node instance")
        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot call the internal _add_dblink_from if the "
                "destination node is not stored")
        if src._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot call the internal _add_dblink_from if the "
                "source node is not stored")

        if link_type is LinkType.CREATE or link_type is LinkType.INPUT:
            # Check for cycles. This works if the transitive closure is enabled; if it
            # isn't, this test will never fail, but then having a circular link is not
            # meaningful but does not pose a huge threat
            #
            # I am linking src->self; a loop would be created if a DbPath exists already
            # in the TC table from self to src
            if len(DbPath.objects.filter(parent=self.dbnode, child=src.dbnode)) > 0:
                raise ValueError(
                    "The link you are attempting to create would generate a loop")

        if label is None:
            autolabel_idx = 1

            existing_from_autolabels = list(DbLink.objects.filter(
                output=self.dbnode,
                label__startswith="link_").values_list('label', flat=True))
            while "link_{}".format(autolabel_idx) in existing_from_autolabels:
                autolabel_idx += 1

            safety_counter = 0
            while True:
                safety_counter += 1
                if safety_counter > 100:
                    # Well, if you have more than 100 concurrent addings
                    # to the same node, you are clearly doing something wrong...
                    raise InternalError("Hey! We found more than 100 concurrent"
                                        " adds of links "
                                        "to the same nodes! Are you really doing that??")
                try:
                    self._do_create_link(src, "link_{}".format(autolabel_idx), link_type)
                    break
                except UniquenessError:
                    # Retry loop until you find a new loop
                    autolabel_idx += 1
        else:
            self._do_create_link(src, label, link_type)

    def _do_create_link(self, src, label, link_type):
        sid = None
        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            sid = transaction.savepoint()
            DbLink.objects.create(input=src.dbnode, output=self.dbnode,
                                  label=label, type=link_type.value)
            transaction.savepoint_commit(sid)
        except IntegrityError as e:
            transaction.savepoint_rollback(sid)
            raise UniquenessError("There is already a link with the same "
                                  "name (raw message was {})"
                                  "".format(e.message))

    def _get_db_input_links(self, link_type):
        from aiida.backends.djsite.db.models import DbLink

        link_filter = {'output': self.dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return [(i.label, i.input.get_aiida_class()) for i in
                DbLink.objects.filter(**link_filter).distinct()]


    def _get_db_output_links(self, link_type):
        from aiida.backends.djsite.db.models import DbLink

        link_filter = {'input': self.dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return ((i.label, i.output.get_aiida_class()) for i in
                DbLink.objects.filter(**link_filter).distinct())

    def _set_db_computer(self, computer):
        from aiida.backends.djsite.db.models import DbComputer
        self.dbnode.dbcomputer = DbComputer.get_dbcomputer(computer)

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        DO NOT USE DIRECTLY.

        :param str key: key name
        :param value: its value
        """
        from aiida.backends.djsite.db.models import DbAttribute

        DbAttribute.set_value_for_node(self.dbnode, key, value)
        self._increment_version_number_db()

    def _del_db_attr(self, key):
        from aiida.backends.djsite.db.models import DbAttribute
        if not DbAttribute.has_key(self.dbnode, key):
            raise AttributeError("DbAttribute {} does not exist".format(
                key))
        DbAttribute.del_value_for_node(self.dbnode, key)
        self._increment_version_number_db()

    def _get_db_attr(self, key):
        from aiida.backends.djsite.db.models import DbAttribute
        return DbAttribute.get_value_for_node(
            dbnode=self.dbnode, key=key)

    def _set_db_extra(self, key, value, exclusive=False):
        from aiida.backends.djsite.db.models import DbExtra

        DbExtra.set_value_for_node(self.dbnode, key, value,
                                   stop_if_existing=exclusive)
        self._increment_version_number_db()

    def _reset_db_extras(self, new_extras):
        raise NotImplementedError("Reset of extras has not been implemented"
                                  "for Django backend.")

    def _get_db_extra(self, key, *args):
        from aiida.backends.djsite.db.models import DbExtra
        return DbExtra.get_value_for_node(dbnode=self.dbnode,
                                          key=key)

    def _del_db_extra(self, key):
        from aiida.backends.djsite.db.models import DbExtra
        if not DbExtra.has_key(self.dbnode, key):
            raise AttributeError("DbExtra {} does not exist".format(
                key))
        return DbExtra.del_value_for_node(self.dbnode, key)
        self._increment_version_number_db()

    def _db_iterextras(self):
        from aiida.backends.djsite.db.models import DbExtra
        extraslist = DbExtra.list_all_node_elements(self.dbnode)
        for e in extraslist:
            yield (e.key, e.getvalue())

    def _db_iterattrs(self):
        from aiida.backends.djsite.db.models import DbAttribute

        all_attrs = DbAttribute.get_all_values_for_node(self.dbnode)
        for attr in all_attrs:
            yield (attr, all_attrs[attr])

    def _db_attrs(self):
        # Note: I "duplicate" the code from iterattrs and reimplement it
        # here, rather than
        # calling iterattrs from here, because iterattrs is slow on each call
        # since it has to call .getvalue(). To improve!
        from aiida.backends.djsite.db.models import DbAttribute
        attrlist = DbAttribute.list_all_node_elements(self.dbnode)
        for attr in attrlist:
            yield attr.key

    def add_comment(self, content, user=None):
        from aiida.backends.djsite.db.models import DbComment
        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after "
                                         "storing the node")

        DbComment.objects.create(dbnode=self._dbnode,
                                 user=user,
                                 content=content)

    def get_comment_obj(self, id=None, user=None):
        from aiida.backends.djsite.db.models import DbComment
        import operator
        from django.db.models import Q
        query_list = []

        # If an id is specified then we add it to the query
        if id is not None:
            query_list.append(Q(pk=id))

        # If a user is specified then we add it to the query
        if user is not None:
            query_list.append(Q(user=user))

        dbcomments = DbComment.objects.filter(
            reduce(operator.and_, query_list))
        comments = []
        from aiida.orm.implementation.django.comment import Comment
        for dbcomment in dbcomments:
            comments.append(Comment(dbcomment=dbcomment))
        return comments

    def get_comments(self, pk=None):
        from aiida.backends.djsite.db.models import DbComment
        if pk is not None:
            try:
                correct = all([isinstance(_, int) for _ in pk])
                if not correct:
                    raise ValueError('pk must be an integer or a list of integers')
            except TypeError:
                if not isinstance(pk, int):
                    raise ValueError('pk must be an integer or a list of integers')
            return list(DbComment.objects.filter(
                dbnode=self._dbnode, pk=pk).order_by('pk').values(
                'pk', 'user__email', 'ctime', 'mtime', 'content'))

        return list(DbComment.objects.filter(dbnode=self._dbnode).order_by(
            'pk').values('pk', 'user__email', 'ctime', 'mtime', 'content'))

    def _get_dbcomments(self, pk=None):
        from aiida.backends.djsite.db.models import DbComment
        if pk is not None:
            try:
                correct = all([isinstance(_, int) for _ in pk])
                if not correct:
                    raise ValueError('pk must be an integer or a list of integers')
                return list(DbComment.objects.filter(dbnode=self._dbnode, pk__in=pk).order_by('pk'))
            except TypeError:
                if not isinstance(pk, int):
                    raise ValueError('pk must be an integer or a list of integers')
                return list(DbComment.objects.filter(dbnode=self._dbnode, pk=pk).order_by('pk'))

        return list(DbComment.objects.filter(dbnode=self._dbnode).order_by('pk'))

    def _update_comment(self, new_field, comment_pk, user):
        from aiida.backends.djsite.db.models import DbComment
        comment = list(DbComment.objects.filter(dbnode=self._dbnode,
                                                pk=comment_pk, user=user))[0]

        if not isinstance(new_field, basestring):
            raise ValueError("Non string comments are not accepted")

        if not comment:
            raise NotExistent("Found no comment for user {} and pk {}".format(
                user, comment_pk))

        comment.content = new_field
        comment.save()

    def _remove_comment(self, comment_pk, user):
        from aiida.backends.djsite.db.models import DbComment
        comment = DbComment.objects.filter(dbnode=self._dbnode, pk=comment_pk)[0]
        comment.delete()

    def _increment_version_number_db(self):
        from aiida.backends.djsite.db.models import DbNode
        # I increment the node number using a filter
        self._dbnode.nodeversion = F('nodeversion') + 1
        self._dbnode.save()

        # This reload internally the node of self._dbnode
        # Note: I have to reload the object (to have the right values in memory,
        # otherwise I only get the Django Field F object as a result!
        self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)

    def copy(self):
        newobject = self.__class__()
        newobject.dbnode.type = self.dbnode.type  # Inherit type
        newobject.dbnode.label = self.dbnode.label  # Inherit label
        # TODO: add to the description the fact that this was a copy?
        newobject.dbnode.description = self.dbnode.description  # Inherit description
        newobject.dbnode.dbcomputer = self.dbnode.dbcomputer  # Inherit computer

        for k, v in self.iterattrs():
            if k != Sealable.SEALED_KEY:
                newobject._set_attr(k, v)

        for path in self.get_folder_list():
            newobject.add_path(self.get_abs_path(path), path)

        return newobject

    @property
    def uuid(self):
        return unicode(self.dbnode.uuid)

    @property
    def id(self):
        return self.dbnode.id

    @property
    def dbnode(self):
        # I also update the internal _dbnode variable, if it was saved
        # from aiida.backends.djsite.db.models import DbNode
        #        if not self._to_be_stored:
        #            self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
        return self._dbnode

    def store_all(self, with_transaction=True):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager

        if with_transaction:
            context_man = transaction.atomic()
        else:
            context_man = EmptyContextManager()

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} was already stored".format(self.pk))

        # For each parent, check that all its inputs are stored
        for label in self._inputlinks_cache:
            try:
                parent_node = self._inputlinks_cache[label][0]
                parent_node._check_are_parents_stored()
            except ModificationNotAllowed:
                raise ModificationNotAllowed(
                    "Parent node (UUID={}) has "
                    "unstored parents, cannot proceed (only direct parents "
                    "can be unstored and will be stored by store_all, not "
                    "grandparents or other ancestors".format(parent_node.uuid))

        with context_man:
            # Always without transaction: either it is the context_man here,
            # or it is managed outside
            self._store_input_nodes()
            self.store(with_transaction=False)
            self._store_cached_input_links(with_transaction=False)

        return self


    def _store_cached_input_links(self, with_transaction=True):
        """
        Store all input links that are in the local cache, transferring them
        to the DB.

        :note: This can be called only if all parents are already stored.

        :note: Links are stored only after the input nodes are stored. Moreover,
            link storage is done in a transaction, and if one of the links
            cannot be stored, an exception is raised and *all* links will remain
            in the cache.

        :note: This function can be called only after the node is stored.
           After that, it can be called multiple times, and nothing will be
           executed if no links are still in the cache.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager

        if with_transaction:
            context_man = transaction.atomic()
        else:
            context_man = EmptyContextManager()

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} is not stored yet".format(self.pk))

        with context_man:
            # This raises if there is an unstored node.
            self._check_are_parents_stored()
            # I have to store only those links where the source is already
            # stored
            links_to_store = list(self._inputlinks_cache.keys())

            for label in links_to_store:
                src, link_type = self._inputlinks_cache[label]
                self._add_dblink_from(src, label, link_type)
            # If everything went smoothly, clear the entries from the cache.
            # I do it here because I delete them all at once if no error
            # occurred; otherwise, links will not be stored and I
            # should not delete them from the cache (but then an exception
            # would have been raised, and the following lines are not executed)
            self._inputlinks_cache.clear()

    def store(self, with_transaction=True):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        # TODO: This needs to be generalized, allowing for flexible methods
        # for storing data and its attributes.
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager
        from aiida.common.exceptions import ValidationError
        from aiida.backends.djsite.db.models import DbAttribute
        import aiida.orm.autogroup

        if with_transaction:
            context_man = transaction.atomic()
        else:
            context_man = EmptyContextManager()

        if self._to_be_stored:

            # As a first thing, I check if the data is valid
            self._validate()

            # Verify that parents are already stored. Raises if this is not
            # the case.
            self._check_are_parents_stored()

            # I save the corresponding django entry
            # I set the folder
            # NOTE: I first store the files, then only if this is successful,
            # I store the DB entry. In this way,
            # I assume that if a node exists in the DB, its folder is in place.
            # On the other hand, periodically the user might need to run some
            # bookkeeping utility to check for lone folders.
            self._repository_folder.replace_with_folder(
                self._get_temp_folder().abspath, move=True, overwrite=True)

            # I do the transaction only during storage on DB to avoid timeout
            # problems, especially with SQLite
            try:
                with context_man:
                    # Save the row
                    self._dbnode.save()
                    # Save its attributes 'manually' without incrementing
                    # the version for each add.
                    DbAttribute.reset_values_for_node(self.dbnode,
                                                      attributes=self._attrs_cache,
                                                      with_transaction=False)
                    # This should not be used anymore: I delete it to
                    # possibly free memory
                    del self._attrs_cache

                    self._temp_folder = None
                    self._to_be_stored = False

                    # Here, I store those links that were in the cache and
                    # that are between stored nodes.
                    self._store_cached_input_links()

            # This is one of the few cases where it is ok to do a 'global'
            # except, also because I am re-raising the exception
            except:
                # I put back the files in the sandbox folder since the
                # transaction did not succeed
                self._get_temp_folder().replace_with_folder(
                    self._repository_folder.abspath, move=True, overwrite=True)
                raise

            # Set up autogrouping used be verdi run
            autogroup = aiida.orm.autogroup.current_autogroup
            grouptype = aiida.orm.autogroup.VERDIAUTOGROUP_TYPE
            if autogroup is not None:
                if not isinstance(autogroup, aiida.orm.autogroup.Autogroup):
                    raise ValidationError("current_autogroup is not an AiiDA Autogroup")
                if autogroup.is_to_be_grouped(self):
                    group_name = autogroup.get_group_name()
                    if group_name is not None:
                        from aiida.orm import Group

                        g = Group.get_or_create(name=group_name, type_string=grouptype)[0]
                        g.add_nodes(self)

        # This is useful because in this way I can do
        # n = Node().store()
        return self

    @property
    def has_children(self):
        from aiida.backends.djsite.db.models import DbPath
        childrens = DbPath.objects.filter(parent=self.pk)
        return False if not childrens else True

    @property
    def has_parents(self):
        from aiida.backends.djsite.db.models import DbPath
        parents = DbPath.objects.filter(child=self.pk)
        return False if not parents else True
