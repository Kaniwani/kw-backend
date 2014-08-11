# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Profile'
        db.create_table('kw_webapp_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['auth.User'])),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal('kw_webapp', ['Profile'])

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
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('kw_webapp', ['Reading'])

        # Adding model 'UserSpecific'
        db.create_table('kw_webapp_userspecific', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['kw_webapp.Vocabulary'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('correct', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('incorrect', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('streak', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('last_studied', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('kw_webapp', ['UserSpecific'])


    def backwards(self, orm):
        # Deleting model 'Profile'
        db.delete_table('kw_webapp_profile')

        # Deleting model 'Vocabulary'
        db.delete_table('kw_webapp_vocabulary')

        # Deleting model 'Reading'
        db.delete_table('kw_webapp_reading')

        # Deleting model 'UserSpecific'
        db.delete_table('kw_webapp_userspecific')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kw_webapp.profile': {
            'Meta': {'object_name': 'Profile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'to': "orm['auth.User']"})
        },
        'kw_webapp.reading': {
            'Meta': {'object_name': 'Reading'},
            'character': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kana': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kw_webapp.Vocabulary']"})
        },
        'kw_webapp.userspecific': {
            'Meta': {'object_name': 'UserSpecific'},
            'correct': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incorrect': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'last_studied': ('django.db.models.fields.DateTimeField', [], {}),
            'streak': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kw_webapp.Vocabulary']"})
        },
        'kw_webapp.vocabulary': {
            'Meta': {'object_name': 'Vocabulary'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meaning': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['kw_webapp']