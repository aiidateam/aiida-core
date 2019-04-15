# -*- coding: utf-8 -*-
from __future__ import absolute_import

import copy

from sqlalchemy import literal
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.attributes import flag_modified

from aiida.backends.utils import get_automatic_user
from aiida.backends.sqlalchemy.models.node import DbNode, DbLink, DbPath
from aiida.backends.sqlalchemy.models.comment import DbComment
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.computer import DbComputer

from aiida.common.utils import get_new_uuid
from aiida.common.folders import RepositoryFolder
from aiida.common.exceptions import (InternalError, ModificationNotAllowed,
                                     NotExistent, UniquenessError,
                                     ValidationError)
from aiida.common.links import LinkType
from aiida.common.lang import override

from aiida.orm.implementation.general.node import AbstractNode, _NO_DEFAULT
from aiida.orm.implementation.sqlalchemy.computer import Computer
from aiida.orm.implementation.sqlalchemy.group import Group
from aiida.orm.implementation.sqlalchemy.utils import django_filter, get_attr

import aiida.orm.autogroup

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"


class Node(AbstractNode):
    def __init__(self, **kwargs):
        super(Node, self).__init__()

        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            if not isinstance(dbnode, DbNode):
                raise TypeError("dbnode is not a DbNode instance")
            if dbnode.id is None:
                raise ValueError("If cannot load an aiida.orm.Node instance "
                                 "from an unsaved DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any "
                                 "further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name,
                                                 uuid=self._dbnode.uuid)

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
    def get_subclass_from_uuid(cls, uuid):
        try:
            node = cls.query(uuid=uuid).one()
        except (NoResultFound, ProgrammingError):
            raise NotExistent("No entry with UUID={} found".format(uuid))
        if not isinstance(node, cls):
            raise NotExistent("UUID={} is not an instance of {}".format(
                uuid, cls.__name__))
        return node

    @classmethod
    def get_subclass_from_pk(cls, pk):
        if not isinstance(pk, int):
            raise ValueError("Incorrect type for int")
        try:
            from aiida.backends.sqlalchemy import session
            node = cls.query(id=pk).one()
        except NoResultFound:
            # DataError is thrown when you pass a string instead of an int for
            # instance
            raise NotExistent("No entry with pk= {} found".format(pk))
        if not isinstance(node, cls):
            raise NotExistent("pk= {} is not an instance of {}".format(
                pk, cls.__name__))
        return node

    def __int__(self):
        if self._to_be_store:
            return None
        else:
            return self._dbnode.id

    @classmethod
    def query(cls, *args, **kwargs):
        q = django_filter(DbNode.aiida_query, **kwargs)
        q = q.reset_joinpoint()

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

            q = q.filter(DbNode.type.like("{}%".format(superclass_string)))

        return q

    def _update_db_label_field(self, field_value):
        from aiida.backends.sqlalchemy import session
        self.dbnode.label = field_value
        if not self._to_be_stored:
            self._dbnode.save(commit=False)
            self._increment_version_number_db()

    def _update_db_description_field(self, field_value):
        from aiida.backends.sqlalchemy import session
        self.dbnode.description = field_value
        if not self._to_be_stored:
            self._dbnode.save(commit=False)
            self._increment_version_number_db()

    def _replace_dblink_from(self, src, label, link_type):
        from aiida.backends.sqlalchemy import session
        try:
            self._add_dblink_from(src, label)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            self._remove_dblink_from(label)
            self._add_dblink_from(src, label, link_type)

    def _remove_dblink_from(self, label):
        from aiida.backends.sqlalchemy import session
        link = self.dbnode.outputs.filter_by(label=label).first()
        session.delete(link)
        session.commit()

    def _add_dblink_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        from aiida.backends.sqlalchemy import session
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

        # Check for cycles. This works if the transitive closure is enabled; if
        # it isn't, this test will never fail, but then having a circular link
        # is not meaningful but does not pose a huge threat
        #
        # I am linking src->self; a loop would be created if a DbPath exists
        # already in the TC table from self to src
        c = session.query(literal(True)).filter(DbPath.query
                                                .filter_by(parent_id=self.dbnode.id, child_id=src.dbnode.id)
                                                .exists()).scalar()
        if c:
            raise ValueError(
                "The link you are attempting to create would generate a loop")

        if label is None:
            autolabel_idx = 1

            existing_from_autolabels = session.query(DbLink.label).filter(
                DbLink.output_id == self.dbnode.id,
                DbLink.label.like("link%")
            )

            while "link_{}".format(autolabel_idx) in existing_from_autolabels:
                autolabel_idx += 1

            safety_counter = 0
            while True:
                safety_counter += 1
                if safety_counter > 3:
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
        from aiida.backends.sqlalchemy import session
        try:
            link = DbLink(input_id=src.dbnode.id, output_id=self.dbnode.id,
                          label=label, type=link_type.value)
            session.add(link)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise UniquenessError("There is already a link with the same "
                                  "name (raw message was {})"
                                  "".format(e))

    def get_inputs(self, node_type=None, also_labels=False, only_in_db=False,
                   link_type=None):

        link_filter = {'output': self.dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        inputs_list = [(i.label, i.input.get_aiida_class()) for i in
                       DbLink.query.filter_by(output=self.dbnode)
                           .distinct().all()]

        if not only_in_db:
            # Needed for the check
            input_list_keys = [i[0] for i in inputs_list]

            for k, v in self._inputlinks_cache.iteritems():
                src = v[0]
                if k in input_list_keys:
                    raise InternalError("There exist a link with the same name "
                                        "'{}' both in the DB and in the internal "
                                        "cache for node pk= {}!".format(k, self.id))
                inputs_list.append((k, src))

        if node_type is None:
            filtered_list = inputs_list
        else:
            filtered_list = [i for i in inputs_list if isinstance(i[1], node_type)]

        if also_labels:
            return list(filtered_list)
        else:
            return [i[1] for i in filtered_list]

    @override
    def get_outputs(self, type=None, also_labels=False, link_type=None):

        link_filter = {'input': self.dbnode}
        if link_type is not None:
            link_filter['type'] = link_type.value
        outputs_list = ((i.label, i.output.get_aiida_class()) for i in
                        DbLink.query.filter_by(**link_filter).distinct().all())

        if type is None:
            if also_labels:
                return list(outputs_list)
            else:
                return [i[1] for i in outputs_list]
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1], type))
            if also_labels:
                return list(filtered_list)
            else:
                return [i[1] for i in filtered_list]

    def set_computer(self, computer):
        if self._to_be_stored:
            computer = DbComputer.get_dbcomputer(computer)
            self.dbnode.dbcomputer = computer
        else:
            raise ModificationNotAllowed(
                "Node with uuid={} was already stored".format(self.uuid))

    def _set_attr(self, key, value):
        if self._to_be_stored:
            self._attrs_cache[key] = copy.deepcopy(value)
        else:
            self.dbnode.set_attr(key, value)
            self._increment_version_number_db()

    def _del_attr(self, key):
        if self._to_be_stored:
            try:
                del self._attrs_cache[key]
            except KeyError:
                raise AttributeError(
                    "Attribute {} does not exist".format(key))
        else:
            self.dbnode.del_attr(key)
            self._increment_version_number_db()

    def get_attr(self, key, default=_NO_DEFAULT):
        exception = AttributeError("Attribute '{}' does not exist".format(key))

        has_default = default is not _NO_DEFAULT
        if self._to_be_stored:
            try:
                return self._attrs_cache[key]
            except KeyError:
                if has_default:
                    return default
                raise exception
        else:
            try:
                return get_attr(self.dbnode.attributes, key)
            except (KeyError, IndexError):
                if has_default:
                    return default
                else:
                    raise exception

    def set_extra(self, key, value, exclusive=False):
        # TODO SP: validate key
        # TODO SP: handle exclusive (what to do in case the key already exist
        # ?)
        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set only after "
                "storing the node")

        self.dbnode.set_extra(key, value)
        self._increment_version_number_db()

    def get_extra(self, key, default=None):
        # TODO SP: in the Django implementation, if the node is not stored,
        # we can't get an extra. In the SQLA one, because this is simply a
        # column, we could still return one if it exists.
        try:
            return get_attr(self.dbnode.extras, key)
        except (KeyError, IndexError) as e:
            if default:
                return default
            else:
                raise AttributeError

    def get_extras(self):
        return self.dbnode.extras

    def del_extra(self, key):
        self.dbnode.del_extra(key)

    def extras(self):
        return self.dbnode.extras

    def iterextras(self):
        return self.dbnode.extras.iteritems()

    def iterattrs(self):
        # TODO: check what happens if someone stores the object while
        #        the iterator is being used!
        if self._to_be_stored:
            it_items = self._attrs_cache.iteritems()
        else:
            it_items = self.dbnode.attributes.iteritems()

        for k, v in it_items:
            yield (k, v)

    def get_attrs(self):
        return self.dbnode.attributes

    def attrs(self):
        if self._to_be_stored:
            it = self._attrs_cache.iterkeys()
        else:
            it = self.dbnode.attributes.iterkeys()
        for k in it:
            yield k

    def add_comment(self, content, user=None):
        from aiida.backends.sqlalchemy import session
        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after "
                                         "storing the node")

        comment = DbComment(dbnode=self._dbnode, user=user, content=content)
        session.add(comment)
        session.commit()

    def get_comment_obj(self, id=None, user=None):
        dbcomments_query = DbComment.query.filter_by(dbnode=self._dbnode)

        if id is not None:
            dbcomments_query = dbcomments_query.filter_by(id=id)
        if user is not None:
            dbcomments_query = dbcomments_query.filter_by(user=user)

        dbcomments = dbcomments_query.all()
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
        } for c in comments ]

    def _get_dbcomments(self, pk=None, with_user=False):
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

        if with_user:
            comments.join(DbUser)

        comments = comments.order_by('id').all()

        return comments

    def _update_comment(self, new_field, comment_pk, user):
        comment = DbComment.query.filter_by(dbnode=self._dbnode,
                                            id=comment_pk, user=user).first()

        if not isinstance(new_field, basestring):
            raise ValueError("Non string comments are not accepted")

        if not comment:
            raise NotExistent("Found no comment for user {} and id {}".format(
                user, comment_pk))

        comment.content = new_field
        comment.save()

    def _remove_comment(self, comment_pk, user):
        comment = DbComment.query.filter_by(dbnode=self._dbnode, id=comment_pk).first()
        if comment:
            comment.delete()

    def _increment_version_number_db(self):
        self._dbnode.nodeversion = DbNode.nodeversion + 1
        self._dbnode.save()

    def copy(self):
        newobject = self.__class__()
        newobject.dbnode.type = self.dbnode.type  # Inherit type
        newobject.dbnode.label = self.dbnode.label  # Inherit label
        # TODO: add to the description the fact that this was a copy?
        newobject.dbnode.description = self.dbnode.description  # Inherit description
        newobject.dbnode.dbcomputer = self.dbnode.dbcomputer  # Inherit computer

        for k, v in self.iterattrs():
            newobject._set_attr(k, v)

        for path in self.get_folder_list():
            newobject.add_path(self.get_abs_path(path), path)

        return newobject

    @property
    def pk(self):
        return self.dbnode.id

    @property
    def id(self):
        return self.dbnode.id

    @property
    def dbnode(self):
        return self._dbnode

    def store_all(self, with_transaction=True):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} was already stored".format(self.id))

        # For each parent, check that all its inputs are stored
        for link in self._inputlinks_cache:
            try:
                parent_node = self._inputlinks_cache[link][0]
                parent_node._check_are_parents_stored()
            except ModificationNotAllowed:
                raise ModificationNotAllowed("Parent node (UUID={}) has "
                                             "unstored parents, cannot proceed (only direct parents "
                                             "can be unstored and will be stored by store_all, not "
                                             "grandparents or other ancestors".format(parent_node.uuid))

        self._store_input_nodes()
        self.store(with_transaction=False)
        self._store_cached_input_links(with_transaction=False)
        from aiida.backends.sqlalchemy import session

        if with_transaction:
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()

        return self

    def _store_input_nodes(self):
        """
        Find all input nodes, and store them, checking that they do not
        have unstored inputs in turn.

        :note: this function stores all nodes without transactions; always
          call it from within a transaction!
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "_store_input_nodes can be called only if the node is "
                "unstored (node {} is stored, instead)".format(self.id))

        for link in self._inputlinks_cache:
            parent = self._inputlinks_cache[link][0]
            if not parent.is_stored:
                parent.store(with_transaction=False)

    def _check_are_parents_stored(self):
        """
        Check if all parents are already stored, otherwise raise.

        :raise ModificationNotAllowed: if one of the input nodes in not already
          stored.
        """
        # Preliminary check to verify that inputs are stored already
        for link in self._inputlinks_cache:
            if not self._inputlinks_cache[link][0].is_stored:
                raise ModificationNotAllowed(
                    "Cannot store the input link '{}' because the "
                    "source node is not stored. Either store it first, "
                    "or call _store_input_links with the store_parents "
                    "parameter set to True".format(link))

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

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} is not stored yet".format(self.id))

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

        from aiida.backends.sqlalchemy import session
        if with_transaction:
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()

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
        if self._to_be_stored:
            self._validate()

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

            try:
                self._dbnode.save(commit=False)
                # Save its attributes 'manually' without incrementing
                # the version for each add.
                self.dbnode.attributes = self._attrs_cache
                flag_modified(self.dbnode, "attributes")
                # This should not be used anymore: I delete it to
                # possibly free memory
                del self._attrs_cache

                self._temp_folder = None
                self._to_be_stored = False

                # Here, I store those links that were in the cache and
                # that are between stored nodes.
                self._store_cached_input_links(with_transaction=False)

                if with_transaction:
                    self.dbnode.session.commit()

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
                        g = Group.get_or_create(name=group_name, type_string=grouptype)[0]
                        g.add_nodes(self)

        return self

    @property
    def has_children(self):
        #~ from aiida.backends.sqlalchemy.model.node import DbNode
        return self.dbnode.outputs_q.all()
        #~ return session.query(literal(True)).filter(
            #~ self.dbnode.child_paths.exists()).scalar() or False

    @property
    def has_parents(self):
        return session.query(literal(True)).filter(
            self.dbnode.parent_paths.exists()).scalar() or False

    @property
    def uuid(self):
        return unicode(self.dbnode.uuid)
