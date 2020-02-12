# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.1'
DOWN_REVISION = '1.0.0'


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DbUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                (
                    'is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status'
                    )
                ),
                ('email', models.EmailField(unique=True, max_length=75, db_index=True)),
                ('first_name', models.CharField(max_length=254, blank=True)),
                ('last_name', models.CharField(max_length=254, blank=True)),
                ('institution', models.CharField(max_length=254, blank=True)),
                (
                    'is_staff',
                    models.BooleanField(
                        default=False, help_text='Designates whether the user can log into this admin site.'
                    )
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        help_text=
                        'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
                    )
                ),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                (
                    'groups',
                    models.ManyToManyField(
                        related_query_name='user',
                        related_name='user_set',
                        to='auth.Group',
                        blank=True,
                        help_text=
                        'The groups this user belongs to. A user will get all permissions granted to each of his/her group.',
                        verbose_name='groups'
                    )
                ),
                (
                    'user_permissions',
                    models.ManyToManyField(
                        related_query_name='user',
                        related_name='user_set',
                        to='auth.Permission',
                        blank=True,
                        help_text='Specific permissions for this user.',
                        verbose_name='user permissions'
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024, db_index=True)),
                (
                    'datatype',
                    models.CharField(
                        default='none',
                        max_length=10,
                        db_index=True,
                        choices=[('float', 'float'), ('int', 'int'), ('txt', 'txt'), ('bool', 'bool'), ('date', 'date'),
                                 ('json', 'json'), ('dict', 'dict'), ('list', 'list'), ('none', 'none')]
                    )
                ),
                ('tval', models.TextField(default='', blank=True)),
                ('fval', models.FloatField(default=None, null=True)),
                ('ival', models.IntegerField(default=None, null=True)),
                ('bval', models.NullBooleanField(default=None)),
                ('dval', models.DateTimeField(default=None, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbAuthInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('auth_params', models.TextField(default='{}')),
                ('metadata', models.TextField(default='{}')),
                ('enabled', models.BooleanField(default=True)),
                ('aiidauser', models.ForeignKey(to='db.DbUser', on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbCalcState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                (
                    'state',
                    models.CharField(
                        db_index=True,
                        max_length=25,
                        choices=[('UNDETERMINED', 'UNDETERMINED'), ('NOTFOUND', 'NOTFOUND'),
                                 ('RETRIEVALFAILED', 'RETRIEVALFAILED'), ('COMPUTED', 'COMPUTED'),
                                 ('RETRIEVING', 'RETRIEVING'), ('WITHSCHEDULER', 'WITHSCHEDULER'),
                                 ('SUBMISSIONFAILED', 'SUBMISSIONFAILED'), ('PARSING', 'PARSING'), ('FAILED', 'FAILED'),
                                 ('FINISHED', 'FINISHED'), ('TOSUBMIT', 'TOSUBMIT'), ('SUBMITTING', 'SUBMITTING'),
                                 ('IMPORTED', 'IMPORTED'), ('NEW', 'NEW'), ('PARSINGFAILED', 'PARSINGFAILED')]
                    )
                ),
                ('time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(editable=False, blank=True, max_length=36)),
                ('ctime', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('mtime', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbComputer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36, editable=False, blank=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('hostname', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('enabled', models.BooleanField(default=True)),
                ('transport_type', models.CharField(max_length=255)),
                ('scheduler_type', models.CharField(max_length=255)),
                ('transport_params', models.TextField(default='{}')),
                ('metadata', models.TextField(default='{}')),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024, db_index=True)),
                (
                    'datatype',
                    models.CharField(
                        default='none',
                        max_length=10,
                        db_index=True,
                        choices=[('float', 'float'), ('int', 'int'), ('txt', 'txt'), ('bool', 'bool'), ('date', 'date'),
                                 ('json', 'json'), ('dict', 'dict'), ('list', 'list'), ('none', 'none')]
                    )
                ),
                ('tval', models.TextField(default='', blank=True)),
                ('fval', models.FloatField(default=None, null=True)),
                ('ival', models.IntegerField(default=None, null=True)),
                ('bval', models.NullBooleanField(default=None)),
                ('dval', models.DateTimeField(default=None, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36, editable=False, blank=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('type', models.CharField(default='', max_length=255, db_index=True)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('description', models.TextField(blank=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255, db_index=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbLock',
            fields=[
                ('key', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('creation', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('timeout', models.IntegerField(editable=False)),
                ('owner', models.CharField(max_length=255)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('loggername', models.CharField(max_length=255, db_index=True)),
                ('levelname', models.CharField(max_length=50, db_index=True)),
                ('objname', models.CharField(db_index=True, max_length=255, blank=True)),
                ('objpk', models.IntegerField(null=True, db_index=True)),
                ('message', models.TextField(blank=True)),
                ('metadata', models.TextField(default='{}')),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36, editable=False, blank=True)),
                ('type', models.CharField(max_length=255, db_index=True)),
                ('label', models.CharField(db_index=True, max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('ctime', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('mtime', models.DateTimeField(auto_now=True)),
                ('nodeversion', models.IntegerField(default=1, editable=False)),
                ('public', models.BooleanField(default=False)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbPath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('depth', models.IntegerField(editable=False)),
                ('entry_edge_id', models.IntegerField(null=True, editable=False)),
                ('direct_edge_id', models.IntegerField(null=True, editable=False)),
                ('exit_edge_id', models.IntegerField(null=True, editable=False)),
                (
                    'child',
                    models.ForeignKey(
                        related_name='parent_paths', editable=False, to='db.DbNode', on_delete=models.CASCADE
                    )
                ),
                (
                    'parent',
                    models.ForeignKey(
                        related_name='child_paths', editable=False, to='db.DbNode', on_delete=models.CASCADE
                    )
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=1024, db_index=True)),
                (
                    'datatype',
                    models.CharField(
                        default='none',
                        max_length=10,
                        db_index=True,
                        choices=[('float', 'float'), ('int', 'int'), ('txt', 'txt'), ('bool', 'bool'), ('date', 'date'),
                                 ('json', 'json'), ('dict', 'dict'), ('list', 'list'), ('none', 'none')]
                    )
                ),
                ('tval', models.TextField(default='', blank=True)),
                ('fval', models.FloatField(default=None, null=True)),
                ('ival', models.IntegerField(default=None, null=True)),
                ('bval', models.NullBooleanField(default=None)),
                ('dval', models.DateTimeField(default=None, null=True)),
                ('description', models.TextField(blank=True)),
                ('time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbWorkflow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36, editable=False, blank=True)),
                ('ctime', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('mtime', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(db_index=True, max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('nodeversion', models.IntegerField(default=1, editable=False)),
                ('lastsyncedversion', models.IntegerField(default=0, editable=False)),
                (
                    'state',
                    models.CharField(
                        choices=[('CREATED', 'CREATED'), ('ERROR', 'ERROR'), ('FINISHED', 'FINISHED'),
                                 ('INITIALIZED', 'INITIALIZED'), ('RUNNING', 'RUNNING'), ('SLEEP', 'SLEEP')],
                        default='INITIALIZED',
                        max_length=255
                    )
                ),
                ('report', models.TextField(blank=True)),
                ('module', models.TextField()),
                ('module_class', models.TextField()),
                ('script_path', models.TextField()),
                ('script_md5', models.CharField(max_length=255)),
                ('user', models.ForeignKey(to='db.DbUser', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbWorkflowData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('data_type', models.CharField(default='PARAMETER', max_length=255)),
                ('value_type', models.CharField(default='NONE', max_length=255)),
                ('json_value', models.TextField(blank=True)),
                ('aiida_obj', models.ForeignKey(blank=True, to='db.DbNode', null=True, on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='data', to='db.DbWorkflow', on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbWorkflowStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('nextcall', models.CharField(default='none', max_length=255)),
                (
                    'state',
                    models.CharField(
                        choices=[('CREATED', 'CREATED'), ('ERROR', 'ERROR'), ('FINISHED', 'FINISHED'),
                                 ('INITIALIZED', 'INITIALIZED'), ('RUNNING', 'RUNNING'), ('SLEEP', 'SLEEP')],
                        default='CREATED',
                        max_length=255
                    )
                ),
                ('calculations', models.ManyToManyField(related_name='workflow_step', to='db.DbNode')),
                ('parent', models.ForeignKey(related_name='steps', to='db.DbWorkflow', on_delete=models.CASCADE)),
                ('sub_workflows', models.ManyToManyField(related_name='parent_workflow_step', to='db.DbWorkflow')),
                ('user', models.ForeignKey(to='db.DbUser', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='dbworkflowstep',
            unique_together=set([('parent', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='dbworkflowdata',
            unique_together=set([('parent', 'name', 'data_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='dbsetting',
            unique_together=set([('key',)]),
        ),
        migrations.AddField(
            model_name='dbnode',
            name='children',
            field=models.ManyToManyField(related_name='parents', through='db.DbPath', to='db.DbNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbnode',
            name='dbcomputer',
            field=models.ForeignKey(
                related_name='dbnodes', on_delete=django.db.models.deletion.PROTECT, to='db.DbComputer', null=True
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbnode',
            name='outputs',
            field=models.ManyToManyField(related_name='inputs', through='db.DbLink', to='db.DbNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbnode',
            name='user',
            field=models.ForeignKey(
                related_name='dbnodes', on_delete=django.db.models.deletion.PROTECT, to='db.DbUser'
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dblink',
            name='input',
            field=models.ForeignKey(
                related_name='output_links', on_delete=django.db.models.deletion.PROTECT, to='db.DbNode'
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dblink',
            name='output',
            field=models.ForeignKey(related_name='input_links', to='db.DbNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dblink',
            unique_together=set([('input', 'output'), ('output', 'label')]),
        ),
        migrations.AddField(
            model_name='dbgroup',
            name='dbnodes',
            field=models.ManyToManyField(related_name='dbgroups', to='db.DbNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbgroup',
            name='user',
            field=models.ForeignKey(related_name='dbgroups', to='db.DbUser', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dbgroup',
            unique_together=set([('name', 'type')]),
        ),
        migrations.AddField(
            model_name='dbextra',
            name='dbnode',
            field=models.ForeignKey(related_name='dbextras', to='db.DbNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dbextra',
            unique_together=set([('dbnode', 'key')]),
        ),
        migrations.AddField(
            model_name='dbcomment',
            name='dbnode',
            field=models.ForeignKey(related_name='dbcomments', to='db.DbNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbcomment',
            name='user',
            field=models.ForeignKey(to='db.DbUser', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbcalcstate',
            name='dbnode',
            field=models.ForeignKey(related_name='dbstates', to='db.DbNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dbcalcstate',
            unique_together=set([('dbnode', 'state')]),
        ),
        migrations.AddField(
            model_name='dbauthinfo',
            name='dbcomputer',
            field=models.ForeignKey(to='db.DbComputer', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dbauthinfo',
            unique_together=set([('aiidauser', 'dbcomputer')]),
        ),
        migrations.AddField(
            model_name='dbattribute',
            name='dbnode',
            field=models.ForeignKey(related_name='dbattributes', to='db.DbNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dbattribute',
            unique_together=set([('dbnode', 'key')]),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
