"""Migration 0019: every list matches docs/music.md, and it undoes cleanly."""

import re
import unicodedata
from importlib import import_module
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test import TestCase

from api.models import Emotion, EmotionPair, EmotionPairSong, EmotionSong, Song

migration = import_module('api.migrations.0019_music_md_sync')

HEADINGS = {
    'Happy': 'happy', 'Sad': 'sad', 'Angry': 'angry', 'Motivated': 'motivational',
    'Scared': 'fear', 'Depressed': 'depressing', 'Nostalgic': 'nostalgic',
    'Romantic': 'romantic', 'Lonely': 'lonely', 'Calm': 'calm',
    'Stressed': 'stressed', 'Surprised': 'surprising',
}
MIX_HEADINGS = {
    'Bittersweet': 'bittersweet', 'Tender': 'tender', 'Challenged': 'challenged',
    'Bittersweet Nostalgia': 'bittersweet_nostalgia',
    'Romantic Melancholy': 'romantic_melancholy',
}
# The stored spelling of a song docs/music.md spells differently.
STORED_AS = {
    ('awitin mo at isasayaw ko', 'vst and company'): ('awitin mo isasayaw ko', 'vst and company'),
    ('merry go round', 'joe hisaishi'): ('merry go round of life', 'joe hisaishi'),
}


def _key(title, artist):
    def norm(text):
        text = unicodedata.normalize('NFKD', text.replace('’', "'").replace('‘', "'"))
        text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
        text = text.replace(' & ', ' and ')
        return re.sub(r'[^a-z0-9!.]+', ' ', text).strip()
    key = (norm(title), norm(artist))
    return STORED_AS.get(key, key)


def _music_md_lists():
    """Each list in docs/music.md, repeats collapsed, as normalized keys."""
    # The standalone backend repo has no docs/ and keeps a copy in api/data/.
    path = Path(settings.BASE_DIR).parent / 'docs' / 'music.md'
    if not path.exists():
        path = Path(settings.BASE_DIR) / 'api' / 'data' / 'music.md'
    lists, current, in_mixed = {}, None, False
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == 'Mixed':
            in_mixed, current = True, None
            continue
        headings = MIX_HEADINGS if in_mixed else HEADINGS
        if line in headings:
            current = headings[line]
            lists[current] = []
            continue
        match = re.match(r'^(.*?)\s+–\s+(.*?)(\s*\(duplicate\))?$', line)
        if match and current:
            key = _key(match.group(1), match.group(2))
            if key not in lists[current]:
                lists[current].append(key)
    return lists


def _emotion_list(name):
    return [
        (link.song.title, link.song.artist)
        for link in EmotionSong.objects.filter(emotion__name=name)
        .select_related('song').order_by('position')
    ]


def _mix_list(name):
    return [
        (link.song.title, link.song.artist)
        for link in EmotionPairSong.objects.filter(pair__name=name)
        .select_related('song').order_by('position')
    ]


