"""Remove three songs from one emotion each (therapist list update, 2026-10-21).

ANGRY: Halaga (Parokya ni Edgar). LONELY: Weston Road Flows (Drake).
ROMANTIC: All of Me (John Legend). Only the emotion link is removed; the Song
rows stay, so history and favorites that point at them still work. The songs
after each removed one move up, so positions stay 1..n. Undoing puts each song
back at its old position. docs/music.md lists the same change.
"""
from django.db import migrations

REMOVALS = [
    ('angry', 'Halaga', 'Parokya ni Edgar', 9),
    ('lonely', 'Weston Road Flows', 'Drake', 10),
    ('romantic', 'All of Me', 'John Legend', 10),
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
    for emotion_name, title, artist, _ in REMOVALS:
        emotion = Emotion.objects.get(name=emotion_name)
        EmotionSong.objects.filter(
            emotion=emotion, song__title=title, song__artist=artist,
        ).delete()
        _renumber(EmotionSong, emotion)


def restore_songs(apps, schema_editor):
    Emotion = apps.get_model('api', 'Emotion')
    Song = apps.get_model('api', 'Song')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    for emotion_name, title, artist, position in REMOVALS:
        emotion = Emotion.objects.get(name=emotion_name)
        song = Song.objects.get(title=title, artist=artist)
        if EmotionSong.objects.filter(emotion=emotion, song=song).exists():
            continue
        for link in EmotionSong.objects.filter(emotion=emotion, position__gte=position):
            link.position += 1
            link.save(update_fields=['position'])
        EmotionSong.objects.create(emotion=emotion, song=song, position=position)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_add_new_therapist_songs'),
    ]

    operations = [
        migrations.RunPython(remove_songs, restore_songs),
    ]
