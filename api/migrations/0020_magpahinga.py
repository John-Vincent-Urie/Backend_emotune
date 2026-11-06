"""Depressed's Ben&Ben song is "Magpahinga", not "Pahinga" (2026-11-06).

Ben&Ben has no song called "Pahinga" on Spotify, so that entry could never
play. The therapist's song is "Magpahinga" (the original 2021 single, looked
up by exact title and artist); docs/music.md now names it. It takes the same
place in DEPRESSED. The "Pahinga" row is only unlinked: favorites and history
can point to it.

Undoing puts "Pahinga" back in that place and removes "Magpahinga" if nothing
else uses it.
"""
from django.db import migrations

OLD = ('Pahinga', 'Ben&Ben')
NEW = {
    'title': 'Magpahinga', 'artist': 'Ben&Ben',
    'spotify_track_id': '4LBCCdHfmHm9NwerX6hvrz', 'album': 'Magpahinga',
    'image': 'https://i.scdn.co/image/ab67616d0000b2730b0bc4352c1be985dc6e7d69',
    'duration_ms': 238792,
}
EMOTION = 'depressing'


def _swap(apps, from_song, to_song):
    Emotion = apps.get_model('api', 'Emotion')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    emotion = Emotion.objects.get(name=EMOTION)
    link = EmotionSong.objects.filter(emotion=emotion, song=from_song).first()
    if link is None:
        return
    if EmotionSong.objects.filter(emotion=emotion, song=to_song).exists():
        link.delete()
        return
    link.song = to_song
    link.save(update_fields=['song'])


def use_magpahinga(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    magpahinga, _ = Song.objects.get_or_create(
        title=NEW['title'], artist=NEW['artist'],
        defaults={
            **NEW,
            'spotify_url': f"https://open.spotify.com/track/{NEW['spotify_track_id']}",
        },
    )
    pahinga = Song.objects.filter(title=OLD[0], artist=OLD[1]).first()
    if pahinga is not None:
        _swap(apps, pahinga, magpahinga)


def use_pahinga(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    magpahinga = Song.objects.filter(title=NEW['title'], artist=NEW['artist']).first()
    if magpahinga is None:
        return
    pahinga = Song.objects.get(title=OLD[0], artist=OLD[1])
    _swap(apps, magpahinga, pahinga)
    Song.objects.filter(
        pk=magpahinga.pk, emotion_links__isnull=True, pair_links__isnull=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_music_md_sync'),
    ]

    operations = [
        migrations.RunPython(use_magpahinga, use_pahinga),
    ]
