# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Synonym'
        db.delete_table('kw_webapp_synonym')

        # Adding field 'Profile.vacation_date'
        db.add_column('kw_webapp_profile', 'vacation_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True, default=None),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'Synonym'
        db.create_table('kw_webapp_synonym', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['kw_webapp.UserSpecific'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('kw_webapp', ['Synonym'])

        # Deleting field 'Profile.vacation_date'
        db.delete_column('kw_webapp_profile', 'vacation_date')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'", 'ordering': "('name',)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kw_webapp.announcement': {
            'Meta': {'object_name': 'Announcement'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'default': 'datetime.datetime(2015, 6, 14, 0, 0)'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'kw_webapp.level': {
            'Meta': {'object_name': 'Level'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'kw_webapp.profile': {
            'Meta': {'object_name': 'Profile'},
            'about': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'api_valid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'posts_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'topics_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'twitter': ('django.db.models.fields.CharField', [], {'default': "'@Tadgh11'", 'max_length': '255'}),
            'unlocked_levels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['kw_webapp.Level']", 'symmetrical': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'vacation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True', 'default': 'None'}),
            'website': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
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
            'burnt': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'correct': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incorrect': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_studied': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'needs_review': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'next_review_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'streak': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'synonyms': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'default': 'None', 'max_length': '255'}),
            'unlock_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
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