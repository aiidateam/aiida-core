# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.djsite.db.models import DbComment
from aiida.orm.implementation.general.comment import AbstractComment
from aiida.common.exceptions import NotExistent, MultipleObjectsError



class Comment(AbstractComment):

    def __init__(self, **kwargs):

        # If no arguments are passed, then create a new DbComment
        if not kwargs:
            self.dbcomment = DbComment()

        # If a DbComment is passed as argument. Just use it and
        # wrap it with a Comment object
        elif 'dbcomment' in kwargs:
            # When a dbcomment is passed as argument, then no other arguments
            # should be passed.
            if len(kwargs) > 1:
                raise ValueError("When a DbComment is passed as argument, no"
                                 "further arguments are accepted.")
            dbcomment = kwargs.pop('dbcomment')
            if not isinstance(dbcomment, DbComment):
                raise ValueError("Expected a DbComment. Object of a different"
                                 "class was given as argument.")
            self.dbcomment = dbcomment

        else:
            id = kwargs.pop('id', None)
            if id is None:
                id = kwargs.pop('pk', None)
            user = kwargs.pop('user', None)
            dbnode = kwargs.pop('dbnode', None)

            # Constructing the default query
            import operator
            from django.db.models import Q
            query_list = []

            # If an id is specified then we add it to the query
            if id is not None:
                query_list.append(Q(pk=id))

            # If a user is specified then we add it to the query
            if user is not None:
                query_list.append(Q(user=user))

            # If a dbnode is specified then we add it to the query
            if dbnode is not None:
                query_list.append(Q(dbnode=dbnode))

            res = DbComment.objects.filter(reduce(operator.and_, query_list))
            ccount = len(res)
            if ccount > 1:
                raise MultipleObjectsError(
                    "The arguments that you specified were too vague. More "
                    "than one comments with this data were found in the "
                    "database")
            elif ccount == 0:
                raise NotExistent("No comments were found with the given "
                                 "arguments")

            self.dbcomment = res[0]

    @property
    def pk(self):
        return self.dbnode.pk

    @property
    def id(self):
        return self.dbnode.pk

    @property
    def to_be_stored(self):
        return self.dbcomment.pk is None

    @property
    def uuid(self):
        return unicode(self.dbcomment.uuid)

    def get_ctime(self):
        return self.dbcomment.ctime

    def set_ctime(self, val):
        self.dbcomment.ctime = val
        if not self.to_be_stored:
            self.dbcomment.save()

    def get_mtime(self):
        return self.dbcomment.mtime

    def set_mtime(self, val):
        self.dbcomment.mtime = val
        if not self.to_be_stored:
            self.dbcomment.save()

    def get_user(self):
        return self.dbcomment.user

    def set_user(self, val):
        self.dbcomment.user = val
        if not self.to_be_stored:
            self.dbcomment.save()

    def get_content(self):
        return self.dbcomment.content

    def set_content(self, val):
        self.dbcomment.content = val
        if not self.to_be_stored:
            self.dbcomment.save()

    def delete(self):
        self.dbcomment.delete()

