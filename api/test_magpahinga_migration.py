"""Migration 0020: Depressed plays Ben&Ben's "Magpahinga" instead of "Pahinga"."""

from importlib import import_module

from django.apps import apps
from django.test import TestCase

from api.models import EmotionSong, Song

migration = import_module('api.migrations.0020_magpahinga')


def _depressed():
    return [
        (link.song.title, link.song.artist)
        for link in EmotionSong.objects.filter(emotion__name='depressing')
        .select_related('song').order_by('position')
    ]


class MagpahingaMigrationTests(TestCase):
    def test_magpahinga_takes_pahingas_place_and_plays(self):
        songs = _depressed()
        self.assertEqual(songs[4], ('Magpahinga', 'Ben&Ben'))
        self.assertNotIn(('Pahinga', 'Ben&Ben'), songs)
        self.assertEqual(len(songs), 10)

        track = Song.objects.get(title='Magpahinga', artist='Ben&Ben').as_track(5)
        self.assertTrue(track['playable'])
        self.assertEqual(track['uri'], 'spotify:track:4LBCCdHfmHm9NwerX6hvrz')

    def test_pahinga_is_unlinked_but_kept(self):
        pahinga = Song.objects.get(title='Pahinga', artist='Ben&Ben')
        self.assertFalse(pahinga.emotion_links.exists())

    def test_undo_restores_pahinga_and_redo_is_idempotent(self):
        migration.use_pahinga(apps, None)
        self.assertEqual(_depressed()[4], ('Pahinga', 'Ben&Ben'))
        self.assertFalse(Song.objects.filter(title='Magpahinga').exists())

        migration.use_magpahinga(apps, None)
        migration.use_magpahinga(apps, None)
        self.assertEqual(_depressed()[4], ('Magpahinga', 'Ben&Ben'))
        self.assertEqual(Song.objects.filter(title='Magpahinga').count(), 1)
