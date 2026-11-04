"""Five songs for each named mix (therapist list, 2026-10-30).

Each mix had one song (0016); docs/music.md now gives five per mix, 25 in all.
This sets every mix's list in the therapist's order. Songs already in the
collection are reused by title and artist; the rest are added. Each new song's
Spotify recording is the original release, looked up by exact title and
artist.

Undoing removes the added songs and puts each mix back to its one 0016 song.
"""
from django.db import migrations

# Songs not yet in the collection.
NEW_SONGS = [
    {'title': 'Multo', 'artist': 'Cup of Joe',
     'spotify_track_id': '4cBm8rv2B5BJWU2pDaHVbF', 'album': 'Multo',
     'image': 'https://i.scdn.co/image/ab67616d0000b273394048503e3be0e65e962638',
     'duration_ms': 237692},
    {'title': 'Lifetime', 'artist': 'Ben&Ben',
     'spotify_track_id': '3X9c4tBzSdGhlO4Fx3WYgW', 'album': 'Lifetime',
     'image': 'https://i.scdn.co/image/ab67616d0000b273b83f0ca0165387681bf9f8c6',
     'duration_ms': 171527},
    {'title': 'Tahanan', 'artist': 'Adie',
     'spotify_track_id': '5CUQnKjA6nlteCnxMKsjIu', 'album': 'Tahanan',
     'image': 'https://i.scdn.co/image/ab67616d0000b273fc33995c8086aed744eedc1a',
     'duration_ms': 293727},
    {'title': 'Mahika', 'artist': 'Adie & Janine Berdin',
     'spotify_track_id': '47sq83n5WN22ZzYnGn8aTy', 'album': 'Mahika',
     'image': 'https://i.scdn.co/image/ab67616d0000b273e529281ba0fa960297a26c94',
     'duration_ms': 201951},
    {'title': 'Tadhana', 'artist': 'Up Dharma Down',
     'spotify_track_id': '6FIEuf1JIzmCtach0gXpeG', 'album': 'Capacities',
     'image': 'https://i.scdn.co/image/ab67616d0000b273c37604dd465e90d386feb4bf',
     'duration_ms': 222446},
    {'title': 'Karera', 'artist': 'BINI',
     'spotify_track_id': '6xfsvHFXr8GgRzaFAkmjAY', 'album': 'Karera',
     'image': 'https://i.scdn.co/image/ab67616d0000b2733c8cf1ec61e1b3ab4ab3daeb',
     'duration_ms': 268474},
    {'title': 'The Climb', 'artist': 'Miley Cyrus',
     'spotify_track_id': '0V8FYVlBFuXXTIvRnMbZyS', 'album': 'Hannah Montana The Movie',
     'image': 'https://i.scdn.co/image/ab67616d0000b2730e8ba185f3e9f15630a7b5fb',
     'duration_ms': 236066},
    {'title': 'Unstoppable', 'artist': 'Sia',
     'spotify_track_id': '2J2Z1SkXYghSajLibnQHOa', 'album': 'This Is Acting',
     'image': 'https://i.scdn.co/image/ab67616d0000b273b9bea8700ca3c305eb9569a3',
     'duration_ms': 217746},
    {'title': 'The Nights', 'artist': 'Avicii',
     'spotify_track_id': '0ct6r3EGTcMLPtrXHDvVjc', 'album': 'The Days / Nights',
     'image': 'https://i.scdn.co/image/ab67616d0000b2730ae4f4d42e4a09f3a29f64ad',
     'duration_ms': 176658},
    {'title': 'Kabisado', 'artist': 'IV OF SPADES',
     'spotify_track_id': '4z928BtE4j1bjhcX9RU44M', 'album': 'Andalucia',
     'image': 'https://i.scdn.co/image/ab67616d0000b27314708b669227cf0b2c458946',
     'duration_ms': 207920},
    {'title': '1990', 'artist': 'Uncle Dags',
     'spotify_track_id': '5iSyPFZyJUh6Dedbg6Gpvq', 'album': '1990',
     'image': 'https://i.scdn.co/image/ab67616d0000b273e8426efe67293d490b08d1af',
     'duration_ms': 217161},
    {'title': 'bittersweet', 'artist': 'Madison Beer',
     'spotify_track_id': '3A02hWQ2ebOFDWSbAMNnpw', 'album': 'bittersweet',
     'image': 'https://i.scdn.co/image/ab67616d0000b2732fb3d517253228abf2468f74',
     'duration_ms': 202795},
    {'title': 'Say You Love Me', 'artist': 'Jessie Ware',
     'spotify_track_id': '71AATBHZGo82EnjZnG53Zx', 'album': 'Tough Love',
     'image': 'https://i.scdn.co/image/ab67616d0000b2731c021b680cabd75c57a99679',
     'duration_ms': 257483},
]

