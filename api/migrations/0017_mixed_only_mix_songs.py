"""Keep only the named mixes' songs in MIXED (team decision, 2026-10-30).

MIXED is now split into the five named mixes (Bittersweet, Tender, Challenged,
Bittersweet Nostalgia, Romantic Melancholy), so the five MIXED songs that belong
to none of them are no longer recommended. Only the emotion link is removed;
the Song rows stay, so history and favorites that point at them still work.
The songs after each removed one move up. Undoing puts each back at its old
position. docs/music.md lists the same change.
"""
from django.db import migrations

# (title, artist, position in MIXED before this migration)
REMOVALS = [
    ('Kahit Ayaw Mo Na', 'This Band', 3),
    ('The Night We Met', 'Lord Huron', 7),
    ('Married Life', 'Michael Giacchino', 8),
    ('Forget Her', 'Jeff Buckley', 9),
    ('Palagi', 'TJ Monterde', 10),
]


def _renumber(EmotionSong, emotion):
    for position, link in enumerate(
        EmotionSong.objects.filter(emotion=emotion).order_by('position', 'id'), start=1,
    ):
        if link.position != position:
            link.position = position
            link.save(update_fields=['position'])


def remove_songs(apps, schema_editor):
    Emotion = apps.get_model('api', 'Emotion')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    mixed = Emotion.objects.get(name='mixed')
    for title, artist, _ in REMOVALS:
        EmotionSong.objects.filter(
            emotion=mixed, song__title=title, song__artist=artist,
        ).delete()
    _renumber(EmotionSong, mixed)


def restore_songs(apps, schema_editor):
    Emotion = apps.get_model('api', 'Emotion')
    Song = apps.get_model('api', 'Song')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    mixed = Emotion.objects.get(name='mixed')
    for title, artist, position in REMOVALS:
        song = Song.objects.get(title=title, artist=artist)
        if EmotionSong.objects.filter(emotion=mixed, song=song).exists():
            continue
        for link in EmotionSong.objects.filter(emotion=mixed, position__gte=position):
            link.position += 1
            link.save(update_fields=['position'])
        EmotionSong.objects.create(emotion=mixed, song=song, position=position)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_emotion_pairs'),
    ]

    operations = [
        migrations.RunPython(remove_songs, restore_songs),
    ]
