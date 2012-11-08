# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calc'
        db.create_table('main_calc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Project'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcStatus'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcType'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'])),
        ))
        db.send_create_signal('main', ['Calc'])

        # Adding M2M table for field inpstruc on 'Calc'
        db.create_table('main_calc_inpstruc', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('struc', models.ForeignKey(orm['main.struc'], null=False))
        ))
        db.create_unique('main_calc_inpstruc', ['calc_id', 'struc_id'])

        # Adding M2M table for field outstruc on 'Calc'
        db.create_table('main_calc_outstruc', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('struc', models.ForeignKey(orm['main.struc'], null=False))
        ))
        db.create_unique('main_calc_outstruc', ['calc_id', 'struc_id'])

        # Adding M2M table for field inppot on 'Calc'
        db.create_table('main_calc_inppot', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False))
        ))
        db.create_unique('main_calc_inppot', ['calc_id', 'potential_id'])

        # Adding M2M table for field outpot on 'Calc'
        db.create_table('main_calc_outpot', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False))
        ))
        db.create_unique('main_calc_outpot', ['calc_id', 'potential_id'])

        # Adding M2M table for field basis on 'Calc'
        db.create_table('main_calc_basis', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False))
        ))
        db.create_unique('main_calc_basis', ['calc_id', 'basis_id'])

        # Adding M2M table for field group on 'Calc'
        db.create_table('main_calc_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('calcgroup', models.ForeignKey(orm['main.calcgroup'], null=False))
        ))
        db.create_unique('main_calc_group', ['calc_id', 'calcgroup_id'])

        # Adding M2M table for field parent on 'Calc'
        db.create_table('main_calc_parent', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_calc', models.ForeignKey(orm['main.calc'], null=False)),
            ('to_calc', models.ForeignKey(orm['main.calc'], null=False))
        ))
        db.create_unique('main_calc_parent', ['from_calc_id', 'to_calc_id'])

        # Adding model 'CalcGroup'
        db.create_table('main_calcgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CalcGroup'])

        # Adding model 'CalcStatus'
        db.create_table('main_calcstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CalcStatus'])

        # Adding model 'Project'
        db.create_table('main_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['Project'])

        # Adding model 'CalcType'
        db.create_table('main_calctype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CalcType'])

        # Adding model 'CalcComment'
        db.create_table('main_calccomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcComment'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CalcComment'])

        # Adding model 'CalcAttrTxt'
        db.create_table('main_calcattrtxt', (
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
        db.send_create_signal('main', ['CalcAttrTxt'])

        # Adding model 'CalcAttrNum'
        db.create_table('main_calcattrnum', (
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
        db.send_create_signal('main', ['CalcAttrNum'])

        # Adding model 'CalcAttrTxtVal'
        db.create_table('main_calcattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Calc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['CalcAttrTxtVal'])

        # Adding unique constraint on 'CalcAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_calcattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'CalcAttrNumVal'
        db.create_table('main_calcattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Calc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CalcAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['CalcAttrNumVal'])

        # Adding unique constraint on 'CalcAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_calcattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Computer'
        db.create_table('main_computer', (
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
        db.send_create_signal('main', ['Computer'])

        # Adding model 'ComputerUsername'
        db.create_table('main_computerusername', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'])),
            ('aidauser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('remoteusername', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('main', ['ComputerUsername'])

        # Adding unique constraint on 'ComputerUsername', fields ['aidauser', 'computer']
        db.create_unique('main_computerusername', ['aidauser_id', 'computer_id'])

        # Adding model 'Code'
        db.create_table('main_code', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeStatus'])),
            ('computer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Computer'], blank=True)),
        ))
        db.send_create_signal('main', ['Code'])

        # Adding M2M table for field group on 'Code'
        db.create_table('main_code_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('code', models.ForeignKey(orm['main.code'], null=False)),
            ('codegroup', models.ForeignKey(orm['main.codegroup'], null=False))
        ))
        db.create_unique('main_code_group', ['code_id', 'codegroup_id'])

        # Adding model 'CodeGroup'
        db.create_table('main_codegroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeGroup'])

        # Adding model 'CodeComment'
        db.create_table('main_codecomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeComment'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeComment'])

        # Adding model 'CodeStatus'
        db.create_table('main_codestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CodeStatus'])

        # Adding model 'CodeType'
        db.create_table('main_codetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['CodeType'])

        # Adding model 'CodeAttrTxt'
        db.create_table('main_codeattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeAttrTxt'])

        # Adding model 'CodeAttrNum'
        db.create_table('main_codeattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeAttrNum'])

        # Adding model 'CodeAttrTxtVal'
        db.create_table('main_codeattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeAttrTxtVal'])

        # Adding unique constraint on 'CodeAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_codeattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'CodeAttrNumVal'
        db.create_table('main_codeattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Code'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.CodeAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['CodeAttrNumVal'])

        # Adding unique constraint on 'CodeAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_codeattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Element'
        db.create_table('main_element', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('Z', self.gf('django.db.models.fields.IntegerField')(unique=True)),
        ))
        db.send_create_signal('main', ['Element'])

        # Adding M2M table for field group on 'Element'
        db.create_table('main_element_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('element', models.ForeignKey(orm['main.element'], null=False)),
            ('elementgroup', models.ForeignKey(orm['main.elementgroup'], null=False))
        ))
        db.create_unique('main_element_group', ['element_id', 'elementgroup_id'])

        # Adding model 'ElementAttrTxt'
        db.create_table('main_elementattrtxt', (
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
        db.send_create_signal('main', ['ElementAttrTxt'])

        # Adding model 'ElementAttrNum'
        db.create_table('main_elementattrnum', (
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
        db.send_create_signal('main', ['ElementAttrNum'])

        # Adding model 'ElementGroup'
        db.create_table('main_elementgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['ElementGroup'])

        # Adding model 'ElementAttrTxtVal'
        db.create_table('main_elementattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Element'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['ElementAttrTxtVal'])

        # Adding unique constraint on 'ElementAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_elementattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'ElementAttrNumVal'
        db.create_table('main_elementattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Element'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ElementAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['ElementAttrNumVal'])

        # Adding unique constraint on 'ElementAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_elementattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Potential'
        db.create_table('main_potential', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialStatus'])),
        ))
        db.send_create_signal('main', ['Potential'])

        # Adding M2M table for field element on 'Potential'
        db.create_table('main_potential_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_potential_element', ['potential_id', 'element_id'])

        # Adding M2M table for field group on 'Potential'
        db.create_table('main_potential_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('potential', models.ForeignKey(orm['main.potential'], null=False)),
            ('potentialgroup', models.ForeignKey(orm['main.potentialgroup'], null=False))
        ))
        db.create_unique('main_potential_group', ['potential_id', 'potentialgroup_id'])

        # Adding model 'PotentialAttrTxt'
        db.create_table('main_potentialattrtxt', (
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
        db.send_create_signal('main', ['PotentialAttrTxt'])

        # Adding model 'PotentialAttrNum'
        db.create_table('main_potentialattrnum', (
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
        db.send_create_signal('main', ['PotentialAttrNum'])

        # Adding model 'PotentialGroup'
        db.create_table('main_potentialgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['PotentialGroup'])

        # Adding model 'PotentialComment'
        db.create_table('main_potentialcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialComment'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['PotentialComment'])

        # Adding model 'PotentialStatus'
        db.create_table('main_potentialstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['PotentialStatus'])

        # Adding model 'PotentialType'
        db.create_table('main_potentialtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['PotentialType'])

        # Adding model 'PotentialAttrTxtVal'
        db.create_table('main_potentialattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Potential'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['PotentialAttrTxtVal'])

        # Adding unique constraint on 'PotentialAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_potentialattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'PotentialAttrNumVal'
        db.create_table('main_potentialattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Potential'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.PotentialAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['PotentialAttrNumVal'])

        # Adding unique constraint on 'PotentialAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_potentialattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Basis'
        db.create_table('main_basis', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisType'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisStatus'])),
        ))
        db.send_create_signal('main', ['Basis'])

        # Adding M2M table for field element on 'Basis'
        db.create_table('main_basis_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_basis_element', ['basis_id', 'element_id'])

        # Adding M2M table for field group on 'Basis'
        db.create_table('main_basis_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('basis', models.ForeignKey(orm['main.basis'], null=False)),
            ('basisgroup', models.ForeignKey(orm['main.basisgroup'], null=False))
        ))
        db.create_unique('main_basis_group', ['basis_id', 'basisgroup_id'])

        # Adding model 'BasisAttrTxt'
        db.create_table('main_basisattrtxt', (
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
        db.send_create_signal('main', ['BasisAttrTxt'])

        # Adding model 'BasisAttrNum'
        db.create_table('main_basisattrnum', (
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
        db.send_create_signal('main', ['BasisAttrNum'])

        # Adding model 'BasisGroup'
        db.create_table('main_basisgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['BasisGroup'])

        # Adding model 'BasisComment'
        db.create_table('main_basiscomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisComment'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['BasisComment'])

        # Adding model 'BasisStatus'
        db.create_table('main_basisstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['BasisStatus'])

        # Adding model 'BasisType'
        db.create_table('main_basistype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['BasisType'])

        # Adding model 'BasisAttrTxtVal'
        db.create_table('main_basisattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Basis'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['BasisAttrTxtVal'])

        # Adding unique constraint on 'BasisAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_basisattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'BasisAttrNumVal'
        db.create_table('main_basisattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Basis'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.BasisAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['BasisAttrNumVal'])

        # Adding unique constraint on 'BasisAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_basisattrnumval', ['item_id', 'attr_id'])

        # Adding model 'Struc'
        db.create_table('main_struc', (
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
        db.send_create_signal('main', ['Struc'])

        # Adding M2M table for field element on 'Struc'
        db.create_table('main_struc_element', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('struc', models.ForeignKey(orm['main.struc'], null=False)),
            ('element', models.ForeignKey(orm['main.element'], null=False))
        ))
        db.create_unique('main_struc_element', ['struc_id', 'element_id'])

        # Adding M2M table for field group on 'Struc'
        db.create_table('main_struc_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('struc', models.ForeignKey(orm['main.struc'], null=False)),
            ('strucgroup', models.ForeignKey(orm['main.strucgroup'], null=False))
        ))
        db.create_unique('main_struc_group', ['struc_id', 'strucgroup_id'])

        # Adding model 'StrucGroup'
        db.create_table('main_strucgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StrucGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucGroup'])

        # Adding model 'StrucComment'
        db.create_table('main_struccomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StrucComment'], null=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucComment'])

        # Adding model 'StrucAttrTxt'
        db.create_table('main_strucattrtxt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucAttrTxt'])

        # Adding model 'StrucAttrNum'
        db.create_table('main_strucattrnum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('quality', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucAttrNum'])

        # Adding model 'StrucAttrTxtVal'
        db.create_table('main_strucattrtxtval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Struc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StrucAttrTxt'])),
            ('val', self.gf('django.db.models.fields.TextField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucAttrTxtVal'])

        # Adding unique constraint on 'StrucAttrTxtVal', fields ['item', 'attr']
        db.create_unique('main_strucattrtxtval', ['item_id', 'attr_id'])

        # Adding model 'StrucAttrNumVal'
        db.create_table('main_strucattrnumval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Struc'])),
            ('attr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.StrucAttrNum'])),
            ('val', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['StrucAttrNumVal'])

        # Adding unique constraint on 'StrucAttrNumVal', fields ['item', 'attr']
        db.create_unique('main_strucattrnumval', ['item_id', 'attr_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'StrucAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_strucattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'StrucAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_strucattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'BasisAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_basisattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'BasisAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_basisattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'PotentialAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_potentialattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'PotentialAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_potentialattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ElementAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_elementattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ElementAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_elementattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CodeAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_codeattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CodeAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_codeattrtxtval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'ComputerUsername', fields ['aidauser', 'computer']
        db.delete_unique('main_computerusername', ['aidauser_id', 'computer_id'])

        # Removing unique constraint on 'CalcAttrNumVal', fields ['item', 'attr']
        db.delete_unique('main_calcattrnumval', ['item_id', 'attr_id'])

        # Removing unique constraint on 'CalcAttrTxtVal', fields ['item', 'attr']
        db.delete_unique('main_calcattrtxtval', ['item_id', 'attr_id'])

        # Deleting model 'Calc'
        db.delete_table('main_calc')

        # Removing M2M table for field inpstruc on 'Calc'
        db.delete_table('main_calc_inpstruc')

        # Removing M2M table for field outstruc on 'Calc'
        db.delete_table('main_calc_outstruc')

        # Removing M2M table for field inppot on 'Calc'
        db.delete_table('main_calc_inppot')

        # Removing M2M table for field outpot on 'Calc'
        db.delete_table('main_calc_outpot')

        # Removing M2M table for field basis on 'Calc'
        db.delete_table('main_calc_basis')

        # Removing M2M table for field group on 'Calc'
        db.delete_table('main_calc_group')

        # Removing M2M table for field parent on 'Calc'
        db.delete_table('main_calc_parent')

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

        # Removing M2M table for field group on 'Code'
        db.delete_table('main_code_group')

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

        # Removing M2M table for field group on 'Element'
        db.delete_table('main_element_group')

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

        # Removing M2M table for field element on 'Potential'
        db.delete_table('main_potential_element')

        # Removing M2M table for field group on 'Potential'
        db.delete_table('main_potential_group')

        # Deleting model 'PotentialAttrTxt'
        db.delete_table('main_potentialattrtxt')

        # Deleting model 'PotentialAttrNum'
        db.delete_table('main_potentialattrnum')

        # Deleting model 'PotentialGroup'
        db.delete_table('main_potentialgroup')

        # Deleting model 'PotentialComment'
        db.delete_table('main_potentialcomment')

        # Deleting model 'PotentialStatus'
        db.delete_table('main_potentialstatus')

        # Deleting model 'PotentialType'
        db.delete_table('main_potentialtype')

        # Deleting model 'PotentialAttrTxtVal'
        db.delete_table('main_potentialattrtxtval')

        # Deleting model 'PotentialAttrNumVal'
        db.delete_table('main_potentialattrnumval')

        # Deleting model 'Basis'
        db.delete_table('main_basis')

        # Removing M2M table for field element on 'Basis'
        db.delete_table('main_basis_element')

        # Removing M2M table for field group on 'Basis'
        db.delete_table('main_basis_group')

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

        # Deleting model 'Struc'
        db.delete_table('main_struc')

        # Removing M2M table for field element on 'Struc'
        db.delete_table('main_struc_element')

        # Removing M2M table for field group on 'Struc'
        db.delete_table('main_struc_group')

        # Deleting model 'StrucGroup'
        db.delete_table('main_strucgroup')

        # Deleting model 'StrucComment'
        db.delete_table('main_struccomment')

        # Deleting model 'StrucAttrTxt'
        db.delete_table('main_strucattrtxt')

        # Deleting model 'StrucAttrNum'
        db.delete_table('main_strucattrnum')

        # Deleting model 'StrucAttrTxtVal'
        db.delete_table('main_strucattrtxtval')

        # Deleting model 'StrucAttrNumVal'
        db.delete_table('main_strucattrnumval')


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
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisAttrNum']", 'through': "orm['main.BasisAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisAttrTxt']", 'through': "orm['main.BasisAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.BasisGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisattrnum': {
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
        'main.basisattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'BasisAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Basis']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.basisattrtxt': {
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
        'main.basisattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'BasisAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Basis']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.basiscomment': {
            'Meta': {'object_name': 'BasisComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisgroup': {
            'Meta': {'object_name': 'BasisGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.BasisGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basisstatus': {
            'Meta': {'object_name': 'BasisStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.basistype': {
            'Meta': {'object_name': 'BasisType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calc': {
            'Meta': {'object_name': 'Calc'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcAttrNum']", 'through': "orm['main.CalcAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcAttrTxt']", 'through': "orm['main.CalcAttrTxtVal']", 'symmetrical': 'False'}),
            'basis': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Basis']", 'symmetrical': 'False', 'blank': 'True'}),
            'code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']"}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CalcGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inppot': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inpcalc'", 'blank': 'True', 'to': "orm['main.Potential']"}),
            'inpstruc': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inpcalc'", 'blank': 'True', 'to': "orm['main.Struc']"}),
            'outpot': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalc'", 'blank': 'True', 'to': "orm['main.Potential']"}),
            'outstruc': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'outcalc'", 'blank': 'True', 'to': "orm['main.Struc']"}),
            'parent': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'child'", 'blank': 'True', 'to': "orm['main.Calc']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcattrnum': {
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
        'main.calcattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CalcAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Calc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.calcattrtxt': {
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
        'main.calcattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CalcAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Calc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.calccomment': {
            'Meta': {'object_name': 'CalcComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcgroup': {
            'Meta': {'object_name': 'CalcGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CalcGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calcstatus': {
            'Meta': {'object_name': 'CalcStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.calctype': {
            'Meta': {'object_name': 'CalcType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.code': {
            'Meta': {'object_name': 'Code'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeAttrNum']", 'through': "orm['main.CodeAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeAttrTxt']", 'through': "orm['main.CodeAttrTxtVal']", 'symmetrical': 'False'}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']", 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.CodeGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codeattrnum': {
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
        'main.codeattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CodeAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.codeattrtxt': {
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
        'main.codeattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'CodeAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Code']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.codecomment': {
            'Meta': {'object_name': 'CodeComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codegroup': {
            'Meta': {'object_name': 'CodeGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.CodeGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codestatus': {
            'Meta': {'object_name': 'CodeStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.codetype': {
            'Meta': {'object_name': 'CodeType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.computer': {
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
        'main.computerusername': {
            'Meta': {'unique_together': "(('aidauser', 'computer'),)", 'object_name': 'ComputerUsername'},
            'aidauser': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'computer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Computer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remoteusername': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.element': {
            'Meta': {'object_name': 'Element'},
            'Z': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementAttrNum']", 'through': "orm['main.ElementAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementAttrTxt']", 'through': "orm['main.ElementAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ElementGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.elementattrnum': {
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
        'main.elementattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'ElementAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Element']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.elementattrtxt': {
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
        'main.elementattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'ElementAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Element']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.elementgroup': {
            'Meta': {'object_name': 'ElementGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ElementGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potential': {
            'Meta': {'object_name': 'Potential'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotentialAttrNum']", 'through': "orm['main.PotentialAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotentialAttrTxt']", 'through': "orm['main.PotentialAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.PotentialGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialStatus']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialType']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potentialattrnum': {
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
        'main.potentialattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'PotentialAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Potential']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.potentialattrtxt': {
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
        'main.potentialattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'PotentialAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Potential']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.potentialcomment': {
            'Meta': {'object_name': 'PotentialComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potentialgroup': {
            'Meta': {'object_name': 'PotentialGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.PotentialGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potentialstatus': {
            'Meta': {'object_name': 'PotentialStatus'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.potentialtype': {
            'Meta': {'object_name': 'PotentialType'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.struc': {
            'Meta': {'object_name': 'Struc'},
            'attrnum': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StrucAttrNum']", 'through': "orm['main.StrucAttrNumVal']", 'symmetrical': 'False'}),
            'attrtxt': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StrucAttrTxt']", 'through': "orm['main.StrucAttrTxtVal']", 'symmetrical': 'False'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'detail': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dim': ('django.db.models.fields.IntegerField', [], {}),
            'element': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Element']", 'symmetrical': 'False'}),
            'formula': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.StrucGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.strucattrnum': {
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
        'main.strucattrnumval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'StrucAttrNumVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StrucAttrNum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Struc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.FloatField', [], {})
        },
        'main.strucattrtxt': {
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
        'main.strucattrtxtval': {
            'Meta': {'unique_together': "(('item', 'attr'),)", 'object_name': 'StrucAttrTxtVal'},
            'attr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StrucAttrTxt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Struc']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'val': ('django.db.models.fields.TextField', [], {})
        },
        'main.struccomment': {
            'Meta': {'object_name': 'StrucComment'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StrucComment']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.strucgroup': {
            'Meta': {'object_name': 'StrucGroup'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.StrucGroup']", 'null': 'True', 'blank': 'True'}),
            'quality': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['main']