# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'KaniWaniUser'
        db.create_table('kw_webapp_kaniwaniuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('kw_webapp', ['KaniWaniUser'])

        # Adding M2M table for field groups on 'KaniWaniUser'
        m2m_table_name = db.shorten_name('kw_webapp_kaniwaniuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('kaniwaniuser', models.ForeignKey(orm['kw_webapp.kaniwaniuser'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['kaniwaniuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'KaniWaniUser'
        m2m_table_name = db.shorten_name('kw_webapp_kaniwaniuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('kaniwaniuser', models.ForeignKey(orm['kw_webapp.kaniwaniuser'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['kaniwaniuser_id', 'permission_id'])

        # Adding model 'Vocabulary'
        db.create_table('kw_webapp_vocabulary', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('meaning', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('kw_webapp', ['Vocabulary'])

        # Adding model 'Reading'
        db.create_table('kw_webapp_reading', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['kw_webapp.Vocabulary'])),
            ('character', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('kana', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('level', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('kw_webapp', ['Reading'])


    def backwards(self, orm):
        # Deleting model 'KaniWaniUser'
        db.delete_table('kw_webapp_kaniwaniuser')

        # Removing M2M table for field groups on 'KaniWaniUser'
        db.delete_table(db.shorten_name('kw_webapp_kaniwaniuser_groups'))

        # Removing M2M table for field user_permissions on 'KaniWaniUser'
        db.delete_table(db.shorten_name('kw_webapp_kaniwaniuser_user_permissions'))

        # Deleting model 'Vocabulary'
        db.delete_table('kw_webapp_vocabulary')

        # Deleting model 'Reading'
        db.delete_table('kw_webapp_reading')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kw_webapp.kaniwaniuser': {
            'Meta': {'object_name': 'KaniWaniUser'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'kw_webapp.reading': {
            'Meta': {'object_name': 'Reading'},
            'character': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kana': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'level': ('django.db.models.fields.IntegerField', [], {}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kw_webapp.Vocabulary']"})
        },
        'kw_webapp.vocabulary': {
            'Meta': {'object_name': 'Vocabulary'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meaning': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['kw_webapp']