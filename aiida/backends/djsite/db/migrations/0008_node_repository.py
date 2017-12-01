# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0007_update_linktypes'),
    ]

    operations = [
        migrations.CreateModel(
            name='DbFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(editable=False, blank=True)),
                ('key', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbNodeFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(editable=False, blank=True)),
                ('path', models.CharField(max_length=255, db_index=True)),
                ('metadata', models.TextField(default=b'{}')),
                ('file', models.ForeignKey(related_name='dbnodefiles', on_delete=django.db.models.deletion.PROTECT, to='db.DbFile', null=True)),
                ('node', models.ForeignKey(related_name='dbnodefiles', to='db.DbNode')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DbRepository',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('uuid', django_extensions.db.fields.UUIDField(auto=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='dbnodefile',
            unique_together=set([('node', 'path')]),
        ),
        migrations.AddField(
            model_name='dbfile',
            name='nodes',
            field=models.ManyToManyField(related_name='files', through='db.DbNodeFile', to='db.DbNode'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dbfile',
            name='repository',
            field=models.ForeignKey(related_name='files', on_delete=django.db.models.deletion.PROTECT, to='db.DbRepository'),
            preserve_default=True,
        ),
    ]
