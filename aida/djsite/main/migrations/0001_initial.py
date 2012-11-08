# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calc'
        db.create_table('aidadb_calc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Code'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Project'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcStatus'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcType'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Computer'])),
        ))
        db.send_create_signal('aidadb', ['Calc'])

        # Adding M2M table for field inpstruc on 'Calc'
        db.create_table('aidadb_calc_inpstruc', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('struc', models.ForeignKey(orm['aidadb.struc'], null=False))
        ))
        db.create_unique('aidadb_calc_inpstruc', ['calc_id', 'struc_id'])

        # Adding M2M table for field outstruc on 'Calc'
        db.create_table('aidadb_calc_outstruc', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('struc', models.ForeignKey(orm['aidadb.struc'], null=False))
        ))
        db.create_unique('aidadb_calc_outstruc', ['calc_id', 'struc_id'])

        # Adding M2M table for field inppot on 'Calc'
        db.create_table('aidadb_calc_inppot', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('potential', models.ForeignKey(orm['aidadb.potential'], null=False))
        ))
        db.create_unique('aidadb_calc_inppot', ['calc_id', 'potential_id'])

        # Adding M2M table for field outpot on 'Calc'
        db.create_table('aidadb_calc_outpot', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('potential', models.ForeignKey(orm['aidadb.potential'], null=False))
        ))
        db.create_unique('aidadb_calc_outpot', ['calc_id', 'potential_id'])

        # Adding M2M table for field basis on 'Calc'
        db.create_table('aidadb_calc_basis', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('basis', models.ForeignKey(orm['aidadb.basis'], null=False))
        ))
        db.create_unique('aidadb_calc_basis', ['calc_id', 'basis_id'])

        # Adding M2M table for field group on 'Calc'
        db.create_table('aidadb_calc_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('calcgroup', models.ForeignKey(orm['aidadb.calcgroup'], null=False))
        ))
        db.create_unique('aidadb_calc_group', ['calc_id', 'calcgroup_id'])

        # Adding M2M table for field parent on 'Calc'
        db.create_table('aidadb_calc_parent', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_calc', models.ForeignKey(orm['aidadb.calc'], null=False)),
            ('to_calc', models.ForeignKey(orm['aidadb.calc'], null=False))
        ))
        db.create_unique('aidadb_calc_parent', ['from_calc_id', 'to_calc_id'])

        # Adding model 'CalcGroup'
        db.create_table('aidadb_calcgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcGroup'])

        # Adding model 'CalcStatus'
        db.create_table('aidadb_calcstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcStatus'])

        # Adding model 'Project'
        db.create_table('aidadb_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['Project'])

        # Adding model 'CalcType'
        db.create_table('aidadb_calctype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcType'])

        # Adding model 'CalcComment'
        db.create_table('aidadb_calccomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcComment'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcComment'])

        # Adding model 'CalcAttrTxt'
        db.create_table('aidadb_calcattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['CalcAttrTxt'])

        # Adding model 'CalcAttrNum'
        db.create_table('aidadb_calcattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['CalcAttrNum'])

        # Adding model 'CalcAttrTxtVal'
        db.create_table('aidadb_calcattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Calc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcAttrTxtVal'])

        # Adding unique constraint on 'CalcAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_calcattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'CalcAttrNumVal'
        db.create_table('aidadb_calcattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Calc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CalcAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CalcAttrNumVal'])

        # Adding unique constraint on 'CalcAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_calcattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Computer'
        db.create_table('aidadb_computer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('workdir', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('aidadb', ['Computer'])

        # Adding model 'ComputerUsername'
        db.create_table('aidadb_computerusername', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Computer'])),
            ('aidauser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='computerusername_remoteuser_set', to=orm['auth.User'])),
            ('remoteusername', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('aidadb', ['ComputerUsername'])

        # Adding unique constraint on 'ComputerUsername', fields ['aidauser', 'computer']
        db.create_unique('aidadb_computerusername', ['aidauser_id', 'computer_id'])

        # Adding model 'Code'
        db.create_table('aidadb_code', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeStatus'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Computer'], blank=True)),
        ))
        db.send_create_signal('aidadb', ['Code'])

        # Adding M2M table for field group on 'Code'
        db.create_table('aidadb_code_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('code', models.ForeignKey(orm['aidadb.code'], null=False)),
            ('codegroup', models.ForeignKey(orm['aidadb.codegroup'], null=False))
        ))
        db.create_unique('aidadb_code_group', ['code_id', 'codegroup_id'])

        # Adding model 'CodeGroup'
        db.create_table('aidadb_codegroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeGroup'])

        # Adding model 'CodeComment'
        db.create_table('aidadb_codecomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeComment'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeComment'])

        # Adding model 'CodeStatus'
        db.create_table('aidadb_codestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeStatus'])

        # Adding model 'CodeType'
        db.create_table('aidadb_codetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeType'])

        # Adding model 'CodeAttrTxt'
        db.create_table('aidadb_codeattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeAttrTxt'])

        # Adding model 'CodeAttrNum'
        db.create_table('aidadb_codeattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeAttrNum'])

        # Adding model 'CodeAttrTxtVal'
        db.create_table('aidadb_codeattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Code'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeAttrTxtVal'])

        # Adding unique constraint on 'CodeAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_codeattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'CodeAttrNumVal'
        db.create_table('aidadb_codeattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Code'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.CodeAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['CodeAttrNumVal'])

        # Adding unique constraint on 'CodeAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_codeattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Element'
        db.create_table('aidadb_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('Z', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('aidadb', ['Element'])

        # Adding M2M table for field group on 'Element'
        db.create_table('aidadb_element_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('element', models.ForeignKey(orm['aidadb.element'], null=False)),
            ('elementgroup', models.ForeignKey(orm['aidadb.elementgroup'], null=False))
        ))
        db.create_unique('aidadb_element_group', ['element_id', 'elementgroup_id'])

        # Adding model 'ElementAttrTxt'
        db.create_table('aidadb_elementattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['ElementAttrTxt'])

        # Adding model 'ElementAttrNum'
        db.create_table('aidadb_elementattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['ElementAttrNum'])

        # Adding model 'ElementGroup'
        db.create_table('aidadb_elementgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.ElementGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['ElementGroup'])

        # Adding model 'ElementAttrTxtVal'
        db.create_table('aidadb_elementattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Element'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.ElementAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['ElementAttrTxtVal'])

        # Adding unique constraint on 'ElementAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_elementattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'ElementAttrNumVal'
        db.create_table('aidadb_elementattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Element'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.ElementAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['ElementAttrNumVal'])

        # Adding unique constraint on 'ElementAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_elementattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Potential'
        db.create_table('aidadb_potential', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialStatus'])),
        ))
        db.send_create_signal('aidadb', ['Potential'])

        # Adding M2M table for field element on 'Potential'
        db.create_table('aidadb_potential_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['aidadb.potential'], null=False)),
            ('element', models.ForeignKey(orm['aidadb.element'], null=False))
        ))
        db.create_unique('aidadb_potential_element', ['potential_id', 'element_id'])

        # Adding M2M table for field group on 'Potential'
        db.create_table('aidadb_potential_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['aidadb.potential'], null=False)),
            ('potentialgroup', models.ForeignKey(orm['aidadb.potentialgroup'], null=False))
        ))
        db.create_unique('aidadb_potential_group', ['potential_id', 'potentialgroup_id'])

        # Adding model 'PotentialAttrTxt'
        db.create_table('aidadb_potentialattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialAttrTxt'])

        # Adding model 'PotentialAttrNum'
        db.create_table('aidadb_potentialattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialAttrNum'])

        # Adding model 'PotentialGroup'
        db.create_table('aidadb_potentialgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialGroup'])

        # Adding model 'PotentialComment'
        db.create_table('aidadb_potentialcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialComment'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialComment'])

        # Adding model 'PotentialStatus'
        db.create_table('aidadb_potentialstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialStatus'])

        # Adding model 'PotentialType'
        db.create_table('aidadb_potentialtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialType'])

        # Adding model 'PotentialAttrTxtVal'
        db.create_table('aidadb_potentialattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Potential'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialAttrTxtVal'])

        # Adding unique constraint on 'PotentialAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_potentialattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'PotentialAttrNumVal'
        db.create_table('aidadb_potentialattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Potential'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.PotentialAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['PotentialAttrNumVal'])

        # Adding unique constraint on 'PotentialAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_potentialattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Basis'
        db.create_table('aidadb_basis', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisStatus'])),
        ))
        db.send_create_signal('aidadb', ['Basis'])

        # Adding M2M table for field element on 'Basis'
        db.create_table('aidadb_basis_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['aidadb.basis'], null=False)),
            ('element', models.ForeignKey(orm['aidadb.element'], null=False))
        ))
        db.create_unique('aidadb_basis_element', ['basis_id', 'element_id'])

        # Adding M2M table for field group on 'Basis'
        db.create_table('aidadb_basis_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['aidadb.basis'], null=False)),
            ('basisgroup', models.ForeignKey(orm['aidadb.basisgroup'], null=False))
        ))
        db.create_unique('aidadb_basis_group', ['basis_id', 'basisgroup_id'])

        # Adding model 'BasisAttrTxt'
        db.create_table('aidadb_basisattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['BasisAttrTxt'])

        # Adding model 'BasisAttrNum'
        db.create_table('aidadb_basisattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('isinput', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('aidadb', ['BasisAttrNum'])

        # Adding model 'BasisGroup'
        db.create_table('aidadb_basisgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisGroup'])

        # Adding model 'BasisComment'
        db.create_table('aidadb_basiscomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisComment'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisComment'])

        # Adding model 'BasisStatus'
        db.create_table('aidadb_basisstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisStatus'])

        # Adding model 'BasisType'
        db.create_table('aidadb_basistype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisType'])

        # Adding model 'BasisAttrTxtVal'
        db.create_table('aidadb_basisattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Basis'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisAttrTxtVal'])

        # Adding unique constraint on 'BasisAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_basisattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'BasisAttrNumVal'
        db.create_table('aidadb_basisattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Basis'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.BasisAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['BasisAttrNumVal'])

        # Adding unique constraint on 'BasisAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_basisattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Struc'
        db.create_table('aidadb_struc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('formula', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('dim', self.gf('django.db.models.fields.IntegerField')()),
            ('detail', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('aidadb', ['Struc'])

        # Adding M2M table for field element on 'Struc'
        db.create_table('aidadb_struc_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('struc', models.ForeignKey(orm['aidadb.struc'], null=False)),
            ('element', models.ForeignKey(orm['aidadb.element'], null=False))
        ))
        db.create_unique('aidadb_struc_element', ['struc_id', 'element_id'])

        # Adding M2M table for field group on 'Struc'
        db.create_table('aidadb_struc_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('struc', models.ForeignKey(orm['aidadb.struc'], null=False)),
            ('strucgroup', models.ForeignKey(orm['aidadb.strucgroup'], null=False))
        ))
        db.create_unique('aidadb_struc_group', ['struc_id', 'strucgroup_id'])

        # Adding model 'StrucGroup'
        db.create_table('aidadb_strucgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.StrucGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucGroup'])

        # Adding model 'StrucComment'
        db.create_table('aidadb_struccomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.StrucComment'], null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucComment'])

        # Adding model 'StrucAttrTxt'
        db.create_table('aidadb_strucattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucAttrTxt'])

        # Adding model 'StrucAttrNum'
        db.create_table('aidadb_strucattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucAttrNum'])

        # Adding model 'StrucAttrTxtVal'
        db.create_table('aidadb_strucattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Struc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.StrucAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucAttrTxtVal'])

        # Adding unique constraint on 'StrucAttrTxtVal', fields ['item', 'attr']
        db.create_unique('aidadb_strucattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'StrucAttrNumVal'
        db.create_table('aidadb_strucattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.Struc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['aidadb.StrucAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('aidadb', ['StrucAttrNumVal'])

        # Adding unique constraint on 'StrucAttrNumVal', fields ['item', 'attr']
        db.create_unique('aidadb_strucattrnumval', ['item_id', 'attr_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'StrucAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_strucattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'StrucAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_strucattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'BasisAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_basisattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'BasisAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_basisattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'PotentialAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_potentialattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'PotentialAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_potentialattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ElementAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_elementattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ElementAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_elementattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CodeAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_codeattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CodeAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_codeattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ComputerUsername', fields ['aidauser', 'computer']
        db.delete_unique('aidadb_computerusername', ['aidauser_id', 'computer_id'])

        # Removing unique constraint on 'CalcAttrNumVal', fields ['item', 'attr']
        db.delete_unique('aidadb_calcattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CalcAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('aidadb_calcattrtxtval', ['item_id', 'attr_id'])

        # Deleting model 'Calc'
        db.delete_table('aidadb_calc')

        # Removing M2M table for field inpstruc on 'Calc'
        db.delete_table('aidadb_calc_inpstruc')

        # Removing M2M table for field outstruc on 'Calc'
        db.delete_table('aidadb_calc_outstruc')

        # Removing M2M table for field inppot on 'Calc'
        db.delete_table('aidadb_calc_inppot')

        # Removing M2M table for field outpot on 'Calc'
        db.delete_table('aidadb_calc_outpot')

        # Removing M2M table for field basis on 'Calc'
        db.delete_table('aidadb_calc_basis')

        # Removing M2M table for field group on 'Calc'
        db.delete_table('aidadb_calc_group')

        # Removing M2M table for field parent on 'Calc'
        db.delete_table('aidadb_calc_parent')

        # Deleting model 'CalcGroup'
        db.delete_table('aidadb_calcgroup')

        # Deleting model 'CalcStatus'
        db.delete_table('aidadb_calcstatus')

        # Deleting model 'Project'
        db.delete_table('aidadb_project')

        # Deleting model 'CalcType'
        db.delete_table('aidadb_calctype')

        # Deleting model 'CalcComment'
        db.delete_table('aidadb_calccomment')

        # Deleting model 'CalcAttrTxt'
        db.delete_table('aidadb_calcattrtxt')

        # Deleting model 'CalcAttrNum'
        db.delete_table('aidadb_calcattrnum')

        # Deleting model 'CalcAttrTxtVal'
        db.delete_table('aidadb_calcattrtxtval')

        # Deleting model 'CalcAttrNumVal'
        db.delete_table('aidadb_calcattrnumval')

        # Deleting model 'Computer'
        db.delete_table('aidadb_computer')

        # Deleting model 'ComputerUsername'
        db.delete_table('aidadb_computerusername')

        # Deleting model 'Code'
        db.delete_table('aidadb_code')

        # Removing M2M table for field group on 'Code'
        db.delete_table('aidadb_code_group')

        # Deleting model 'CodeGroup'
        db.delete_table('aidadb_codegroup')

        # Deleting model 'CodeComment'
        db.delete_table('aidadb_codecomment')

        # Deleting model 'CodeStatus'
        db.delete_table('aidadb_codestatus')

        # Deleting model 'CodeType'
        db.delete_table('aidadb_codetype')

        # Deleting model 'CodeAttrTxt'
        db.delete_table('aidadb_codeattrtxt')

        # Deleting model 'CodeAttrNum'
        db.delete_table('aidadb_codeattrnum')

        # Deleting model 'CodeAttrTxtVal'
        db.delete_table('aidadb_codeattrtxtval')

        # Deleting model 'CodeAttrNumVal'
        db.delete_table('aidadb_codeattrnumval')

        # Deleting model 'Element'
        db.delete_table('aidadb_element')

        # Removing M2M table for field group on 'Element'
        db.delete_table('aidadb_element_group')

        # Deleting model 'ElementAttrTxt'
        db.delete_table('aidadb_elementattrtxt')

        # Deleting model 'ElementAttrNum'
        db.delete_table('aidadb_elementattrnum')

        # Deleting model 'ElementGroup'
        db.delete_table('aidadb_elementgroup')

        # Deleting model 'ElementAttrTxtVal'
        db.delete_table('aidadb_elementattrtxtval')

        # Deleting model 'ElementAttrNumVal'
        db.delete_table('aidadb_elementattrnumval')

        # Deleting model 'Potential'
        db.delete_table('aidadb_potential')

        # Removing M2M table for field element on 'Potential'
        db.delete_table('aidadb_potential_element')

        # Removing M2M table for field group on 'Potential'
        db.delete_table('aidadb_potential_group')

        # Deleting model 'PotentialAttrTxt'
        db.delete_table('aidadb_potentialattrtxt')

        # Deleting model 'PotentialAttrNum'
        db.delete_table('aidadb_potentialattrnum')

        # Deleting model 'PotentialGroup'
        db.delete_table('aidadb_potentialgroup')

        # Deleting model 'PotentialComment'
        db.delete_table('aidadb_potentialcomment')

        # Deleting model 'PotentialStatus'
        db.delete_table('aidadb_potentialstatus')

        # Deleting model 'PotentialType'
        db.delete_table('aidadb_potentialtype')

        # Deleting model 'PotentialAttrTxtVal'
        db.delete_table('aidadb_potentialattrtxtval')

        # Deleting model 'PotentialAttrNumVal'
        db.delete_table('aidadb_potentialattrnumval')

        # Deleting model 'Basis'
        db.delete_table('aidadb_basis')

        # Removing M2M table for field element on 'Basis'
        db.delete_table('aidadb_basis_element')

        # Removing M2M table for field group on 'Basis'
        db.delete_table('aidadb_basis_group')

        # Deleting model 'BasisAttrTxt'
        db.delete_table('aidadb_basisattrtxt')

        # Deleting model 'BasisAttrNum'
        db.delete_table('aidadb_basisattrnum')

        # Deleting model 'BasisGroup'
        db.delete_table('aidadb_basisgroup')

        # Deleting model 'BasisComment'
        db.delete_table('aidadb_basiscomment')

        # Deleting model 'BasisStatus'
        db.delete_table('aidadb_basisstatus')

        # Deleting model 'BasisType'
        db.delete_table('aidadb_basistype')

        # Deleting model 'BasisAttrTxtVal'
        db.delete_table('aidadb_basisattrtxtval')

        # Deleting model 'BasisAttrNumVal'
        db.delete_table('aidadb_basisattrnumval')

        # Deleting model 'Struc'
        db.delete_table('aidadb_struc')

        # Removing M2M table for field element on 'Struc'
        db.delete_table('aidadb_struc_element')

        # Removing M2M table for field group on 'Struc'
        db.delete_table('aidadb_struc_group')

        # Deleting model 'StrucGroup'
        db.delete_table('aidadb_strucgroup')

        # Deleting model 'StrucComment'
        db.delete_table('aidadb_struccomment')

        # Deleting model 'StrucAttrTxt'
        db.delete_table('aidadb_strucattrtxt')

        # Deleting model 'StrucAttrNum'
        db.delete_table('aidadb_strucattrnum')

        # Deleting model 'StrucAttrTxtVal'
        db.delete_table('aidadb_strucattrtxtval')

        # Deleting model 'StrucAttrNumVal'
        db.delete_table('aidadb_strucattrnumval')


    models = {
        'aidadb.basis': {
            'Meta': {'object_name': 'Basis'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.BasisAttrNum']", 'through': "orm['aidadb.BasisAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.BasisAttrTxt']", 'through': "orm['aidadb.BasisAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.Element']", 'symmetrical': 'False'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.BasisGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basisattrnum': {
            'Meta': {'object_name': 'BasisAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basisattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'BasisAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Basis']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.basisattrtxt': {
            'Meta': {'object_name': 'BasisAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basisattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'BasisAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Basis']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.basiscomment': {
            'Meta': {'object_name': 'BasisComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basisgroup': {
            'Meta': {'object_name': 'BasisGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.BasisGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basisstatus': {
            'Meta': {'object_name': 'BasisStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.basistype': {
            'Meta': {'object_name': 'BasisType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calc': {
            'Meta': {'object_name': 'Calc'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CalcAttrNum']", 'through': "orm['aidadb.CalcAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CalcAttrTxt']", 'through': "orm['aidadb.CalcAttrTxtVal']", 'symmetrical': 'False'}),
            'basis': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.Basis']", 'symmetrical': 'False', 'blank': 'True'}),
            'code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Code']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Computer']"}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CalcGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inppot': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inpcalc'", 'blank': 'True', 'to': "orm['aidadb.Potential']"}),
            'inpstruc': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inpcalc'", 'blank': 'True', 'to': "orm['aidadb.Struc']"}),
            'outpot': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalc'", 'blank': 'True', 'to': "orm['aidadb.Potential']"}),
            'outstruc': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalc'", 'blank': 'True', 'to': "orm['aidadb.Struc']"}),
            'parent': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'child'", 'blank': 'True', 'to': "orm['aidadb.Calc']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Project']"}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calcattrnum': {
            'Meta': {'object_name': 'CalcAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calcattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CalcAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Calc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.calcattrtxt': {
            'Meta': {'object_name': 'CalcAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calcattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CalcAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Calc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.calccomment': {
            'Meta': {'object_name': 'CalcComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calcgroup': {
            'Meta': {'object_name': 'CalcGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CalcGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calcstatus': {
            'Meta': {'object_name': 'CalcStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.calctype': {
            'Meta': {'object_name': 'CalcType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.code': {
            'Meta': {'object_name': 'Code'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CodeAttrNum']", 'through': "orm['aidadb.CodeAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CodeAttrTxt']", 'through': "orm['aidadb.CodeAttrTxtVal']", 'symmetrical': 'False'}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Computer']", 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.CodeGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codeattrnum': {
            'Meta': {'object_name': 'CodeAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codeattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CodeAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Code']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.codeattrtxt': {
            'Meta': {'object_name': 'CodeAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codeattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CodeAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Code']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.codecomment': {
            'Meta': {'object_name': 'CodeComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codegroup': {
            'Meta': {'object_name': 'CodeGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.CodeGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codestatus': {
            'Meta': {'object_name': 'CodeStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.codetype': {
            'Meta': {'object_name': 'CodeType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.computer': {
            'Meta': {'object_name': 'Computer'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'workdir': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'aidadb.computerusername': {
            'Meta': {'unique_together': "(('aidauser', 'computer'),)", 'object_name': 'ComputerUsername'},
            'aidauser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'computerusername_remoteuser_set'", 'to': "orm['auth.User']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Computer']"}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'remoteusername': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.element': {
            'Meta': {'object_name': 'Element'},
            'Z': ('django.db.models.fields.IntegerField', [], {}),
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.ElementAttrNum']", 'through': "orm['aidadb.ElementAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.ElementAttrTxt']", 'through': "orm['aidadb.ElementAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.ElementGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.elementattrnum': {
            'Meta': {'object_name': 'ElementAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.elementattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'ElementAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.ElementAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Element']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.elementattrtxt': {
            'Meta': {'object_name': 'ElementAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.elementattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'ElementAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.ElementAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Element']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.elementgroup': {
            'Meta': {'object_name': 'ElementGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.ElementGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potential': {
            'Meta': {'object_name': 'Potential'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.PotentialAttrNum']", 'through': "orm['aidadb.PotentialAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.PotentialAttrTxt']", 'through': "orm['aidadb.PotentialAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.Element']", 'symmetrical': 'False'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.PotentialGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialattrnum': {
            'Meta': {'object_name': 'PotentialAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'PotentialAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Potential']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.potentialattrtxt': {
            'Meta': {'object_name': 'PotentialAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isinput': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'PotentialAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Potential']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.potentialcomment': {
            'Meta': {'object_name': 'PotentialComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialgroup': {
            'Meta': {'object_name': 'PotentialGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.PotentialGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialstatus': {
            'Meta': {'object_name': 'PotentialStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.potentialtype': {
            'Meta': {'object_name': 'PotentialType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.project': {
            'Meta': {'object_name': 'Project'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.struc': {
            'Meta': {'object_name': 'Struc'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.StrucAttrNum']", 'through': "orm['aidadb.StrucAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.StrucAttrTxt']", 'through': "orm['aidadb.StrucAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'detail': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dim': ('django.db.models.fields.IntegerField', [], {}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.Element']", 'symmetrical': 'False'}),
            'formula': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['aidadb.StrucGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.strucattrnum': {
            'Meta': {'object_name': 'StrucAttrNum'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.strucattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'StrucAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.StrucAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Struc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'aidadb.strucattrtxt': {
            'Meta': {'object_name': 'StrucAttrTxt'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.strucattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'StrucAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.StrucAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.Struc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'aidadb.struccomment': {
            'Meta': {'object_name': 'StrucComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.StrucComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'aidadb.strucgroup': {
            'Meta': {'object_name': 'StrucGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['aidadb.StrucGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
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
        }
    }

    complete_apps = ['aidadb']