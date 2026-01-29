###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for checkpoint tagging functionality in the persistence module."""

import pytest

from aiida.engine.persistence import AiiDAPersister
from aiida.orm import CalculationNode


class TestCheckpointTags:
    """Test suite for checkpoint tag functionality."""

    def test_checkpoint_default_untagged(self):
        """Test saving and retrieving a checkpoint without a tag."""
        node = CalculationNode()
        node.store()
        
        # Set default checkpoint
        checkpoint_data = '{"test": "data"}'
        node.set_checkpoint(checkpoint_data)
        
        # Retrieve default checkpoint
        retrieved = node.get_checkpoint()
        assert retrieved == checkpoint_data
        
    def test_checkpoint_with_tag(self):
        """Test saving and retrieving checkpoints with different tags."""
        node = CalculationNode()
        node.store()
        
        checkpoint_1 = '{"version": 1}'
        checkpoint_2 = '{"version": 2}'
        
        # Set checkpoints with different tags
        node.set_checkpoint(checkpoint_1, tag='v1')
        node.set_checkpoint(checkpoint_2, tag='v2')
        
        # Retrieve tagged checkpoints
        assert node.get_checkpoint(tag='v1') == checkpoint_1
        assert node.get_checkpoint(tag='v2') == checkpoint_2
        
    def test_checkpoint_mixed_tagged_and_default(self):
        """Test saving both default and tagged checkpoints."""
        node = CalculationNode()
        node.store()
        
        default_checkpoint = '{"default": true}'
        tagged_checkpoint = '{"tagged": true}'
        
        # Set default and tagged checkpoints
        node.set_checkpoint(default_checkpoint)
        node.set_checkpoint(tagged_checkpoint, tag='backup')
        
        # Retrieve both
        assert node.get_checkpoint() == default_checkpoint
        assert node.get_checkpoint(tag='backup') == tagged_checkpoint
        
    def test_checkpoint_overwrite_tag(self):
        """Test that setting a checkpoint with the same tag overwrites the previous one."""
        node = CalculationNode()
        node.store()
        
        checkpoint_1 = '{"version": 1}'
        checkpoint_2 = '{"version": 2}'
        
        # Set checkpoint with tag 'v1'
        node.set_checkpoint(checkpoint_1, tag='v1')
        assert node.get_checkpoint(tag='v1') == checkpoint_1
        
        # Overwrite with new data
        node.set_checkpoint(checkpoint_2, tag='v1')
        assert node.get_checkpoint(tag='v1') == checkpoint_2
        
    def test_checkpoint_nonexistent_tag(self):
        """Test that retrieving a nonexistent tag returns None."""
        node = CalculationNode()
        node.store()
        
        node.set_checkpoint('{"data": "test"}', tag='existing')
        
        # Try to retrieve nonexistent tag
        assert node.get_checkpoint(tag='nonexistent') is None
        assert node.get_checkpoint(tag='another_nonexistent') is None
        
    def test_checkpoint_list_tags(self):
        """Test retrieving all checkpoint tags."""
        node = CalculationNode()
        node.store()
        
        # Set multiple checkpoints
        node.set_checkpoint('{"default": true}')
        node.set_checkpoint('{"data": "v1"}', tag='v1')
        node.set_checkpoint('{"data": "v2"}', tag='v2')
        node.set_checkpoint('{"data": "backup"}', tag='backup')
        
        # Get all tags
        tags = node.get_checkpoints()
        assert None in tags  # Default checkpoint
        assert 'v1' in tags
        assert 'v2' in tags
        assert 'backup' in tags
        assert len(tags) == 4
        
    def test_checkpoint_delete_tagged(self):
        """Test deleting a specific tagged checkpoint."""
        node = CalculationNode()
        node.store()
        
        node.set_checkpoint('{"v1": "data"}', tag='v1')
        node.set_checkpoint('{"v2": "data"}', tag='v2')
        
        # Delete one tag
        node.delete_checkpoint(tag='v1')
        
        # v1 should be gone, v2 should remain
        assert node.get_checkpoint(tag='v1') is None
        assert node.get_checkpoint(tag='v2') == '{"v2": "data"}'
        
    def test_checkpoint_delete_default(self):
        """Test deleting the default checkpoint."""
        node = CalculationNode()
        node.store()
        
        node.set_checkpoint('{"default": true}')
        node.set_checkpoint('{"tagged": true}', tag='backup')
        
        # Delete default
        node.delete_checkpoint()
        
        # Default should be gone, tagged should remain
        assert node.get_checkpoint() is None
        assert node.get_checkpoint(tag='backup') == '{"tagged": true}'
        
    def test_checkpoint_delete_all(self):
        """Test deleting all checkpoints removes the attribute."""
        node = CalculationNode()
        node.store()
        
        node.set_checkpoint('{"data": "v1"}', tag='v1')
        
        # Delete the only checkpoint
        node.delete_checkpoint(tag='v1')
        
        # Attribute should be gone
        assert node.base.attributes.get(CalculationNode.CHECKPOINT_KEY, None) is None
        assert node.get_checkpoints() == []
        
    def test_checkpoint_legacy_format_compatibility(self):
        """Test that legacy string format checkpoints are still readable."""
        node = CalculationNode()
        node.store()
        
        # Simulate legacy format (directly set as string)
        legacy_checkpoint = '{"legacy": "format"}'
        node.base.attributes.set(CalculationNode.CHECKPOINT_KEY, legacy_checkpoint)
        
        # Should still be retrievable
        assert node.get_checkpoint() == legacy_checkpoint
        assert node.checkpoint == legacy_checkpoint
        
        # Should appear in list as default
        assert node.get_checkpoints() == [None]
        
    def test_checkpoint_legacy_to_tagged_migration(self):
        """Test migrating from legacy string format to tagged format."""
        node = CalculationNode()
        node.store()
        
        # Start with legacy format
        legacy_checkpoint = '{"legacy": "format"}'
        node.base.attributes.set(CalculationNode.CHECKPOINT_KEY, legacy_checkpoint)
        
        # Add a tagged checkpoint
        node.set_checkpoint('{"new_tag": "data"}', tag='new')
        
        # Both should coexist
        assert node.get_checkpoint() == legacy_checkpoint
        assert node.get_checkpoint(tag='new') == '{"new_tag": "data"}'
        
        # List should include both
        tags = node.get_checkpoints()
        assert None in tags
        assert 'new' in tags
        
    def test_checkpoint_empty_attribute(self):
        """Test handling of missing checkpoint attribute."""
        node = CalculationNode()
        node.store()
        
        # No checkpoint set
        assert node.get_checkpoint() is None
        assert node.get_checkpoint(tag='any') is None
        assert node.get_checkpoints() == []
        
    def test_checkpoint_property_backward_compatibility(self):
        """Test that the checkpoint property still works for backward compatibility."""
        node = CalculationNode()
        node.store()
        
        checkpoint_data = '{"test": "backward_compat"}'
        node.set_checkpoint(checkpoint_data)
        
        # Old-style access via property should still work
        assert node.checkpoint == checkpoint_data


