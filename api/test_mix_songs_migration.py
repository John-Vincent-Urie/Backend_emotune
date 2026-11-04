"""Migration 0018 (five songs per named mix) applies and undoes cleanly."""

from importlib import import_module

from django.apps import apps
from django.test import TestCase

from api.models import EmotionPair, EmotionPairSong, Song

migration = import_module('api.migrations.0018_mix_song_lists')


def _mix_lists():
    return {
        pair.name: [
            (link.song.title, link.song.artist)
            for link in pair.song_links.select_related('song').order_by('position')
        ]
        for pair in EmotionPair.objects.all()
    }


class MixSongListMigrationTests(TestCase):
    def test_every_mix_has_its_five_songs_in_order(self):
        self.assertEqual(_mix_lists(), migration.MIX_SONGS)
        for pair in EmotionPair.objects.all():
            self.assertEqual(
                list(pair.song_links.order_by('position').values_list('position', flat=True)),
                [1, 2, 3, 4, 5],
            )

    def test_new_songs_keep_their_spotify_recording(self):
        multo = Song.objects.get(title='Multo', artist='Cup of Joe')
        self.assertEqual(multo.spotify_track_id, '4cBm8rv2B5BJWU2pDaHVbF')
        self.assertEqual(multo.spotify_url, 'https://open.spotify.com/track/4cBm8rv2B5BJWU2pDaHVbF')
        beer = Song.objects.get(title='bittersweet', artist='Madison Beer')
        self.assertEqual(beer.spotify_track_id, '3A02hWQ2ebOFDWSbAMNnpw')
        self.assertEqual(beer.spotify_url, 'https://open.spotify.com/track/3A02hWQ2ebOFDWSbAMNnpw')
        self.assertFalse(Song.objects.filter(artist='LANY').exists())

    def test_shared_songs_keep_their_other_lists(self):
        with_a_smile = Song.objects.get(title='With a Smile', artist='Eraserheads')
        self.assertTrue(with_a_smile.emotion_links.filter(emotion__name='depressing').exists())
        self.assertTrue(with_a_smile.pair_links.filter(pair__name='bittersweet_nostalgia').exists())

    def test_undo_restores_one_song_per_mix_and_redo_is_idempotent(self):
        migration.remove_mix_songs(apps, None)

        self.assertEqual(
            _mix_lists(),
            {name: [song] for name, song in migration.PREVIOUS_SONG.items()},
        )
        self.assertEqual(set(EmotionPairSong.objects.values_list('position', flat=True)), {1})
        for data in migration.NEW_SONGS:
            self.assertFalse(
                Song.objects.filter(title=data['title'], artist=data['artist']).exists(),
                data['title'],
            )
        # Songs that were already in the collection stay.
        self.assertTrue(Song.objects.filter(title='Married Life').exists())

        migration.add_mix_songs(apps, None)
        migration.add_mix_songs(apps, None)
        self.assertEqual(_mix_lists(), migration.MIX_SONGS)
