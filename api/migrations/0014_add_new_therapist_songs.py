"""Add eight therapist-approved songs (2026-10-21).

Each song goes at the end of its emotion's list. The Spotify recording is the
original release, looked up by exact title and artist. "The Night We Met" is
already in SAD, so its existing Song row is linked to MIXED as well rather than
duplicated. docs/music.md lists the same songs.
"""
from django.db import migrations

SONGS = [
    ('sad', {
        'title': 'Paubaya', 'artist': 'Moira Dela Torre',
        'spotify_track_id': '7IZ3aOo6kzegDLZdZKOMm7', 'album': 'Paubaya',
        'image': 'https://i.scdn.co/image/ab67616d0000b273fd86d3241340bfba19c9fc4c',
        'duration_ms': 282020,
    }),
    ('angry', {
        'title': 'Upuan', 'artist': 'Gloc-9',
        'spotify_track_id': '5sSG2CQBI3perj0gMbhXd1', 'album': 'Matrikula',
        'image': 'https://i.scdn.co/image/ab67616d0000b27315672104a65e094292214fd0',
        'duration_ms': 253000,
    }),
    ('depressing', {
        'title': 'I Wanna Be Yours', 'artist': 'Arctic Monkeys',
        'spotify_track_id': '5XeFesFbtLpXzIVDNQP22n', 'album': 'AM',
        'image': 'https://i.scdn.co/image/ab67616d0000b2734ae1c4c5c45aabe565499163',
        'duration_ms': 183956,
    }),
    ('nostalgic', {
        'title': 'Magbalik', 'artist': 'Callalily',
        'spotify_track_id': '5zMR44ZH4KVZj4FlhTj3SE', 'album': 'Destination XYZ',
        'image': 'https://i.scdn.co/image/ab67616d0000b273e1eb7dcffb820f82dea0348b',
        'duration_ms': 326813,
    }),
    ('mixed', {
        'title': 'The Night We Met', 'artist': 'Lord Huron',
        'spotify_track_id': '5yJaXWIErrrsjQ3J0eR5aK', 'album': 'Strange Trails',
        'image': '', 'duration_ms': 208000,
    }),
    ('mixed', {
        'title': 'Married Life', 'artist': 'Michael Giacchino',
        'spotify_track_id': '7iocNjLrxPHLl8njgRlv5U',
        'album': 'Up (Original Motion Picture Soundtrack)',
        'image': 'https://i.scdn.co/image/ab67616d0000b27390ab02c84abe851ec8353506',
        'duration_ms': 250573,
    }),
    ('mixed', {
        'title': 'Forget Her', 'artist': 'Jeff Buckley',
        'spotify_track_id': '6UuVONmxXwTKN1ISepuAoQ', 'album': 'Grace',
        'image': 'https://i.scdn.co/image/ab67616d0000b273afc2d1d2c8703a10aeded0af',
        'duration_ms': 314693,
    }),
    ('mixed', {
        'title': 'Palagi', 'artist': 'TJ Monterde',
        'spotify_track_id': '0sqnYgWOw9DMc6jRgkcB2m', 'album': 'Palagi',
        'image': 'https://i.scdn.co/image/ab67616d0000b2734dfe438c126e581409c45481',
        'duration_ms': 218051,
    }),
]


def add_songs(apps, schema_editor):
    Emotion = apps.get_model('api', 'Emotion')
    Song = apps.get_model('api', 'Song')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    for emotion_name, data in SONGS:
        emotion = Emotion.objects.get(name=emotion_name)
        track_id = data['spotify_track_id']
        song, _ = Song.objects.get_or_create(
            title=data['title'], artist=data['artist'],
            defaults={**data, 'spotify_url': f'https://open.spotify.com/track/{track_id}'},
        )
        if EmotionSong.objects.filter(emotion=emotion, song=song).exists():
            continue
        last = EmotionSong.objects.filter(emotion=emotion).order_by('-position').first()
        EmotionSong.objects.create(
            emotion=emotion, song=song, position=(last.position + 1) if last else 1,
        )


def remove_songs(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    for emotion_name, data in SONGS:
        EmotionSong.objects.filter(
            emotion__name=emotion_name,
            song__title=data['title'], song__artist=data['artist'],
        ).delete()
    # Drop the Song rows this migration created; the reused one stays linked
    # to its other emotion.
    for _, data in SONGS:
        Song.objects.filter(
            title=data['title'], artist=data['artist'], emotion_links__isnull=True,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_awitin_mo_recording'),
    ]

    operations = [
        migrations.RunPython(add_songs, remove_songs),
    ]