class TestPersisterCheckpointTags:
    """Test suite for AiiDAPersister checkpoint tag functionality."""
    
    def test_persister_checkpoint_methods_signature(self):
        """Test that persister methods accept tag parameter."""
        persister = AiiDAPersister()
        
        # These should not raise AttributeError for tag parameter
        assert hasattr(persister, 'save_checkpoint')
        assert hasattr(persister, 'load_checkpoint')
        assert hasattr(persister, 'delete_checkpoint')
        
        # Check method signatures accept tag parameter
        import inspect
        
        save_sig = inspect.signature(persister.save_checkpoint)
        assert 'tag' in save_sig.parameters
        
        load_sig = inspect.signature(persister.load_checkpoint)
        assert 'tag' in load_sig.parameters
        
        delete_sig = inspect.signature(persister.delete_checkpoint)
        assert 'tag' in delete_sig.parameters


class TestCheckpointTagsIntegration:
    """Integration tests for checkpoint tagging with real processes."""
    
    def test_multiple_checkpoints_per_process(self):
        """Test that a single process can have multiple checkpoints."""
        node = CalculationNode()
        node.store()
        
        # Simulate multiple checkpoints at different stages
        stages = ['input_validation', 'preprocessing', 'execution', 'postprocessing']
        
        for i, stage in enumerate(stages):
            checkpoint_data = f'{{"stage": "{stage}", "progress": {i + 1}/{len(stages)}}}'
            node.set_checkpoint(checkpoint_data, tag=stage)
        
        # Verify all checkpoints
        for stage in stages:
            retrieved = node.get_checkpoint(tag=stage)
            assert retrieved is not None
            assert stage in retrieved
        
        # Verify count
        assert len(node.get_checkpoints()) == len(stages)
