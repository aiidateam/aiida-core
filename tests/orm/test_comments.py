###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the Comment ORM class."""

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.orm.comments import Comment
from aiida.tools.graph.deletions import delete_nodes


@pytest.fixture
def node():
    """Return a stored node."""
    return orm.Data().store()


@pytest.fixture
def create_comment(default_user, node):
    """Create a comment with a default user and node."""

    def factory(content=''):
        return Comment(node, default_user, content).store()

    return factory


def test_comment_content(create_comment):
    """Test getting and setting content of a Comment."""
    content = 'Be more constructive with your feedback'
    comment = create_comment(content)
    assert comment.content == content


def test_comment_mtime(create_comment):
    """Test getting and setting mtime of a Comment."""
    comment = create_comment()
    mtime = comment.mtime
    comment.set_content('Changing an attribute should automatically change the mtime')
    assert comment.content == 'Changing an attribute should automatically change the mtime'
    assert comment.mtime != mtime


def test_comment_node(node, default_user):
    """Test getting the node of a Comment."""
    comment = Comment(node, default_user, 'comment').store()
    assert comment.node.uuid == node.uuid


def test_comment_user(node, default_user):
    """Test getting the user of a Comment."""
    comment = Comment(node, default_user, 'comment').store()
    assert comment.user.uuid == default_user.uuid


@pytest.mark.xfail
def test_comment_set_user(node, default_user):
    new_user = orm.User(email='meeseeks.look@me').store()
    comment = Comment(node, default_user, 'Look at me!').store()
    assert comment.user.uuid == default_user.uuid
    comment.set_user(new_user)
    assert comment.user.uuid == new_user.uuid


def test_comment_collection_get(create_comment):
    """Test retrieving a Comment through the collection."""
    comment = create_comment()
    loaded = Comment.collection.get(id=comment.pk)
    assert loaded.uuid == comment.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_comment_collection_delete(node, default_user):
    """Test deleting a Comment through the collection."""
    comment = Comment(node, default_user, 'I will perish').store()
    comment_pk = comment.pk

    Comment.collection.delete(comment.pk)

    with pytest.raises(exceptions.NotExistent):
        Comment.collection.delete(comment_pk)

    with pytest.raises(exceptions.NotExistent):
        Comment.collection.get(id=comment_pk)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_comment_collection_delete_all(node, default_user):
    """Test deleting all Comments through the collection."""
    comment = Comment(node, default_user, 'I will perish').store()
    Comment(node, default_user, 'Surely not?').store()
    comment_pk = comment.pk

    # Assert the comments exist
    assert len(Comment.collection.all()) == 2

    # Delete all Comments
    Comment.collection.delete_all()

    with pytest.raises(exceptions.NotExistent):
        Comment.collection.delete(comment_pk)

    with pytest.raises(exceptions.NotExistent):
        Comment.collection.get(id=comment_pk)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_comment_collection_delete_many(node, default_user):
    """Test deleting many Comments through the collection."""
    comment_one = Comment(node, default_user, 'I will perish').store()
    comment_two = Comment(node, default_user, 'Surely not?').store()
    comment_ids = [_.pk for _ in [comment_one, comment_two]]

    # Assert the Comments exist
    assert len(Comment.collection.all()) == 2

    # Delete new Comments using filter
    filters = {'id': {'in': comment_ids}}
    Comment.collection.delete_many(filters=filters)

    builder = orm.QueryBuilder().append(Comment, project='id')
    assert builder.count() == 0

    for comment_pk in comment_ids:
        with pytest.raises(exceptions.NotExistent):
            Comment.collection.delete(comment_pk)

        with pytest.raises(exceptions.NotExistent):
            Comment.collection.get(id=comment_pk)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_comment_querybuilder(default_user):
    """Test querying for comments by joining on nodes in the QueryBuilder."""
    user_one = default_user
    user_two = orm.User(email='commenting@user.s').store()

    node_one = orm.Data().store()
    comment_one = Comment(node_one, user_one, 'comment_one').store()

    node_two = orm.Data().store()
    comment_two = Comment(node_two, user_one, 'comment_two').store()
    comment_three = Comment(node_two, user_one, 'comment_three').store()

    node_three = orm.CalculationNode().store()
    comment_four = Comment(node_three, user_two, 'new_user_comment').store()

    node_four = orm.CalculationNode().store()
    comment_five = Comment(node_four, user_one, 'user one comment').store()
    comment_six = Comment(node_four, user_two, 'user two comment').store()

    # Retrieve a node by joining on a specific comment
    builder = orm.QueryBuilder()
    builder.append(Comment, tag='comment', filters={'id': comment_one.pk})
    builder.append(orm.Node, with_comment='comment', project=['uuid'])
    nodes = builder.all()

    assert len(nodes) == 1
    for query_node in nodes:
        assert str(query_node[0]) in [node_one.uuid]

    # Retrieve a comment by joining on a specific node
    builder = orm.QueryBuilder()
    builder.append(orm.Node, tag='node', filters={'id': node_two.pk})
    builder.append(Comment, with_node='node', project=['uuid'])
    comments = builder.all()

    assert len(comments) == 2
    for comment in comments:
        assert str(comment[0]) in [comment_two.uuid, comment_three.uuid]

    # Retrieve a user by joining on a specific comment
    builder = orm.QueryBuilder()
    builder.append(Comment, tag='comment', filters={'id': comment_four.pk})
    builder.append(orm.User, with_comment='comment', project=['email'])
    users = builder.all()

    assert len(users) == 1
    for user in users:
        assert str(user[0]) == user_two.email

    # Retrieve a comment by joining on a specific user
    builder = orm.QueryBuilder()
    builder.append(orm.User, tag='user', filters={'email': user_one.email})
    builder.append(Comment, with_user='user', project=['uuid'])
    comments = builder.all()

    assert len(comments) == 4
    for comment in comments:
        assert str(comment[0]) in [comment_one.uuid, comment_two.uuid, comment_three.uuid, comment_five.uuid]

    # Retrieve users from comments of a single node by joining specific node
    builder = orm.QueryBuilder()
    builder.append(orm.Node, tag='node', filters={'id': node_four.pk})
    builder.append(Comment, tag='comments', with_node='node', project=['uuid'])
    builder.append(orm.User, with_comment='comments', project=['email'])
    comments_and_users = builder.all()

    assert len(comments_and_users) == 2
    for entry in comments_and_users:
        assert len(entry) == 2

        comment_uuid = str(entry[0])
        user_email = str(entry[1])

        assert comment_uuid in [comment_five.uuid, comment_six.uuid]
        assert user_email in [user_one.email, user_two.email]


def test_objects_get(node):
    """Test getting a comment from the collection"""
    comment = node.base.comments.add('Check out the comment on _this_ one')
    gotten_comment = Comment.collection.get(id=comment.pk)
    assert isinstance(gotten_comment, Comment)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_delete_node_with_comments(node, default_user):
    """Test deleting a node with comments."""
    Comment(node, default_user, 'I will perish').store()
    assert len(Comment.collection.all()) == 1
    delete_nodes([node.pk], dry_run=False)
    assert len(Comment.collection.all()) == 0
