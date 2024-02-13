###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for verdi node"""
import errno
import gzip
import io
import os
import warnings

import pytest
from aiida import orm
from aiida.cmdline.commands import cmd_node
from aiida.cmdline.utils.echo import ExitCode


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiNode:
    """Tests for `verdi node`."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        node = orm.Data()

        self.ATTR_KEY_ONE = 'a'
        self.ATTR_VAL_ONE = '1'
        self.ATTR_KEY_TWO = 'b'
        self.ATTR_VAL_TWO = 'test'

        node.base.attributes.set_many({self.ATTR_KEY_ONE: self.ATTR_VAL_ONE, self.ATTR_KEY_TWO: self.ATTR_VAL_TWO})

        self.EXTRA_KEY_ONE = 'x'
        self.EXTRA_VAL_ONE = '2'
        self.EXTRA_KEY_TWO = 'y'
        self.EXTRA_VAL_TWO = 'other'

        node.base.extras.set_many({self.EXTRA_KEY_ONE: self.EXTRA_VAL_ONE, self.EXTRA_KEY_TWO: self.EXTRA_VAL_TWO})

        node.store()
        self.node = node

    @classmethod
    def get_unstored_folder_node(cls):
        """Get a "default" folder node with some data.

        The node is unstored so one can add more content to it before storing it.
        """
        folder_node = orm.FolderData()
        cls.content_file1 = 'nobody expects'
        cls.content_file2 = 'the minister of silly walks'
        cls.key_file1 = 'some/nested/folder/filename.txt'
        cls.key_file2 = 'some_other_file.txt'
        folder_node.base.repository.put_object_from_filelike(io.StringIO(cls.content_file1), cls.key_file1)
        folder_node.base.repository.put_object_from_filelike(io.StringIO(cls.content_file2), cls.key_file2)
        return folder_node

    def test_node_show(self, run_cli_command):
        """Test `verdi node show`"""
        node = orm.Data().store()
        node.label = 'SOMELABEL'
        options = [str(node.pk)]
        result = run_cli_command(cmd_node.node_show, options, use_subprocess=True)

        # Let's check some content in the output. At least the UUID and the label should be in there
        assert node.label in result.output
        assert node.uuid in result.output

        # Let's now test the '--print-groups' option
        options.append('--print-groups')
        result = run_cli_command(cmd_node.node_show, options, use_subprocess=True)
        # I don't check the list of groups - it might be in an autogroup

        # Let's create a group and put the node in there
        group_name = 'SOMEGROUPNAME'
        group = orm.Group(group_name).store()
        group.add_nodes(node)

        result = run_cli_command(cmd_node.node_show, options, use_subprocess=True)

        # Now the group should be in there
        assert group_name in result.output

    def test_node_attributes(self, run_cli_command):
        """Test verdi node attributes"""
        options = [str(self.node.uuid)]
        result = run_cli_command(cmd_node.attributes, options, suppress_warnings=True)
        assert self.ATTR_KEY_ONE in result.output
        assert self.ATTR_VAL_ONE in result.output
        assert self.ATTR_KEY_TWO in result.output
        assert self.ATTR_VAL_TWO in result.output

        for flag in ['-k', '--keys']:
            options = [flag, self.ATTR_KEY_ONE, '--', str(self.node.uuid)]
            result = run_cli_command(cmd_node.attributes, options, suppress_warnings=True)
            assert self.ATTR_KEY_ONE in result.output
            assert self.ATTR_VAL_ONE in result.output
            assert self.ATTR_KEY_TWO not in result.output
            assert self.ATTR_VAL_TWO not in result.output

        for flag in ['-r', '--raw']:
            options = [flag, str(self.node.uuid)]
            run_cli_command(cmd_node.attributes, options, suppress_warnings=True)

        for flag in ['-f', '--format']:
            for fmt in ['json+date', 'yaml', 'yaml_expanded']:
                options = [flag, fmt, str(self.node.uuid)]
                run_cli_command(cmd_node.attributes, options, suppress_warnings=True)

        for flag in ['-i', '--identifier']:
            for fmt in ['pk', 'uuid']:
                options = [flag, fmt, str(self.node.uuid)]
                run_cli_command(cmd_node.attributes, options, suppress_warnings=True)

    def test_node_extras(self, run_cli_command):
        """Test verdi node extras"""
        options = [str(self.node.uuid)]
        result = run_cli_command(cmd_node.extras, options, suppress_warnings=True)
        assert self.EXTRA_KEY_ONE in result.output
        assert self.EXTRA_VAL_ONE in result.output
        assert self.EXTRA_KEY_TWO in result.output
        assert self.EXTRA_VAL_TWO in result.output

        for flag in ['-k', '--keys']:
            options = [flag, self.EXTRA_KEY_ONE, '--', str(self.node.uuid)]
            result = run_cli_command(cmd_node.extras, options, suppress_warnings=True)
            assert self.EXTRA_KEY_ONE in result.output
            assert self.EXTRA_VAL_ONE in result.output
            assert self.EXTRA_KEY_TWO not in result.output
            assert self.EXTRA_VAL_TWO not in result.output

        for flag in ['-r', '--raw']:
            options = [flag, str(self.node.uuid)]
            result = run_cli_command(cmd_node.extras, options, suppress_warnings=True)

        for flag in ['-f', '--format']:
            for fmt in ['json+date', 'yaml', 'yaml_expanded']:
                options = [flag, fmt, str(self.node.uuid)]
                run_cli_command(cmd_node.extras, options, suppress_warnings=True)

        for flag in ['-i', '--identifier']:
            for fmt in ['pk', 'uuid']:
                options = [flag, fmt, str(self.node.uuid)]
                run_cli_command(cmd_node.extras, options, suppress_warnings=True)

    def test_node_repo_ls(self, run_cli_command):
        """Test 'verdi node repo ls' command."""
        folder_node = self.get_unstored_folder_node().store()

        options = [str(folder_node.pk), 'some/nested/folder']
        result = run_cli_command(cmd_node.repo_ls, options)

        assert 'filename.txt' in result.output

        options = [str(folder_node.pk), 'some/non-existing-folder']
        result = run_cli_command(cmd_node.repo_ls, options, raises=True)
        assert 'does not exist for the given node' in result.output

    def test_node_repo_cat(self, run_cli_command):
        """Test 'verdi node repo cat' command."""
        # Test cat binary files
        folder_node = orm.FolderData()
        bytestream = gzip.compress(b'COMPRESS')
        folder_node.base.repository.put_object_from_filelike(io.BytesIO(bytestream), 'filename.txt.gz')
        folder_node.store()

        options = [str(folder_node.pk), 'filename.txt.gz']
        result = run_cli_command(cmd_node.repo_cat, options)
        assert gzip.decompress(result.stdout_bytes) == b'COMPRESS'

    def test_node_repo_cat_singlefile(self, run_cli_command):
        """Test ``verdi node repo cat`` for a ``SinglefileNode``.

        Here the relative path argument should be optional and the command should determine it automatically.
        """
        node = orm.SinglefileData(io.BytesIO(b'content')).store()
        options = [str(node.pk)]
        result = run_cli_command(cmd_node.repo_cat, options)
        assert result.stdout_bytes == b'content'

    def test_node_repo_dump(self, tmp_path, run_cli_command):
        """Test 'verdi node repo dump' command."""
        folder_node = self.get_unstored_folder_node().store()
        out_path = tmp_path / 'out_dir'
        options = [str(folder_node.uuid), str(out_path)]
        res = run_cli_command(cmd_node.repo_dump, options)
        assert not res.stdout

        for file_key, content in [(self.key_file1, self.content_file1), (self.key_file2, self.content_file2)]:
            curr_path = out_path
            for key_part in file_key.split('/'):
                curr_path /= key_part
                assert curr_path.exists()
            with curr_path.open('r') as res_file:
                assert res_file.read() == content

    def test_node_repo_dump_to_nested_folder(self, tmp_path, run_cli_command):
        """Test 'verdi node repo dump' command, with an output folder whose parent does not exist."""
        folder_node = self.get_unstored_folder_node().store()
        out_path = tmp_path / 'out_dir' / 'nested' / 'path'
        options = [str(folder_node.uuid), str(out_path)]
        res = run_cli_command(cmd_node.repo_dump, options)
        assert not res.stdout

        for file_key, content in [(self.key_file1, self.content_file1), (self.key_file2, self.content_file2)]:
            curr_path = out_path
            for key_part in file_key.split('/'):
                curr_path /= key_part
                assert curr_path.exists()
            with curr_path.open('r') as res_file:
                assert res_file.read() == content

    def test_node_repo_existing_out_dir(self, tmp_path, run_cli_command):
        """Test 'verdi node repo dump' command, check that an existing output directory is not overwritten."""
        folder_node = self.get_unstored_folder_node().store()
        out_path = tmp_path / 'out_dir'
        # Create the directory and put a file in it
        out_path.mkdir()
        some_file = out_path / 'file_name'
        some_file_content = 'ni!'
        with some_file.open('w') as file_handle:
            file_handle.write(some_file_content)
        options = [str(folder_node.uuid), str(out_path)]
        res = run_cli_command(cmd_node.repo_dump, options, raises=True)
        assert 'exists' in res.stderr

        # Make sure the directory content is still there
        with some_file.open('r') as file_handle:
            assert file_handle.read() == some_file_content


def delete_temporary_file(filepath):
    """Attempt to delete a file, given an absolute path. If the deletion fails because the file does not exist
    the exception will be caught and passed. Any other exceptions will raise.

    :param filepath: the absolute file path
    """
    try:
        os.remove(filepath)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise
        else:
            pass


class TestVerdiGraph:
    """Tests for the ``verdi node graph`` command."""

    @pytest.fixture(autouse=True)
    def init_profile(self, run_cli_command, tmp_path):
        """Initialize the profile."""
        from aiida.orm import Data

        self.node = Data().store()

        # some of the export tests write in the current directory,
        # make sure it is writeable and we don't pollute the current one
        self.old_cwd = os.getcwd()
        self.cwd = str(tmp_path.absolute())
        os.chdir(self.cwd)
        yield
        os.chdir(self.old_cwd)
        os.rmdir(self.cwd)

    def test_generate_graph(self, run_cli_command):
        """Test that the default graph can be generated
        The command should run without error and should produce the .dot file
        """
        # Get a PK of a node which exists
        root_node = str(self.node.pk)
        filename = f'{root_node}.dot.pdf'
        options = [root_node]
        try:
            run_cli_command(cmd_node.graph_generate, options)
            assert os.path.isfile(filename)
        finally:
            delete_temporary_file(filename)

    def test_catch_bad_pk(self, run_cli_command):
        """Test that an invalid root_node pk (non-numeric, negative, or decimal),
        or non-existent pk will produce an error
        """
        from aiida.common.exceptions import NotExistent
        from aiida.orm import load_node

        # Forbidden pk
        for root_node in ['xyz', '-5', '3.14']:
            options = [root_node]
            filename = f'{root_node}.dot.pdf'
            try:
                run_cli_command(cmd_node.graph_generate, options, raises=True)
                assert not os.path.isfile(filename)
            finally:
                delete_temporary_file(filename)

        # Non-existant pk

        # Check that an arbitrary pk definately can't be loaded
        root_node = 123456789
        try:
            node = load_node(pk=root_node)
            assert node is None
        except NotExistent:
            pass
        #  Make sure verdi graph rejects this non-existant pk
        try:
            filename = f'{root_node!s}.dot.pdf'
            options = [str(root_node)]
            run_cli_command(cmd_node.graph_generate, options, raises=True)
            assert not os.path.isfile(filename)
        finally:
            delete_temporary_file(filename)

    def test_check_recursion_flags(self, run_cli_command):
        """Test the ancestor-depth and descendent-depth options.

        Test that they don't fail if not specified and that, if specified, they only accept positive ints
        """
        root_node = str(self.node.pk)
        filename = f'{root_node}.dot.pdf'

        # Test that not specifying them works
        try:
            run_cli_command(cmd_node.graph_generate, [root_node])
            assert os.path.isfile(filename)
        finally:
            delete_temporary_file(filename)

        # Test that the options accept zero or a positive int
        for opt in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for value in ['0', '1']:
                options = [opt, value, root_node]
                try:
                    run_cli_command(cmd_node.graph_generate, options)
                    assert os.path.isfile(filename)
                finally:
                    delete_temporary_file(filename)

        # Check the options reject any values that are not positive ints
        for flag in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for badvalue in ['xyz', '3.14', '-5']:
                options = [flag, badvalue, root_node]
                try:
                    run_cli_command(cmd_node.graph_generate, options, raises=True)
                    assert not os.path.isfile(filename)
                finally:
                    delete_temporary_file(filename)

    def test_check_io_flags(self, run_cli_command):
        """Test the input and output flags work."""
        root_node = str(self.node.pk)
        filename = f'{root_node}.dot.pdf'

        for flag in ['-i', '--process-in', '-o', '--process-out']:
            options = [flag, root_node]
            try:
                run_cli_command(cmd_node.graph_generate, options)
                assert os.path.isfile(filename)
            finally:
                delete_temporary_file(filename)

    def test_output_format(self, run_cli_command):
        """Test that the output file format can be specified"""
        root_node = str(self.node.pk)

        for option in ['-f', '--output-format']:
            # Test different formats. Could exhaustively test the formats
            # supported on a given OS (printed by '$ dot -T?') but here
            # we just use the built-ins dot and canon as a minimal check that
            # the option works. After all, this test is for the cmdline.
            for fileformat in ['pdf', 'png']:
                filename = f'{root_node}.dot.{fileformat}'
                options = [option, fileformat, root_node]
                try:
                    run_cli_command(cmd_node.graph_generate, options)
                    assert os.path.isfile(filename)
                finally:
                    delete_temporary_file(filename)

    def test_node_id_label_format(self, run_cli_command):
        """Test that the node id label format can be specified"""
        root_node = str(self.node.pk)
        filename = f'{root_node}.dot.pdf'

        for id_label_type in ['uuid', 'pk', 'label']:
            options = ['--identifier', id_label_type, root_node]
            try:
                run_cli_command(cmd_node.graph_generate, options)
                assert os.path.isfile(filename)
            finally:
                delete_temporary_file(filename)

    @pytest.mark.parametrize('output_file', ('without_extension', 'without_extension.pdf'))
    def test_output_file(self, run_cli_command, output_file):
        """Test that the output file can be specified through an argument."""
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                run_cli_command(cmd_node.graph_generate, [str(self.node.pk), output_file])
                assert os.path.isfile(output_file)
            finally:
                delete_temporary_file(output_file)


COMMENT = 'Well I never...'


class TestVerdiUserCommand:
    """Tests for the ``verdi node comment`` command."""

    @pytest.fixture(autouse=True)
    def init_profile(self, run_cli_command):
        """Initialize the profile."""
        self.node = orm.Data().store()

    def test_comment_show_simple(self, run_cli_command):
        """Test simply calling the show command (without data to show)."""
        result = run_cli_command(cmd_node.comment_show, [], suppress_warnings=True)
        assert result.output == ''
        assert result.exit_code == 0

    def test_comment_show(self, run_cli_command):
        """Test showing an existing comment."""
        self.node.base.comments.add(COMMENT)

        options = [str(self.node.pk)]
        result = run_cli_command(cmd_node.comment_show, options)
        assert result.output.find(COMMENT) != -1
        assert result.exit_code == 0

    def test_comment_add(self, run_cli_command):
        """Test adding a comment."""
        options = ['-N', str(self.node.pk), '--', f'{COMMENT}']
        result = run_cli_command(cmd_node.comment_add, options)
        assert result.exit_code == 0

        comment = self.node.base.comments.all()
        assert len(comment) == 1
        assert comment[0].content == COMMENT

    def test_comment_remove(self, run_cli_command):
        """Test removing a comment."""
        comment = self.node.base.comments.add(COMMENT)

        assert len(self.node.base.comments.all()) == 1

        options = [str(comment.pk), '--force']
        result = run_cli_command(cmd_node.comment_remove, options)
        assert result.exit_code == 0, result.output
        assert len(self.node.base.comments.all()) == 0


@pytest.fixture(scope='class')
def create_nodes(aiida_profile_clean_class):
    return [
        orm.Data().store(),
        orm.Bool(True).store(),
        orm.Bool(False).store(),
        orm.Float(1.0).store(),
        orm.Int(1).store(),
    ]


@pytest.mark.usefixtures('create_nodes')
class TestVerdiRehash:
    """Tests for the ``verdi node rehash`` command."""

    def test_rehash_interactive_yes(self, run_cli_command):
        """Passing no options and answering 'Y' to the command will rehash all 5 nodes."""
        expected_node_count = 5
        options = []  # no option, will ask in the prompt
        result = run_cli_command(cmd_node.rehash, options, user_input='y')
        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_interactive_no(self, run_cli_command):
        """Passing no options and answering 'N' to the command will abort the command."""
        options = []  # no option, will ask in the prompt
        result = run_cli_command(cmd_node.rehash, options, user_input='n', raises=True)
        assert result.exit_code == ExitCode.CRITICAL

    def test_rehash(self, run_cli_command):
        """Passing no options to the command will rehash all 5 nodes."""
        expected_node_count = 5
        options = ['-f']  # force, so no questions are asked
        result = run_cli_command(cmd_node.rehash, options)
        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_bool(self, run_cli_command):
        """Limiting the queryset by defining an entry point, in this case bool, should limit nodes to 2."""
        expected_node_count = 2
        options = ['-f', '-e', 'aiida.data:core.bool']
        result = run_cli_command(cmd_node.rehash, options)

        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_float(self, run_cli_command):
        """Limiting the queryset by defining an entry point, in this case float, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:core.float']
        result = run_cli_command(cmd_node.rehash, options)

        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_int(self, run_cli_command):
        """Limiting the queryset by defining an entry point, in this case int, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:core.int']
        result = run_cli_command(cmd_node.rehash, options)

        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_explicit_pk(self, run_cli_command):
        """Limiting the queryset by defining explicit identifiers, should limit nodes to 2 in this example."""
        nodes = orm.QueryBuilder().append(orm.Bool, project='id').all(flat=True)
        expected_node_count = 2
        options = ['-f'] + [str(pk) for pk in nodes]
        result = run_cli_command(cmd_node.rehash, options)

        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_explicit_pk_and_entry_point(self, run_cli_command):
        """Limiting the queryset by defining explicit identifiers and entry point, should limit nodes to 1."""
        nodes = orm.QueryBuilder().append(orm.Float, project='id').all(flat=True)
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:core.float'] + [str(pk) for pk in nodes]
        result = run_cli_command(cmd_node.rehash, options)

        assert f'{expected_node_count} nodes re-hashed' in result.output

    def test_rehash_entry_point_no_matches(self, run_cli_command):
        """Limiting the queryset by defining explicit entry point, with no nodes should exit with non-zero status."""
        options = ['-f', '-e', 'aiida.data:core.structure']
        run_cli_command(cmd_node.rehash, options, raises=True)

    def test_rehash_invalid_entry_point(self, run_cli_command):
        """Passing an invalid entry point should exit with non-zero status."""
        # Incorrect entry point group
        options = ['-f', '-e', 'data:core.structure']
        run_cli_command(cmd_node.rehash, options, raises=True)

        # Non-existent entry point name
        options = ['-f', '-e', 'aiida.data:inexistant']
        run_cli_command(cmd_node.rehash, options, raises=True)

        # Incorrect syntax, no colon to join entry point group and name
        options = ['-f', '-e', 'aiida.data.structure']
        run_cli_command(cmd_node.rehash, options, raises=True)


@pytest.mark.parametrize(
    'options',
    (
        ['--verbosity', 'info'],
        ['--verbosity', 'info', '--force'],
        ['--create-forward'],
        ['--call-calc-forward'],
        ['--call-work-forward'],
        ['--force'],
    ),
)
def test_node_delete_basics(run_cli_command, options):
    """Testing the correct translation for the `--force` and `--verbosity` options.
    This just checks that the calls do not except and that in all cases with the
    force flag there is no messages.
    """
    from aiida.common.exceptions import NotExistent

    node = orm.Data().store()
    pk = node.pk

    run_cli_command(cmd_node.node_delete, options + [str(pk), '--dry-run'], use_subprocess=True)

    # To delete the created node
    run_cli_command(cmd_node.node_delete, [str(pk), '--force'], use_subprocess=True)

    with pytest.raises(NotExistent):
        orm.load_node(pk)


def test_node_delete_missing_pk(run_cli_command):
    """Check that no exception is raised when a non-existent pk is given (just warns)."""
    run_cli_command(cmd_node.node_delete, ['999'])
