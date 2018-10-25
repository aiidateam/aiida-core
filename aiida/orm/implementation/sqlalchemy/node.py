# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
SQL Alchemy Node concrete implementation
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from aiida.backends.sqlalchemy.models.node import DbNode, DbLink
from aiida.backends.sqlalchemy.models.comment import DbComment
from aiida.backends.sqlalchemy.models.computer import DbComputer

from aiida.common.utils import get_new_uuid
from aiida.common.folders import RepositoryFolder
from aiida.common.exceptions import (InternalError, ModificationNotAllowed, NotExistent, UniquenessError)
from aiida.common.links import LinkType
from aiida.common.utils import type_check
from aiida.orm.implementation.general.node import AbstractNode, _HASH_EXTRA_KEY
from aiida.orm.implementation.sqlalchemy.utils import get_attr
from aiida import orm

from . import computer as computers
from . import user as users


class Node(AbstractNode):
    """
    Concrete SQLAlchemy Node implementation
    """
    _plugin_type_string = None

    def __init__(self, **kwargs):
        super(Node, self).__init__()

        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            type_check(dbnode, DbNode)
            if dbnode.id is None:
                raise ValueError("If cannot load an aiida.orm.Node instance " "from an unsaved DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any " "further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

        else:
            user = self._backend.users.get_automatic_user()
            if user is None:
                raise RuntimeError("Could not find a default user")

            self._dbnode = DbNode(user=user.dbuser, uuid=get_new_uuid(), type=self._plugin_type_string)

            self._to_be_stored = True

            # As creating the temp folder may require some time on slow
            # filesystems, we defer its creation
            self._temp_folder = None
            # Used only before the first save
            self._attrs_cache = {}
            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

            # Automatically set all *other* attributes, if possible, otherwise
            # stop
            self._set_with_defaults(**kwargs)

    @classmethod
    def get_subclass_from_uuid(cls, uuid):
        from aiida.orm.querybuilder import QueryBuilder
        from sqlalchemy.exc import DatabaseError
        try:
            query = QueryBuilder()
            query.append(cls, filters={'uuid': {'==': str(uuid)}})

            if query.count() == 0:
                raise NotExistent("No entry with UUID={} found".format(uuid))

            node = query.first()[0]

            if not isinstance(node, cls):
                raise NotExistent("UUID={} is not an instance of {}".format(uuid, cls.__name__))
            return node
        except DatabaseError as exc:
            raise ValueError(str(exc))

    @classmethod
    def get_subclass_from_pk(cls, pk):
        from aiida.orm.querybuilder import QueryBuilder
        from sqlalchemy.exc import DatabaseError
        # If it is not an int make a final attempt
        # to convert to an integer. If you fail,
        # raise an exception.
        try:
            pk = int(pk)
        except:
            raise ValueError("Incorrect type for int")

        try:
            query = QueryBuilder()
            query.append(cls, filters={'id': {'==': pk}})

            if query.count() == 0:
                raise NotExistent("No entry with pk= {} found".format(pk))

            node = query.first()[0]

            if not isinstance(node, cls):
                raise NotExistent("pk= {} is not an instance of {}".format(pk, cls.__name__))
            return node
        except DatabaseError as exc:
            raise ValueError(str(exc))

    def __int__(self):
        if self._to_be_stored:
            return None

        return self._dbnode.id

    @classmethod
    def query(cls, *args, **kwargs):
        raise NotImplementedError("The node query method is not supported in " "SQLAlchemy. Please use QueryBuilder.")

    @property
    def type(self):
        # Type is immutable so no need to ensure the model is up to date
        return self._dbnode.type

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['ctime'])
        return self._dbnode.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['mtime'])
        return self._dbnode.mtime

    def get_user(self):
        """
        Get the user.

        :return: an aiida user model object
        """
        self._ensure_model_uptodate(attribute_names=['user'])
        return self._backend.users.from_dbmodel(self._dbnode.user)

    def set_user(self, user):
        type_check(user, users.SqlaUser)
        self._dbnode.user = user.dbuser

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        self._ensure_model_uptodate(attribute_names=['dbcomputer'])
        if self._dbnode.dbcomputer is None:
            return None

        return orm.Computer.from_bakend_entity(
            self.backend.computers.from_dbmodel(self._dbnode.dbcomputer))

    def _get_db_label_field(self):
        """
        Get the label of the node.

        :return: a string.
        """
        self._ensure_model_uptodate(attribute_names=['label'])
        return self._dbnode.label

    def _update_db_label_field(self, field_value):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        self._dbnode.label = field_value
        if self.is_stored:
            session.add(self._dbnode)
            self._increment_version_number_db()

    def _get_db_description_field(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        self._ensure_model_uptodate(attribute_names=['description'])
        return self._dbnode.description

    def _update_db_description_field(self, field_value):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        self._dbnode.description = field_value
        if self.is_stored:
            session.add(self._dbnode)
            self._increment_version_number_db()

    def _replace_dblink_from(self, src, label, link_type):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        try:
            self._add_dblink_from(src, label)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            try:
                self._remove_dblink_from(label)
                self._add_dblink_from(src, label, link_type)
                session.commit()
            except:
                session.rollback()
                raise

    def _remove_dblink_from(self, label):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        link = DbLink.query.filter_by(label=label).first()
        if link is not None:
            session.delete(link)

    def _add_dblink_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        from aiida.backends.sqlalchemy import get_scoped_session
        from aiida.orm.querybuilder import QueryBuilder
        session = get_scoped_session()
        type_check(src, Node)
        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        if not self.is_stored:
            raise ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                         "destination node is not stored")
        if not src.is_stored:
            raise ModificationNotAllowed("Cannot call the internal _add_dblink_from if the "
                                         "source node is not stored")

        # Check for cycles. This works if the transitive closure is enabled; if
        # it isn't, this test will never fail, but then having a circular link
        # is not meaningful but does not pose a huge threat
        #
        # I am linking src->self; a loop would be created if a DbPath exists
        # already in the TC table from self to src
        if link_type is LinkType.CREATE or link_type is LinkType.INPUT:
            if QueryBuilder().append(
                    Node, filters={
                        'id': self.pk
                    }, tag='parent').append(
                Node, filters={
                    'id': src.pk
                }, tag='child', descendant_of='parent').count() > 0:
                raise ValueError("The link you are attempting to create would generate a loop")

        if label is None:
            autolabel_idx = 1

            existing_from_autolabels = session.query(DbLink.label).filter(DbLink.output_id == self._dbnode.id,
                                                                          DbLink.label.like("link%"))

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
        """
        Create a link from a source node with label and a link type

        :param src: The source node
        :type src: :class:`~aiida.orm.implementation.sqlalchemy.node.Node`
        :param label: The link label
        :param link_type: The link type
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        try:
            with session.begin_nested():
                link = DbLink(input_id=src.id, output_id=self.id, label=label, type=link_type.value)
                session.add(link)
        except SQLAlchemyError as exc:
            raise UniquenessError("There is already a link with the same " "name (raw message was {})" "".format(exc))

    def _get_db_input_links(self, link_type):
        link_filter = {'output': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return [(i.label, i.input.get_aiida_class()) for i in DbLink.query.filter_by(**link_filter).distinct().all()]

    def _get_db_output_links(self, link_type):
        link_filter = {'input': self._dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        return ((i.label, i.output.get_aiida_class()) for i in DbLink.query.filter_by(**link_filter).distinct().all())

    def _set_db_computer(self, computer):
        type_check(computer, computers.SqlaComputer)
        self._dbnode.dbcomputer = computer.dbcomputer

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        DO NOT USE DIRECTLY.

        :param str key: key name
        :param value: its value
        """
        try:
            self._dbnode.set_attr(key, value)
            self._increment_version_number_db()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _del_db_attr(self, key):
        try:
            self._dbnode.del_attr(key)
            self._increment_version_number_db()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_attr(self, key):
        try:
            return get_attr(self._attributes(), key)
        except (KeyError, IndexError):
            raise AttributeError("Attribute '{}' does not exist".format(key))

    def _set_db_extra(self, key, value, exclusive=False):
        if exclusive:
            raise NotImplementedError("exclusive=True not implemented yet in SQLAlchemy backend")

        try:
            self._dbnode.set_extra(key, value)
            self._increment_version_number_db()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _reset_db_extras(self, new_extras):
        try:
            self._dbnode.reset_extras(new_extras)
            self._increment_version_number_db()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_extra(self, key):
        try:
            return get_attr(self._extras(), key)
        except (KeyError, AttributeError):
            raise AttributeError("DbExtra {} does not exist".format(key))

    def _del_db_extra(self, key):
        try:
            self._dbnode.del_extra(key)
            self._increment_version_number_db()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _db_iterextras(self):
        extras = self._extras()
        if extras is None:
            return iter(dict().items())

        return iter(extras.items())

    def _db_iterattrs(self):
        for key, val in self._attributes().items():
            yield (key, val)

    def _db_attrs(self):
        for key in self._attributes().keys():
            yield key

    def add_comment(self, content, user=None):
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after " "storing the node")

        if user is None:
            user = self.backend.users.get_automatic_user()

        comment = DbComment(dbnode=self._dbnode, user=user.dbuser, content=content)
        session.add(comment)
        try:
            session.commit()
        except:
            session = get_scoped_session()
            session.rollback()
            raise

        return comment.id

    def get_comment_obj(self, comment_id=None, user=None):
        """
        Get comment models objects for this node, optionally for a given comment
        id or user.

        :param comment_id: Filter for a particular comment id
        :param user: Filter for a particular user
        :return: A list of comment model instances
        """
        query = DbComment.query.filter_by(dbnode=self._dbnode)

        if comment_id is not None:
            query = query.filter_by(id=comment_id)
        if user is not None:
            query = query.filter_by(user=user.dbuser)

        dbcomments = query.all()
        comments = []
        from aiida.orm.implementation.sqlalchemy.comment import Comment
        for dbcomment in dbcomments:
            comments.append(Comment(dbcomment=dbcomment))
        return comments

    def get_comments(self, pk=None):
        comments = self._get_dbcomments(pk)

        return [{
            "pk": c.id,
            "user__email": c.user.email,
            "ctime": c.ctime,
            "mtime": c.mtime,
            "content": c.content
        } for c in comments]

    def _get_dbcomments(self, pk=None):
        comments = DbComment.query.filter_by(dbnode=self._dbnode)

        if pk is not None:
            try:
                correct = all([isinstance(_, int) for _ in pk])
                if not correct:
                    raise ValueError('id must be an integer or a list of integers')
                comments = comments.filter(DbComment.id.in_(pk))
            except TypeError:
                if not isinstance(pk, int):
                    raise ValueError('id must be an integer or a list of integers')

                comments = comments.filter_by(id=pk)

        comments = comments.order_by('id').all()
        return comments

    def _update_comment(self, new_field, comment_pk, user):
        comment = DbComment.query.filter_by(dbnode=self._dbnode, id=comment_pk, user=user.dbuser).first()

        if not isinstance(new_field, six.string_types):
            raise ValueError("Non string comments are not accepted")

        if not comment:
            raise NotExistent("Found no comment for user {} and id {}".format(user, comment_pk))

        comment.content = new_field
        try:
            comment.save()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _remove_comment(self, comment_pk, user):
        comment = DbComment.query.filter_by(dbnode=self._dbnode, id=comment_pk, user=user.dbuser).first()
        if comment:
            try:
                comment.delete()
            except:
                from aiida.backends.sqlalchemy import get_scoped_session
                session = get_scoped_session()
                session.rollback()
                raise

    def _increment_version_number_db(self):
        self._dbnode.nodeversion = self.nodeversion + 1
        try:
            self._dbnode.save()
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    @property
    def pk(self):
        return self._dbnode.id

    @property
    def id(self):
        return self._dbnode.id

    @property
    def process_type(self):
        return self._dbnode.process_type

    @property
    def dbnode(self):
        self._ensure_model_uptodate()
        return self._dbnode

    @property
    def nodeversion(self):
        self._ensure_model_uptodate(attribute_names=['nodeversion'])
        return self._dbnode.nodeversion

    @property
    def public(self):
        self._ensure_model_uptodate(attribute_names=['public'])
        return self._dbnode.public

    def _db_store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        self._store_input_nodes()
        self.store(with_transaction=False, use_cache=use_cache)
        self._store_cached_input_links(with_transaction=False)
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        if with_transaction:
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise

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

        if not self.is_stored:
            raise ModificationNotAllowed("Node with pk= {} is not stored yet".format(self.id))

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

        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        if with_transaction:
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise

    def _db_store(self, with_transaction=True):
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

        :param bool use_cache: Whether I attempt to find an equal node in the DB.
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        # I save the corresponding django entry
        # I set the folder
        # NOTE: I first store the files, then only if this is successful,
        # I store the DB entry. In this way,
        # I assume that if a node exists in the DB, its folder is in place.
        # On the other hand, periodically the user might need to run some
        # bookkeeping utility to check for lone folders.
        self._repository_folder.replace_with_folder(self._get_temp_folder().abspath, move=True, overwrite=True)

        try:
            session.add(self._dbnode)
            # Save its attributes 'manually' without incrementing
            # the version for each add.
            self._dbnode.attributes = self._attrs_cache
            flag_modified(self._dbnode, "attributes")
            # This should not be used anymore: I delete it to
            # possibly free memory
            del self._attrs_cache

            self._temp_folder = None
            self._to_be_stored = False

            # Here, I store those links that were in the cache and
            # that are between stored nodes.
            self._store_cached_input_links(with_transaction=False)

            if with_transaction:
                try:
                    # aiida.backends.sqlalchemy.get_scoped_session().commit()
                    session.commit()
                except SQLAlchemyError:
                    # print "Cannot store the node. Original exception: {" \
                    #      "}".format(e)
                    session.rollback()
                    raise

        # This is one of the few cases where it is ok to do a 'global'
        # except, also because I am re-raising the exception
        except:
            # I put back the files in the sandbox folder since the
            # transaction did not succeed
            self._get_temp_folder().replace_with_folder(self._repository_folder.abspath, move=True, overwrite=True)
            raise

        self._dbnode.set_extra(_HASH_EXTRA_KEY, self.get_hash())
        return self

    @property
    def uuid(self):
        return six.text_type(self._dbnode.uuid)

    def _attributes(self):
        self._ensure_model_uptodate(['attributes'])
        return self._dbnode.attributes

    def _extras(self):
        self._ensure_model_uptodate(['extras'])
        return self._dbnode.extras

    def _ensure_model_uptodate(self, attribute_names=None):
        if self.is_stored:
            self._dbnode.session.expire(self._dbnode, attribute_names=attribute_names)