class MusicMdSyncTests(TestCase):
    def test_every_emotion_list_matches_music_md_in_count_and_order(self):
        expected = _music_md_lists()
        for name in HEADINGS.values():
            with self.subTest(emotion=name):
                stored = _emotion_list(name)
                self.assertEqual([_key(*song) for song in stored], expected[name])
                self.assertEqual(
                    list(EmotionSong.objects.filter(emotion__name=name)
                         .order_by('position').values_list('position', flat=True)),
                    list(range(1, len(stored) + 1)),
                )

    def test_every_mix_list_matches_music_md_in_count_and_order(self):
        expected = _music_md_lists()
        for name in MIX_HEADINGS.values():
            with self.subTest(mix=name):
                self.assertEqual([_key(*song) for song in _mix_list(name)], expected[name])

    def test_every_emotion_has_ten_distinct_songs(self):
        for name in HEADINGS.values():
            with self.subTest(emotion=name):
                songs = _emotion_list(name)
                self.assertEqual(len(songs), 10)
                self.assertEqual(len(songs), len(set(songs)))
        self.assertEqual(
            [song for song in _emotion_list('angry') if song[1] == 'Juan Karlos'],
            [('ERE', 'Juan Karlos')],
        )

    def test_both_photographs_are_in_nostalgic(self):
        nostalgic = _emotion_list('nostalgic')
        self.assertIn(('Photograph', 'Ed Sheeran'), nostalgic)
        self.assertIn(('Photograph', 'Nickelback'), nostalgic)
        self.assertNotEqual(
            Song.objects.get(title='Photograph', artist='Ed Sheeran').spotify_track_id,
            Song.objects.get(title='Photograph', artist='Nickelback').spotify_track_id,
        )

    def test_spelling_variants_reuse_the_existing_song(self):
        self.assertIn(('Awitin Mo, Isasayaw ko', 'VST & Company'), _emotion_list('happy'))
        self.assertIn(('Merry-Go-Round of Life', 'Joe Hisaishi'), _emotion_list('calm'))
        self.assertFalse(Song.objects.filter(title='Awitin Mo at Isasayaw Ko').exists())
        self.assertFalse(Song.objects.filter(title='Merry-Go-Round').exists())
        self.assertEqual(Song.objects.filter(title__iexact='bittersweet', artist='Madison Beer').count(), 1)

    def test_new_songs_carry_their_spotify_recording(self):
        for data in migration.NEW_SONGS:
            with self.subTest(song=data['title']):
                song = Song.objects.get(title=data['title'], artist=data['artist'])
                self.assertEqual(song.spotify_track_id, data['spotify_track_id'])
                if data['spotify_track_id']:
                    self.assertEqual(
                        song.spotify_url,
                        f"https://open.spotify.com/track/{data['spotify_track_id']}",
                    )
        surprise = Song.objects.get(title='Surprise', artist='P!nk')
        self.assertIsNone(surprise.spotify_track_id)
        self.assertFalse(surprise.as_track(1)['playable'])

    def test_removed_songs_are_unlinked_but_kept(self):
        for title, artist in (('Shake It Off', 'Taylor Swift'), ('Kabisado', 'IV OF SPADES'),
                              ('With a Smile', 'Eraserheads')):
            with self.subTest(song=title):
                song = Song.objects.get(title=title, artist=artist)
                self.assertFalse(song.emotion_links.exclude(emotion__name='mixed').exists())
                self.assertFalse(song.pair_links.exists())

    def test_the_mixed_emotion_list_is_untouched(self):
        self.assertEqual(
            _emotion_list('mixed'),
            [('Happier', 'Marshmello & Bastille'), ('The Day You Said Goodnight', 'Hale'),
             ('Pasilyo', 'SunKissed Lola'), ('Castle on the Hill', 'Ed Sheeran'),
             ('Whatever It Takes', 'Imagine Dragons')],
        )

    def test_undo_restores_0018_and_redo_is_idempotent(self):
        migration.restore_previous_lists(apps, None)

        for name, songs in migration.PREVIOUS_EMOTION_SONGS.items():
            self.assertEqual(_emotion_list(name), songs, name)
        self.assertEqual(
            _mix_list('bittersweet_nostalgia'),
            migration.PREVIOUS_MIX_SONGS['bittersweet_nostalgia'],
        )
        for data in migration.NEW_SONGS:
            self.assertFalse(
                Song.objects.filter(title=data['title'], artist=data['artist']).exists(),
                data['title'],
            )

        migration.sync_with_music_md(apps, None)
        migration.sync_with_music_md(apps, None)
        for name, songs in migration.EMOTION_SONGS.items():
            self.assertEqual(_emotion_list(name), songs, name)
        for name, songs in migration.MIX_SONGS.items():
            self.assertEqual(_mix_list(name), songs, name)
        self.assertEqual(Emotion.objects.count(), 13)
        self.assertEqual(EmotionPair.objects.count(), 5)
