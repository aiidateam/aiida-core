# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Node'
        db.create_table(u'main_node', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('type', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('label', self.gf('django.db.models.fields.TextField')(db_index=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'], null=True)),
        ))
        db.send_create_signal(u'main', ['Node'])

        # Adding model 'Link'
        db.create_table(u'main_link', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('input', self.gf('django.db.models.fields.related.ForeignKey')(related_name='output_links', to=orm['main.Node'])),
            ('output', self.gf('django.db.models.fields.related.ForeignKey')(related_name='input_links', to=orm['main.Node'])),
            ('label', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
            ('include_in_tc', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'main', ['Link'])

        # Adding model 'Path'
        db.create_table(u'main_path', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='child_paths', to=orm['main.Node'])),
            ('child', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parent_paths', to=orm['main.Node'])),
            ('depth', self.gf('django.db.models.fields.IntegerField')()),
            ('entry_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('direct_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('exit_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'main', ['Path'])

        # Adding model 'Attribute'
        db.create_table(u'main_attribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attributes', to=orm['main.Node'])),
            ('key', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('datatype', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('tval', self.gf('django.db.models.fields.TextField')()),
            ('fval', self.gf('django.db.models.fields.FloatField')()),
            ('ival', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'main', ['Attribute'])

        # Adding unique constraint on 'Attribute', fields ['node', 'key']
        db.create_unique(u'main_attribute', ['node_id', 'key'])

        # Adding model 'Group'
        db.create_table(u'main_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('name', self.gf('django.db.models.fields.TextField')(unique=True, db_index=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'main', ['Group'])

        # Adding M2M table for field nodes on 'Group'
        db.create_table(u'main_group_nodes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm[u'main.group'], null=False)),
            ('node', models.ForeignKey(orm[u'main.node'], null=False))
        ))
        db.create_unique(u'main_group_nodes', ['group_id', 'node_id'])

        # Adding model 'Computer'
        db.create_table(u'main_computer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('workdir', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('transport_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('scheduler_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('transport_params', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('metadata', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'main', ['Computer'])

        # Adding model 'RunningJob'
        db.create_table(u'main_runningjob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('calc', self.gf('django.db.models.fields.related.OneToOneField')(related_name='jobinfo', unique=True, to=orm['main.Node'])),
            ('calc_state', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('job_id', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('scheduler_state', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('last_jobinfo', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'main', ['RunningJob'])

        # Adding model 'AuthInfo'
        db.create_table(u'main_authinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('aidauser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'])),
            ('auth_params', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'main', ['AuthInfo'])

        # Adding unique constraint on 'AuthInfo', fields ['aidauser', 'computer']
        db.create_unique(u'main_authinfo', ['aidauser_id', 'computer_id'])

        # Adding model 'Comment'
        db.create_table(u'main_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['main.Node'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'main', ['Comment'])


    def backwards(self, orm):
        # Removing unique constraint on 'AuthInfo', fields ['aidauser', 'computer']
        db.delete_unique(u'main_authinfo', ['aidauser_id', 'computer_id'])

        # Removing unique constraint on 'Attribute', fields ['node', 'key']
        db.delete_unique(u'main_attribute', ['node_id', 'key'])

        # Deleting model 'Node'
        db.delete_table(u'main_node')

        # Deleting model 'Link'
        db.delete_table(u'main_link')

        # Deleting model 'Path'
        db.delete_table(u'main_path')

        # Deleting model 'Attribute'
        db.delete_table(u'main_attribute')

        # Deleting model 'Group'
        db.delete_table(u'main_group')

        # Removing M2M table for field nodes on 'Group'
        db.delete_table('main_group_nodes')

        # Deleting model 'Computer'
        db.delete_table(u'main_computer')

        # Deleting model 'RunningJob'
        db.delete_table(u'main_runningjob')

        # Deleting model 'AuthInfo'
        db.delete_table(u'main_authinfo')

        # Deleting model 'Comment'
        db.delete_table(u'main_comment')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'main.attribute': {
            'Meta': {'unique_together': "(('node', 'key'),)", 'object_name': 'Attribute'},
            'datatype': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'fval': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ival': ('django.db.models.fields.IntegerField', [], {}),
            'key': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attributes'", 'to': u"orm['main.Node']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'tval': ('django.db.models.fields.TextField', [], {})
        },
        u'main.authinfo': {
            'Meta': {'unique_together': "(('aidauser', 'computer'),)", 'object_name': 'AuthInfo'},
            'aidauser': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'auth_params': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Computer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'main.comment': {
            'Meta': {'object_name': 'Comment'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['main.Node']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'main.computer': {
            'Meta': {'object_name': 'Computer'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'scheduler_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'transport_params': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'transport_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'workdir': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'main.group': {
            'Meta': {'object_name': 'Group'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            'nodes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'to': u"orm['main.Node']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'main.link': {
            'Meta': {'object_name': 'Link'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_in_tc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'input': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'output_links'", 'to': u"orm['main.Node']"}),
            'label': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'output': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'input_links'", 'to': u"orm['main.Node']"})
        },
        u'main.node': {
            'Meta': {'object_name': 'Node'},
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents'", 'symmetrical': 'False', 'through': u"orm['main.Path']", 'to': u"orm['main.Node']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Computer']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'outputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': u"orm['main.Link']", 'to': u"orm['main.Node']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'main.path': {
            'Meta': {'object_name': 'Path'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parent_paths'", 'to': u"orm['main.Node']"}),
            'depth': ('django.db.models.fields.IntegerField', [], {}),
            'direct_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'entry_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'exit_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_paths'", 'to': u"orm['main.Node']"})
        },
        u'main.runningjob': {
            'Meta': {'object_name': 'RunningJob'},
            'calc': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'jobinfo'", 'unique': 'True', 'to': u"orm['main.Node']"}),
            'calc_state': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_id': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'last_jobinfo': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'scheduler_state': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }

    complete_apps = ['main']