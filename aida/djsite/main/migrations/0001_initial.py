# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calculation'
        db.create_table('main_calculation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Project'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcStatus'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcType'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'])),
        ))
        db.send_create_signal('main', ['Calculation'])

        # Adding M2M table for field instructures on 'Calculation'
        db.create_table('main_calculation_instructures', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('structure', models.ForeignKey(orm['main.structure'], null=False))
        ))
        db.create_unique('main_calculation_instructures', ['calculation_id', 'structure_id'])

        # Adding M2M table for field outstructures on 'Calculation'
        db.create_table('main_calculation_outstructures', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('structure', models.ForeignKey(orm['main.structure'], null=False))
        ))
        db.create_unique('main_calculation_outstructures', ['calculation_id', 'structure_id'])

        # Adding M2M table for field inpotentials on 'Calculation'
        db.create_table('main_calculation_inpotentials', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False))
        ))
        db.create_unique('main_calculation_inpotentials', ['calculation_id', 'potential_id'])

        # Adding M2M table for field outpotentials on 'Calculation'
        db.create_table('main_calculation_outpotentials', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False))
        ))
        db.create_unique('main_calculation_outpotentials', ['calculation_id', 'potential_id'])

        # Adding M2M table for field bases on 'Calculation'
        db.create_table('main_calculation_bases', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False))
        ))
        db.create_unique('main_calculation_bases', ['calculation_id', 'basis_id'])

        # Adding M2M table for field groups on 'Calculation'
        db.create_table('main_calculation_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('calcgroup', models.ForeignKey(orm['main.calcgroup'], null=False))
        ))
        db.create_unique('main_calculation_groups', ['calculation_id', 'calcgroup_id'])

        # Adding M2M table for field parents on 'Calculation'
        db.create_table('main_calculation_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_calculation', models.ForeignKey(orm['main.calculation'], null=False)),
            ('to_calculation', models.ForeignKey(orm['main.calculation'], null=False))
        ))
        db.create_unique('main_calculation_parents', ['from_calculation_id', 'to_calculation_id'])

        # Adding model 'CalcGroup'
        db.create_table('main_calcgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CalcGroup'])

        # Adding model 'CalcStatus'
        db.create_table('main_calcstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['CalcStatus'])

        # Adding model 'Project'
        db.create_table('main_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['Project'])

        # Adding model 'CalcType'
        db.create_table('main_calctype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['CalcType'])

        # Adding model 'CalcComment'
        db.create_table('main_calccomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcComment'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CalcComment'])

        # Adding model 'CalcAttrTxt'
        db.create_table('main_calcattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['CalcAttrTxt'])

        # Adding model 'CalcAttrNum'
        db.create_table('main_calcattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['CalcAttrNum'])

        # Adding model 'CalcAttrTxtVal'
        db.create_table('main_calcattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('calculation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Calculation'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['CalcAttrTxtVal'])

        # Adding unique constraint on 'CalcAttrTxtVal', fields ['calculation', 'attribute']
        db.create_unique('main_calcattrtxtval', ['calculation_id', 'attribute_id'])

        # Adding model 'CalcAttrNumVal'
        db.create_table('main_calcattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('calculation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Calculation'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcAttrNum'])),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['CalcAttrNumVal'])

        # Adding unique constraint on 'CalcAttrNumVal', fields ['calculation', 'attribute']
        db.create_unique('main_calcattrnumval', ['calculation_id', 'attribute_id'])

        # Adding model 'Computer'
        db.create_table('main_computer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('workdir', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('main', ['Computer'])

        # Adding model 'ComputerUsername'
        db.create_table('main_computerusername', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('remoteusername', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('main', ['ComputerUsername'])

        # Adding unique constraint on 'ComputerUsername', fields ['user', 'computer']
        db.create_unique('main_computerusername', ['user_id', 'computer_id'])

        # Adding model 'Code'
        db.create_table('main_code', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeStatus'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'], blank=True)),
        ))
        db.send_create_signal('main', ['Code'])

        # Adding M2M table for field groups on 'Code'
        db.create_table('main_code_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('code', models.ForeignKey(orm['main.code'], null=False)),
            ('codegroup', models.ForeignKey(orm['main.codegroup'], null=False))
        ))
        db.create_unique('main_code_groups', ['code_id', 'codegroup_id'])

        # Adding model 'CodeGroup'
        db.create_table('main_codegroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeGroup'])

        # Adding model 'CodeComment'
        db.create_table('main_codecomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeComment'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CodeComment'])

        # Adding model 'CodeStatus'
        db.create_table('main_codestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['CodeStatus'])

        # Adding model 'CodeType'
        db.create_table('main_codetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['CodeType'])

        # Adding model 'CodeAttrTxt'
        db.create_table('main_codeattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['CodeAttrTxt'])

        # Adding model 'CodeAttrNum'
        db.create_table('main_codeattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['CodeAttrNum'])

        # Adding model 'CodeAttrTxtVal'
        db.create_table('main_codeattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['CodeAttrTxtVal'])

        # Adding unique constraint on 'CodeAttrTxtVal', fields ['code', 'attribute']
        db.create_unique('main_codeattrtxtval', ['code_id', 'attribute_id'])

        # Adding model 'CodeAttrNumVal'
        db.create_table('main_codeattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeAttrNum'])),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['CodeAttrNumVal'])

        # Adding unique constraint on 'CodeAttrNumVal', fields ['code', 'attribute']
        db.create_unique('main_codeattrnumval', ['code_id', 'attribute_id'])

        # Adding model 'Element'
        db.create_table('main_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('symbol', self.gf('django.db.models.fields.CharField')(unique=True, max_length=3)),
            ('Z', self.gf('django.db.models.fields.IntegerField')(unique=True)),
        ))
        db.send_create_signal('main', ['Element'])

        # Adding M2M table for field groups on 'Element'
        db.create_table('main_element_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('element', models.ForeignKey(orm['main.element'], null=False)),
            ('elementgroup', models.ForeignKey(orm['main.elementgroup'], null=False))
        ))
        db.create_unique('main_element_groups', ['element_id', 'elementgroup_id'])

        # Adding model 'ElementAttrTxt'
        db.create_table('main_elementattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['ElementAttrTxt'])

        # Adding model 'ElementAttrNum'
        db.create_table('main_elementattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['ElementAttrNum'])

        # Adding model 'ElementGroup'
        db.create_table('main_elementgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['ElementGroup'])

        # Adding model 'ElementAttrTxtVal'
        db.create_table('main_elementattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('element', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Element'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['ElementAttrTxtVal'])

        # Adding unique constraint on 'ElementAttrTxtVal', fields ['element', 'attribute']
        db.create_unique('main_elementattrtxtval', ['element_id', 'attribute_id'])

        # Adding model 'ElementAttrNumVal'
        db.create_table('main_elementattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('element', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Element'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementAttrNum'])),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['ElementAttrNumVal'])

        # Adding unique constraint on 'ElementAttrNumVal', fields ['element', 'attribute']
        db.create_unique('main_elementattrnumval', ['element_id', 'attribute_id'])

        # Adding model 'Potential'
        db.create_table('main_potential', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotStatus'])),
        ))
        db.send_create_signal('main', ['Potential'])

        # Adding M2M table for field elements on 'Potential'
        db.create_table('main_potential_elements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_potential_elements', ['potential_id', 'element_id'])

        # Adding M2M table for field groups on 'Potential'
        db.create_table('main_potential_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False)),
            ('potgroup', models.ForeignKey(orm['main.potgroup'], null=False))
        ))
        db.create_unique('main_potential_groups', ['potential_id', 'potgroup_id'])

        # Adding model 'PotAttrTxt'
        db.create_table('main_potattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['PotAttrTxt'])

        # Adding model 'PotAttrNum'
        db.create_table('main_potattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['PotAttrNum'])

        # Adding model 'PotGroup'
        db.create_table('main_potgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['PotGroup'])

        # Adding model 'PotComment'
        db.create_table('main_potcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotComment'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['PotComment'])

        # Adding model 'PotStatus'
        db.create_table('main_potstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['PotStatus'])

        # Adding model 'PotType'
        db.create_table('main_pottype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['PotType'])

        # Adding model 'PotAttrTxtVal'
        db.create_table('main_potattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('potential', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Potential'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['PotAttrTxtVal'])

        # Adding unique constraint on 'PotAttrTxtVal', fields ['potential', 'attribute']
        db.create_unique('main_potattrtxtval', ['potential_id', 'attribute_id'])

        # Adding model 'PotAttrNumVal'
        db.create_table('main_potattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('potential', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Potential'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotAttrNum'])),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['PotAttrNumVal'])

        # Adding unique constraint on 'PotAttrNumVal', fields ['potential', 'attribute']
        db.create_unique('main_potattrnumval', ['potential_id', 'attribute_id'])

        # Adding model 'Basis'
        db.create_table('main_basis', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisStatus'])),
        ))
        db.send_create_signal('main', ['Basis'])

        # Adding M2M table for field elements on 'Basis'
        db.create_table('main_basis_elements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_basis_elements', ['basis_id', 'element_id'])

        # Adding M2M table for field groups on 'Basis'
        db.create_table('main_basis_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False)),
            ('basisgroup', models.ForeignKey(orm['main.basisgroup'], null=False))
        ))
        db.create_unique('main_basis_groups', ['basis_id', 'basisgroup_id'])

        # Adding model 'BasisAttrTxt'
        db.create_table('main_basisattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['BasisAttrTxt'])

        # Adding model 'BasisAttrNum'
        db.create_table('main_basisattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['BasisAttrNum'])

        # Adding model 'BasisGroup'
        db.create_table('main_basisgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['BasisGroup'])

        # Adding model 'BasisComment'
        db.create_table('main_basiscomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisComment'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['BasisComment'])

        # Adding model 'BasisStatus'
        db.create_table('main_basisstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['BasisStatus'])

        # Adding model 'BasisType'
        db.create_table('main_basistype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('main', ['BasisType'])

        # Adding model 'BasisAttrTxtVal'
        db.create_table('main_basisattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('basis', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Basis'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['BasisAttrTxtVal'])

        # Adding unique constraint on 'BasisAttrTxtVal', fields ['basis', 'attribute']
        db.create_unique('main_basisattrtxtval', ['basis_id', 'attribute_id'])

        # Adding model 'BasisAttrNumVal'
        db.create_table('main_basisattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('basis', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Basis'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisAttrNum'])),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['BasisAttrNumVal'])

        # Adding unique constraint on 'BasisAttrNumVal', fields ['basis', 'attribute']
        db.create_unique('main_basisattrnumval', ['basis_id', 'attribute_id'])

        # Adding model 'Structure'
        db.create_table('main_structure', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('formula', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('dim', self.gf('django.db.models.fields.IntegerField')(default=3)),
        ))
        db.send_create_signal('main', ['Structure'])

        # Adding M2M table for field elements on 'Structure'
        db.create_table('main_structure_elements', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('structure', models.ForeignKey(orm['main.structure'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_structure_elements', ['structure_id', 'element_id'])

        # Adding M2M table for field groups on 'Structure'
        db.create_table('main_structure_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('structure', models.ForeignKey(orm['main.structure'], null=False)),
            ('structgroup', models.ForeignKey(orm['main.structgroup'], null=False))
        ))
        db.create_unique('main_structure_groups', ['structure_id', 'structgroup_id'])

        # Adding model 'StructGroup'
        db.create_table('main_structgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StructGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['StructGroup'])

        # Adding model 'StructComment'
        db.create_table('main_structcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StructComment'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['StructComment'])

        # Adding model 'StructAttrTxt'
        db.create_table('main_structattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['StructAttrTxt'])

        # Adding model 'StructAttrNum'
        db.create_table('main_structattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('main', ['StructAttrNum'])

        # Adding model 'StructAttrTxtVal'
        db.create_table('main_structattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('structure', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Structure'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StructAttrTxt'])),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['StructAttrTxtVal'])

        # Adding unique constraint on 'StructAttrTxtVal', fields ['structure', 'attribute']
        db.create_unique('main_structattrtxtval', ['structure_id', 'attribute_id'])

        # Adding model 'StructAttrNumVal'
        db.create_table('main_structattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('structure', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Structure'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StructAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['StructAttrNumVal'])

        # Adding unique constraint on 'StructAttrNumVal', fields ['structure', 'attribute']
        db.create_unique('main_structattrnumval', ['structure_id', 'attribute_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'StructAttrNumVal', fields ['structure', 'attribute']
        db.delete_unique('main_structattrnumval', ['structure_id', 'attribute_id'])

        # Removing unique constraint on 'StructAttrTxtVal', fields ['structure', 'attribute']
        db.delete_unique('main_structattrtxtval', ['structure_id', 'attribute_id'])

        # Removing unique constraint on 'BasisAttrNumVal', fields ['basis', 'attribute']
        db.delete_unique('main_basisattrnumval', ['basis_id', 'attribute_id'])

        # Removing unique constraint on 'BasisAttrTxtVal', fields ['basis', 'attribute']
        db.delete_unique('main_basisattrtxtval', ['basis_id', 'attribute_id'])

        # Removing unique constraint on 'PotAttrNumVal', fields ['potential', 'attribute']
        db.delete_unique('main_potattrnumval', ['potential_id', 'attribute_id'])

        # Removing unique constraint on 'PotAttrTxtVal', fields ['potential', 'attribute']
        db.delete_unique('main_potattrtxtval', ['potential_id', 'attribute_id'])

        # Removing unique constraint on 'ElementAttrNumVal', fields ['element', 'attribute']
        db.delete_unique('main_elementattrnumval', ['element_id', 'attribute_id'])

        # Removing unique constraint on 'ElementAttrTxtVal', fields ['element', 'attribute']
        db.delete_unique('main_elementattrtxtval', ['element_id', 'attribute_id'])

        # Removing unique constraint on 'CodeAttrNumVal', fields ['code', 'attribute']
        db.delete_unique('main_codeattrnumval', ['code_id', 'attribute_id'])

        # Removing unique constraint on 'CodeAttrTxtVal', fields ['code', 'attribute']
        db.delete_unique('main_codeattrtxtval', ['code_id', 'attribute_id'])

        # Removing unique constraint on 'ComputerUsername', fields ['user', 'computer']
        db.delete_unique('main_computerusername', ['user_id', 'computer_id'])

        # Removing unique constraint on 'CalcAttrNumVal', fields ['calculation', 'attribute']
        db.delete_unique('main_calcattrnumval', ['calculation_id', 'attribute_id'])

        # Removing unique constraint on 'CalcAttrTxtVal', fields ['calculation', 'attribute']
        db.delete_unique('main_calcattrtxtval', ['calculation_id', 'attribute_id'])

        # Deleting model 'Calculation'
        db.delete_table('main_calculation')

        # Removing M2M table for field instructures on 'Calculation'
        db.delete_table('main_calculation_instructures')

        # Removing M2M table for field outstructures on 'Calculation'
        db.delete_table('main_calculation_outstructures')

        # Removing M2M table for field inpotentials on 'Calculation'
        db.delete_table('main_calculation_inpotentials')

        # Removing M2M table for field outpotentials on 'Calculation'
        db.delete_table('main_calculation_outpotentials')

        # Removing M2M table for field bases on 'Calculation'
        db.delete_table('main_calculation_bases')

        # Removing M2M table for field groups on 'Calculation'
        db.delete_table('main_calculation_groups')

        # Removing M2M table for field parents on 'Calculation'
        db.delete_table('main_calculation_parents')

        # Deleting model 'CalcGroup'
        db.delete_table('main_calcgroup')

        # Deleting model 'CalcStatus'
        db.delete_table('main_calcstatus')

        # Deleting model 'Project'
        db.delete_table('main_project')

        # Deleting model 'CalcType'
        db.delete_table('main_calctype')

        # Deleting model 'CalcComment'
        db.delete_table('main_calccomment')

        # Deleting model 'CalcAttrTxt'
        db.delete_table('main_calcattrtxt')

        # Deleting model 'CalcAttrNum'
        db.delete_table('main_calcattrnum')

        # Deleting model 'CalcAttrTxtVal'
        db.delete_table('main_calcattrtxtval')

        # Deleting model 'CalcAttrNumVal'
        db.delete_table('main_calcattrnumval')

        # Deleting model 'Computer'
        db.delete_table('main_computer')

        # Deleting model 'ComputerUsername'
        db.delete_table('main_computerusername')

        # Deleting model 'Code'
        db.delete_table('main_code')

        # Removing M2M table for field groups on 'Code'
        db.delete_table('main_code_groups')

        # Deleting model 'CodeGroup'
        db.delete_table('main_codegroup')

        # Deleting model 'CodeComment'
        db.delete_table('main_codecomment')

        # Deleting model 'CodeStatus'
        db.delete_table('main_codestatus')

        # Deleting model 'CodeType'
        db.delete_table('main_codetype')

        # Deleting model 'CodeAttrTxt'
        db.delete_table('main_codeattrtxt')

        # Deleting model 'CodeAttrNum'
        db.delete_table('main_codeattrnum')

        # Deleting model 'CodeAttrTxtVal'
        db.delete_table('main_codeattrtxtval')

        # Deleting model 'CodeAttrNumVal'
        db.delete_table('main_codeattrnumval')

        # Deleting model 'Element'
        db.delete_table('main_element')

        # Removing M2M table for field groups on 'Element'
        db.delete_table('main_element_groups')

        # Deleting model 'ElementAttrTxt'
        db.delete_table('main_elementattrtxt')

        # Deleting model 'ElementAttrNum'
        db.delete_table('main_elementattrnum')

        # Deleting model 'ElementGroup'
        db.delete_table('main_elementgroup')

        # Deleting model 'ElementAttrTxtVal'
        db.delete_table('main_elementattrtxtval')

        # Deleting model 'ElementAttrNumVal'
        db.delete_table('main_elementattrnumval')

        # Deleting model 'Potential'
        db.delete_table('main_potential')

        # Removing M2M table for field elements on 'Potential'
        db.delete_table('main_potential_elements')

        # Removing M2M table for field groups on 'Potential'
        db.delete_table('main_potential_groups')

        # Deleting model 'PotAttrTxt'
        db.delete_table('main_potattrtxt')

        # Deleting model 'PotAttrNum'
        db.delete_table('main_potattrnum')

        # Deleting model 'PotGroup'
        db.delete_table('main_potgroup')

        # Deleting model 'PotComment'
        db.delete_table('main_potcomment')

        # Deleting model 'PotStatus'
        db.delete_table('main_potstatus')

        # Deleting model 'PotType'
        db.delete_table('main_pottype')

        # Deleting model 'PotAttrTxtVal'
        db.delete_table('main_potattrtxtval')

        # Deleting model 'PotAttrNumVal'
        db.delete_table('main_potattrnumval')

        # Deleting model 'Basis'
        db.delete_table('main_basis')

        # Removing M2M table for field elements on 'Basis'
        db.delete_table('main_basis_elements')

        # Removing M2M table for field groups on 'Basis'
        db.delete_table('main_basis_groups')

        # Deleting model 'BasisAttrTxt'
        db.delete_table('main_basisattrtxt')

        # Deleting model 'BasisAttrNum'
        db.delete_table('main_basisattrnum')

        # Deleting model 'BasisGroup'
        db.delete_table('main_basisgroup')

        # Deleting model 'BasisComment'
        db.delete_table('main_basiscomment')

        # Deleting model 'BasisStatus'
        db.delete_table('main_basisstatus')

        # Deleting model 'BasisType'
        db.delete_table('main_basistype')

        # Deleting model 'BasisAttrTxtVal'
        db.delete_table('main_basisattrtxtval')

        # Deleting model 'BasisAttrNumVal'
        db.delete_table('main_basisattrnumval')

        # Deleting model 'Structure'
        db.delete_table('main_structure')

        # Removing M2M table for field elements on 'Structure'
        db.delete_table('main_structure_elements')

        # Removing M2M table for field groups on 'Structure'
        db.delete_table('main_structure_groups')

        # Deleting model 'StructGroup'
        db.delete_table('main_structgroup')

        # Deleting model 'StructComment'
        db.delete_table('main_structcomment')

        # Deleting model 'StructAttrTxt'
        db.delete_table('main_structattrtxt')

        # Deleting model 'StructAttrNum'
        db.delete_table('main_structattrnum')

        # Deleting model 'StructAttrTxtVal'
        db.delete_table('main_structattrtxtval')

        # Deleting model 'StructAttrNumVal'
        db.delete_table('main_structattrnumval')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.basis': {
            'Meta': {'object_name': 'Basis'},
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisAttrNum']", 'through': "orm['main.BasisAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisAttrTxt']", 'through': "orm['main.BasisAttrTxtVal']", 'symmetrical': 'False'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'elements': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisStatus']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisattrnum': {
            'Meta': {'object_name': 'BasisAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisattrnumval': {
            'Meta': {'unique_together': "(('basis', 'attribute'),)", 'object_name': 'BasisAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisAttrNum']"}),
            'basis': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Basis']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'main.basisattrtxt': {
            'Meta': {'object_name': 'BasisAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisattrtxtval': {
            'Meta': {'unique_together': "(('basis', 'attribute'),)", 'object_name': 'BasisAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisAttrTxt']"}),
            'basis': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Basis']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.basiscomment': {
            'Meta': {'object_name': 'BasisComment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisComment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisgroup': {
            'Meta': {'object_name': 'BasisGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisstatus': {
            'Meta': {'object_name': 'BasisStatus'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basistype': {
            'Meta': {'object_name': 'BasisType'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcattrnum': {
            'Meta': {'object_name': 'CalcAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcattrnumval': {
            'Meta': {'unique_together': "(('calculation', 'attribute'),)", 'object_name': 'CalcAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcAttrNum']"}),
            'calculation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Calculation']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'main.calcattrtxt': {
            'Meta': {'object_name': 'CalcAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcattrtxtval': {
            'Meta': {'unique_together': "(('calculation', 'attribute'),)", 'object_name': 'CalcAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcAttrTxt']"}),
            'calculation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Calculation']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.calccomment': {
            'Meta': {'object_name': 'CalcComment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcComment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcgroup': {
            'Meta': {'object_name': 'CalcGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcstatus': {
            'Meta': {'object_name': 'CalcStatus'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calctype': {
            'Meta': {'object_name': 'CalcType'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calculation': {
            'Meta': {'object_name': 'Calculation'},
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcAttrNum']", 'through': "orm['main.CalcAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcAttrTxt']", 'through': "orm['main.CalcAttrTxtVal']", 'symmetrical': 'False'}),
            'bases': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Basis']", 'symmetrical': 'False', 'blank': 'True'}),
            'code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inpotentials': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'incalculations'", 'blank': 'True', 'to': "orm['main.Potential']"}),
            'instructures': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'incalculations'", 'blank': 'True', 'to': "orm['main.Structure']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'outpotentials': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalculations'", 'blank': 'True', 'to': "orm['main.Potential']"}),
            'outstructures': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalculations'", 'blank': 'True', 'to': "orm['main.Structure']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'children'", 'blank': 'True', 'to': "orm['main.Calculation']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcStatus']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.code': {
            'Meta': {'object_name': 'Code'},
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeAttrNum']", 'through': "orm['main.CodeAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeAttrTxt']", 'through': "orm['main.CodeAttrTxtVal']", 'symmetrical': 'False'}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']", 'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeStatus']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.codeattrnum': {
            'Meta': {'object_name': 'CodeAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codeattrnumval': {
            'Meta': {'unique_together': "(('code', 'attribute'),)", 'object_name': 'CodeAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeAttrNum']"}),
            'code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'main.codeattrtxt': {
            'Meta': {'object_name': 'CodeAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codeattrtxtval': {
            'Meta': {'unique_together': "(('code', 'attribute'),)", 'object_name': 'CodeAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeAttrTxt']"}),
            'code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.codecomment': {
            'Meta': {'object_name': 'CodeComment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeComment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codegroup': {
            'Meta': {'object_name': 'CodeGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codestatus': {
            'Meta': {'object_name': 'CodeStatus'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codetype': {
            'Meta': {'object_name': 'CodeType'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.computer': {
            'Meta': {'object_name': 'Computer'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'workdir': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.computerusername': {
            'Meta': {'unique_together': "(('user', 'computer'),)", 'object_name': 'ComputerUsername'},
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remoteusername': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'main.element': {
            'Meta': {'object_name': 'Element'},
            'Z': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementAttrNum']", 'through': "orm['main.ElementAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementAttrTxt']", 'through': "orm['main.ElementAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'symbol': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.elementattrnum': {
            'Meta': {'object_name': 'ElementAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.elementattrnumval': {
            'Meta': {'unique_together': "(('element', 'attribute'),)", 'object_name': 'ElementAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementAttrNum']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Element']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'main.elementattrtxt': {
            'Meta': {'object_name': 'ElementAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.elementattrtxtval': {
            'Meta': {'unique_together': "(('element', 'attribute'),)", 'object_name': 'ElementAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementAttrTxt']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Element']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.elementgroup': {
            'Meta': {'object_name': 'ElementGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potattrnum': {
            'Meta': {'object_name': 'PotAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potattrnumval': {
            'Meta': {'unique_together': "(('potential', 'attribute'),)", 'object_name': 'PotAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotAttrNum']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'potential': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Potential']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'main.potattrtxt': {
            'Meta': {'object_name': 'PotAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potattrtxtval': {
            'Meta': {'unique_together': "(('potential', 'attribute'),)", 'object_name': 'PotAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotAttrTxt']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'potential': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Potential']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.potcomment': {
            'Meta': {'object_name': 'PotComment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotComment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potential': {
            'Meta': {'object_name': 'Potential'},
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotAttrNum']", 'through': "orm['main.PotAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotAttrTxt']", 'through': "orm['main.PotAttrTxtVal']", 'symmetrical': 'False'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'elements': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotStatus']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potgroup': {
            'Meta': {'object_name': 'PotGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potstatus': {
            'Meta': {'object_name': 'PotStatus'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.pottype': {
            'Meta': {'object_name': 'PotType'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.structattrnum': {
            'Meta': {'object_name': 'StructAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.structattrnumval': {
            'Meta': {'unique_together': "(('structure', 'attribute'),)", 'object_name': 'StructAttrNumVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StructAttrNum']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'structure': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Structure']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.structattrtxt': {
            'Meta': {'object_name': 'StructAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.structattrtxtval': {
            'Meta': {'unique_together': "(('structure', 'attribute'),)", 'object_name': 'StructAttrTxtVal'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StructAttrTxt']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'structure': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Structure']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.structcomment': {
            'Meta': {'object_name': 'StructComment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StructComment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.structgroup': {
            'Meta': {'object_name': 'StructGroup'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StructGroup']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.structure': {
            'Meta': {'object_name': 'Structure'},
            'attrsnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StructAttrNum']", 'through': "orm['main.StructAttrNumVal']", 'symmetrical': 'False'}),
            'attrstxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StructAttrTxt']", 'through': "orm['main.StructAttrTxtVal']", 'symmetrical': 'False'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dim': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'elements': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'formula': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StructGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['main']