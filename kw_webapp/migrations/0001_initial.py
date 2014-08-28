# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Level'
        db.create_table('kw_webapp_level', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('kw_webapp', ['Level'])

        # Adding model 'Profile'
        db.create_table('kw_webapp_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['auth.User'])),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('gravatar', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal('kw_webapp', ['Profile'])

        # Adding M2M table for field unlocked_levels on 'Profile'
        m2m_table_name = db.shorten_name('kw_webapp_profile_unlocked_levels')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['kw_webapp.profile'], null=False)),
            ('level', models.ForeignKey(orm['kw_webapp.level'], null=False))
        ))
        db.create_unique(m2m_table_name, ['profile_id', 'level_id'])

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
            ('correct', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('incorrect', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('streak', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('last_studied', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('needs_review', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('kw_webapp', ['UserSpecific'])


    def backwards(self, orm):
        # Deleting model 'Level'
        db.delete_table('kw_webapp_level')

        # Deleting model 'Profile'
        db.delete_table('kw_webapp_profile')

        # Removing M2M table for field unlocked_levels on 'Profile'
        db.delete_table(db.shorten_name('kw_webapp_profile_unlocked_levels'))

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
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)"},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kw_webapp.level': {
            'Meta': {'object_name': 'Level'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'kw_webapp.profile': {
            'Meta': {'object_name': 'Profile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'unlocked_levels': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['kw_webapp.Level']"}),
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
            'correct': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incorrect': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_studied': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'needs_review': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'streak': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
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