# Each mix's songs in the therapist's order (position 1..5).
MIX_SONGS = {
    'bittersweet': [
        ('The Day You Said Goodnight', 'Hale'),
        ('Married Life', 'Michael Giacchino'),
        ('Kathang Isip', 'Ben&Ben'),
        ('Multo', 'Cup of Joe'),
        ('Lifetime', 'Ben&Ben'),
    ],
    'tender': [
        ('Palagi', 'TJ Monterde'),
        ('Pasilyo', 'SunKissed Lola'),
        ('Tahanan', 'Adie'),
        ('Mahika', 'Adie & Janine Berdin'),
        ('Tadhana', 'Up Dharma Down'),
    ],
    'challenged': [
        ('Whatever It Takes', 'Imagine Dragons'),
        ('Karera', 'BINI'),
        ('The Climb', 'Miley Cyrus'),
        ('Unstoppable', 'Sia'),
        ('Hall of Fame', 'The Script ft. will.i.am'),
    ],
    'bittersweet_nostalgia': [
        ('The Nights', 'Avicii'),
        ('Castle on the Hill', 'Ed Sheeran'),
        ('Kabisado', 'IV OF SPADES'),
        ('1990', 'Uncle Dags'),
        ('With a Smile', 'Eraserheads'),
    ],
    'romantic_melancholy': [
        ('Somebody Else', 'The 1975'),
        ('bittersweet', 'Madison Beer'),
        ('The Night We Met', 'Lord Huron'),
        ('Say You Love Me', 'Jessie Ware'),
        ('Happier', 'Marshmello & Bastille'),
    ],
}

# The one song each mix had before this migration (0016).
PREVIOUS_SONG = {
    'bittersweet': ('The Day You Said Goodnight', 'Hale'),
    'tender': ('Pasilyo', 'SunKissed Lola'),
    'challenged': ('Whatever It Takes', 'Imagine Dragons'),
    'bittersweet_nostalgia': ('Castle on the Hill', 'Ed Sheeran'),
    'romantic_melancholy': ('Happier', 'Marshmello & Bastille'),
}


def add_mix_songs(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    EmotionPair = apps.get_model('api', 'EmotionPair')
    EmotionPairSong = apps.get_model('api', 'EmotionPairSong')
    for data in NEW_SONGS:
        track_id = data['spotify_track_id']
        Song.objects.get_or_create(
            title=data['title'], artist=data['artist'],
            defaults={
                **data,
                'spotify_url': f'https://open.spotify.com/track/{track_id}',
            },
        )
    for name, songs in MIX_SONGS.items():
        pair = EmotionPair.objects.get(name=name)
        for position, (title, artist) in enumerate(songs, start=1):
            song = Song.objects.get(title=title, artist=artist)
            link, created = EmotionPairSong.objects.get_or_create(
                pair=pair, song=song, defaults={'position': position},
            )
            if not created and link.position != position:
                link.position = position
                link.save(update_fields=['position'])


def remove_mix_songs(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    EmotionPair = apps.get_model('api', 'EmotionPair')
    EmotionPairSong = apps.get_model('api', 'EmotionPairSong')
    for name, (title, artist) in PREVIOUS_SONG.items():
        pair = EmotionPair.objects.get(name=name)
        EmotionPairSong.objects.filter(pair=pair).exclude(
            song__title=title, song__artist=artist,
        ).delete()
        EmotionPairSong.objects.filter(pair=pair).update(position=1)
    for data in NEW_SONGS:
        # Only songs nothing else uses: another list may have added one since.
        Song.objects.filter(
            title=data['title'], artist=data['artist'],
            emotion_links__isnull=True, pair_links__isnull=True,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_mixed_only_mix_songs'),
    ]

    operations = [
        migrations.RunPython(add_mix_songs, remove_mix_songs),
    ]
