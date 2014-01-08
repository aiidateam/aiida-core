# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DbNode'
        db.create_table(u'db_dbnode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('label', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], on_delete=models.PROTECT)),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['db.DbComputer'], null=True, on_delete=models.PROTECT)),
            ('nodeversion', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('lastsyncedversion', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'db', ['DbNode'])

        # Adding model 'Link'
        db.create_table(u'db_link', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('input', self.gf('django.db.models.fields.related.ForeignKey')(related_name='output_links', to=orm['db.DbNode'])),
            ('output', self.gf('django.db.models.fields.related.ForeignKey')(related_name='input_links', to=orm['db.DbNode'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal(u'db', ['Link'])

        # Adding unique constraint on 'Link', fields ['input', 'output']
        db.create_unique(u'db_link', ['input_id', 'output_id'])

        # Adding unique constraint on 'Link', fields ['output', 'label']
        db.create_unique(u'db_link', ['output_id', 'label'])

        # Adding model 'Path'
        db.create_table(u'db_path', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='child_paths', to=orm['db.DbNode'])),
            ('child', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parent_paths', to=orm['db.DbNode'])),
            ('depth', self.gf('django.db.models.fields.IntegerField')()),
            ('entry_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('direct_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('exit_edge_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'db', ['Path'])

        # Adding model 'Attribute'
        db.create_table(u'db_attribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('dbnode', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attributes', to=orm['db.DbNode'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('datatype', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('tval', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('fval', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
            ('ival', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('bval', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('dval', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
        ))
        db.send_create_signal(u'db', ['Attribute'])

        # Adding unique constraint on 'Attribute', fields ['dbnode', 'key']
        db.create_unique(u'db_attribute', ['dbnode_id', 'key'])

        # Adding model 'Group'
        db.create_table(u'db_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'db', ['Group'])

        # Adding M2M table for field dbnodes on 'Group'
        m2m_table_name = db.shorten_name(u'db_group_dbnodes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm[u'db.group'], null=False)),
            ('dbnode', models.ForeignKey(orm[u'db.dbnode'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'dbnode_id'])

        # Adding model 'DbComputer'
        db.create_table(u'db_dbcomputer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('workdir', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('transport_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('scheduler_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('transport_params', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('metadata', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'db', ['DbComputer'])

        # Adding model 'AuthInfo'
        db.create_table(u'db_authinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('aiidauser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['db.DbComputer'])),
            ('auth_params', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'db', ['AuthInfo'])

        # Adding unique constraint on 'AuthInfo', fields ['aiidauser', 'computer']
        db.create_unique(u'db_authinfo', ['aiidauser_id', 'computer_id'])

        # Adding model 'Comment'
        db.create_table(u'db_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dbnode', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['db.DbNode'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'db', ['Comment'])

        # Adding model 'DbLock'
        db.create_table(u'db_dblock', (
            ('key', self.gf('django.db.models.fields.TextField')(primary_key=True)),
            ('creation', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('timeout', self.gf('django.db.models.fields.IntegerField')()),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'db', ['DbLock'])

        # Adding model 'DbWorkflow'
        db.create_table(u'db_dbworkflow', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], on_delete=models.PROTECT)),
            ('report', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('module', self.gf('django.db.models.fields.TextField')()),
            ('module_class', self.gf('django.db.models.fields.TextField')()),
            ('script_path', self.gf('django.db.models.fields.TextField')()),
            ('script_md5', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='INITIALIZED', max_length=255)),
        ))
        db.send_create_signal(u'db', ['DbWorkflow'])

        # Adding model 'DbWorkflowData'
        db.create_table(u'db_dbworkflowdata', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data', to=orm['db.DbWorkflow'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('data_type', self.gf('django.db.models.fields.TextField')(default='PARAMETER')),
            ('value_type', self.gf('django.db.models.fields.TextField')(default='NONE')),
            ('json_value', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('aiida_obj', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['db.DbNode'], null=True, blank=True)),
        ))
        db.send_create_signal(u'db', ['DbWorkflowData'])

        # Adding unique constraint on 'DbWorkflowData', fields ['parent', 'name', 'data_type']
        db.create_unique(u'db_dbworkflowdata', ['parent_id', 'name', 'data_type'])

        # Adding model 'DbWorkflowStep'
        db.create_table(u'db_dbworkflowstep', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='steps', to=orm['db.DbWorkflow'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], on_delete=models.PROTECT)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('nextcall', self.gf('django.db.models.fields.CharField')(default='none', max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='CREATED', max_length=255)),
        ))
        db.send_create_signal(u'db', ['DbWorkflowStep'])

        # Adding unique constraint on 'DbWorkflowStep', fields ['parent', 'name']
        db.create_unique(u'db_dbworkflowstep', ['parent_id', 'name'])

        # Adding M2M table for field calculations on 'DbWorkflowStep'
        m2m_table_name = db.shorten_name(u'db_dbworkflowstep_calculations')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dbworkflowstep', models.ForeignKey(orm[u'db.dbworkflowstep'], null=False)),
            ('dbnode', models.ForeignKey(orm[u'db.dbnode'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dbworkflowstep_id', 'dbnode_id'])

        # Adding M2M table for field sub_workflows on 'DbWorkflowStep'
        m2m_table_name = db.shorten_name(u'db_dbworkflowstep_sub_workflows')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dbworkflowstep', models.ForeignKey(orm[u'db.dbworkflowstep'], null=False)),
            ('dbworkflow', models.ForeignKey(orm[u'db.dbworkflow'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dbworkflowstep_id', 'dbworkflow_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'DbWorkflowStep', fields ['parent', 'name']
        db.delete_unique(u'db_dbworkflowstep', ['parent_id', 'name'])

        # Removing unique constraint on 'DbWorkflowData', fields ['parent', 'name', 'data_type']
        db.delete_unique(u'db_dbworkflowdata', ['parent_id', 'name', 'data_type'])

        # Removing unique constraint on 'AuthInfo', fields ['aiidauser', 'computer']
        db.delete_unique(u'db_authinfo', ['aiidauser_id', 'computer_id'])

        # Removing unique constraint on 'Attribute', fields ['dbnode', 'key']
        db.delete_unique(u'db_attribute', ['dbnode_id', 'key'])

        # Removing unique constraint on 'Link', fields ['output', 'label']
        db.delete_unique(u'db_link', ['output_id', 'label'])

        # Removing unique constraint on 'Link', fields ['input', 'output']
        db.delete_unique(u'db_link', ['input_id', 'output_id'])

        # Deleting model 'DbNode'
        db.delete_table(u'db_dbnode')

        # Deleting model 'Link'
        db.delete_table(u'db_link')

        # Deleting model 'Path'
        db.delete_table(u'db_path')

        # Deleting model 'Attribute'
        db.delete_table(u'db_attribute')

        # Deleting model 'Group'
        db.delete_table(u'db_group')

        # Removing M2M table for field dbnodes on 'Group'
        db.delete_table(db.shorten_name(u'db_group_dbnodes'))

        # Deleting model 'DbComputer'
        db.delete_table(u'db_dbcomputer')

        # Deleting model 'AuthInfo'
        db.delete_table(u'db_authinfo')

        # Deleting model 'Comment'
        db.delete_table(u'db_comment')

        # Deleting model 'DbLock'
        db.delete_table(u'db_dblock')

        # Deleting model 'DbWorkflow'
        db.delete_table(u'db_dbworkflow')

        # Deleting model 'DbWorkflowData'
        db.delete_table(u'db_dbworkflowdata')

        # Deleting model 'DbWorkflowStep'
        db.delete_table(u'db_dbworkflowstep')

        # Removing M2M table for field calculations on 'DbWorkflowStep'
        db.delete_table(db.shorten_name(u'db_dbworkflowstep_calculations'))

        # Removing M2M table for field sub_workflows on 'DbWorkflowStep'
        db.delete_table(db.shorten_name(u'db_dbworkflowstep_sub_workflows'))


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
        u'db.attribute': {
            'Meta': {'unique_together': "(('dbnode', 'key'),)", 'object_name': 'Attribute'},
            'bval': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'datatype': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'dbnode': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attributes'", 'to': u"orm['db.DbNode']"}),
            'dval': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'fval': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ival': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'tval': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        u'db.authinfo': {
            'Meta': {'unique_together': "(('aiidauser', 'computer'),)", 'object_name': 'AuthInfo'},
            'aiidauser': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'auth_params': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.DbComputer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'db.comment': {
            'Meta': {'object_name': 'Comment'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dbnode': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['db.DbNode']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'db.dbcomputer': {
            'Meta': {'object_name': 'DbComputer'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'scheduler_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'transport_params': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'transport_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'workdir': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'db.dblock': {
            'Meta': {'object_name': 'DbLock'},
            'creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'timeout': ('django.db.models.fields.IntegerField', [], {})
        },
        u'db.dbnode': {
            'Meta': {'object_name': 'DbNode'},
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents'", 'symmetrical': 'False', 'through': u"orm['db.Path']", 'to': u"orm['db.DbNode']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.DbComputer']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'lastsyncedversion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'nodeversion': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'outputs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inputs'", 'symmetrical': 'False', 'through': u"orm['db.Link']", 'to': u"orm['db.DbNode']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'on_delete': 'models.PROTECT'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'db.dbworkflow': {
            'Meta': {'object_name': 'DbWorkflow'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.TextField', [], {}),
            'module_class': ('django.db.models.fields.TextField', [], {}),
            'report': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'script_md5': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'script_path': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'INITIALIZED'", 'max_length': '255'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'on_delete': 'models.PROTECT'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'db.dbworkflowdata': {
            'Meta': {'unique_together': "(('parent', 'name', 'data_type'),)", 'object_name': 'DbWorkflowData'},
            'aiida_obj': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.DbNode']", 'null': 'True', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.TextField', [], {'default': "'PARAMETER'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_value': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data'", 'to': u"orm['db.DbWorkflow']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.TextField', [], {'default': "'NONE'"})
        },
        u'db.dbworkflowstep': {
            'Meta': {'unique_together': "(('parent', 'name'),)", 'object_name': 'DbWorkflowStep'},
            'calculations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workflow_step'", 'symmetrical': 'False', 'to': u"orm['db.DbNode']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'nextcall': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'steps'", 'to': u"orm['db.DbWorkflow']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'CREATED'", 'max_length': '255'}),
            'sub_workflows': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parent_workflow_step'", 'symmetrical': 'False', 'to': u"orm['db.DbWorkflow']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'on_delete': 'models.PROTECT'})
        },
        u'db.group': {
            'Meta': {'object_name': 'Group'},
            'dbnodes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'to': u"orm['db.DbNode']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'db.link': {
            'Meta': {'unique_together': "(('input', 'output'), ('output', 'label'))", 'object_name': 'Link'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'output_links'", 'to': u"orm['db.DbNode']"}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'output': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'input_links'", 'to': u"orm['db.DbNode']"})
        },
        u'db.path': {
            'Meta': {'object_name': 'Path'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parent_paths'", 'to': u"orm['db.DbNode']"}),
            'depth': ('django.db.models.fields.IntegerField', [], {}),
            'direct_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'entry_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'exit_edge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_paths'", 'to': u"orm['db.DbNode']"})
        }
    }

    complete_apps = ['db']