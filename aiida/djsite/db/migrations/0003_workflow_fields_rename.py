# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Column renames
        db.rename_column(u'db_dbworkflow', 'status', 'state')
        db.rename_column(u'db_dbworkflow', 'time', 'ctime')


        # Adding field 'DbWorkflow.mtime'; just a random date,
        # Then it will be set by auto_now
        db.add_column(u'db_dbworkflow', 'mtime',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2013, 12, 13, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'DbWorkflow.label'
        db.add_column(u'db_dbworkflow', 'label',
                      self.gf('django.db.models.fields.CharField')(db_index=True, default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'DbWorkflow.description'
        db.add_column(u'db_dbworkflow', 'description',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'DbWorkflow.nodeversion'
        db.add_column(u'db_dbworkflow', 'nodeversion',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'DbWorkflow.lastsyncedversion'
        db.add_column(u'db_dbworkflow', 'lastsyncedversion',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)



    def backwards(self, orm):
        # Column renames
        db.rename_column(u'db_dbworkflow', 'state', 'status')
        db.rename_column(u'db_dbworkflow', 'ctime', 'time')

        # Deleting field 'DbWorkflow.mtime'
        db.delete_column(u'db_dbworkflow', 'mtime')

        # Deleting field 'DbWorkflow.label'
        db.delete_column(u'db_dbworkflow', 'label')

        # Deleting field 'DbWorkflow.description'
        db.delete_column(u'db_dbworkflow', 'description')

        # Deleting field 'DbWorkflow.nodeversion'
        db.delete_column(u'db_dbworkflow', 'nodeversion')

        # Deleting field 'DbWorkflow.lastsyncedversion'
        db.delete_column(u'db_dbworkflow', 'lastsyncedversion')


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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'lastsyncedversion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'module': ('django.db.models.fields.TextField', [], {}),
            'module_class': ('django.db.models.fields.TextField', [], {}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'nodeversion': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'report': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'script_md5': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'script_path': ('django.db.models.fields.TextField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'INITIALIZED'", 'max_length': '255'}),
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
