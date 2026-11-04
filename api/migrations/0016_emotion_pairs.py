"""Named mixes of two emotions and their songs (therapist list, 2026-10-28).

When the app detects two emotions it plays only the songs the therapist chose
for that exact pair. All five songs are already in MIXED; this only says which
pair each one is for. The names come from the mixed-emotion literature (see
docs/PREDICTION_PIPELINE.md, section 4b); docs/music.md lists the same pairs.
"""
from django.db import migrations, models
import django.db.models.deletion

# (name, display name, emotion, emotion, song title, artist)
PAIRS = [
    ('bittersweet', 'Bittersweet', 'happy', 'sad', 'The Day You Said Goodnight', 'Hale'),
    ('romantic_melancholy', 'Romantic Melancholy', 'sad', 'romantic', 'Happier', 'Marshmello & Bastille'),
    ('tender', 'Tender', 'calm', 'romantic', 'Pasilyo', 'SunKissed Lola'),
    ('bittersweet_nostalgia', 'Bittersweet Nostalgia', 'happy', 'nostalgic', 'Castle on the Hill', 'Ed Sheeran'),
    ('challenged', 'Challenged', 'stressed', 'motivational', 'Whatever It Takes', 'Imagine Dragons'),
]


def add_pairs(apps, schema_editor):
    Emotion = apps.get_model('api', 'Emotion')
    Song = apps.get_model('api', 'Song')
    EmotionPair = apps.get_model('api', 'EmotionPair')
    EmotionPairSong = apps.get_model('api', 'EmotionPairSong')
    for name, display_name, first, second, title, artist in PAIRS:
        low, high = sorted((first, second))
        pair, _ = EmotionPair.objects.get_or_create(
            emotion_a=Emotion.objects.get(name=low),
            emotion_b=Emotion.objects.get(name=high),
            defaults={'name': name, 'display_name': display_name},
        )
        song = Song.objects.get(title=title, artist=artist)
        last = EmotionPairSong.objects.filter(pair=pair).order_by('-position').first()
        EmotionPairSong.objects.get_or_create(
            pair=pair, song=song,
            defaults={'position': (last.position + 1) if last else 1},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_remove_three_songs'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmotionPair',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=50)),
                ('emotion_a', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pairs_a', to='api.emotion')),
                ('emotion_b', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pairs_b', to='api.emotion')),
            ],
            options={
                'db_table': 'emotion_pairs',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EmotionPairSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField()),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='song_links', to='api.emotionpair')),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pair_links', to='api.song')),
            ],
            options={
                'db_table': 'emotion_pair_songs',
                'ordering': ['pair', 'position'],
            },
        ),
        migrations.AddField(
            model_name='emotionpair',
            name='songs',
            field=models.ManyToManyField(related_name='emotion_pairs', through='api.EmotionPairSong', to='api.song'),
        ),
        migrations.AddConstraint(
            model_name='emotionpairsong',
            constraint=models.UniqueConstraint(fields=('pair', 'song'), name='unique_emotion_pair_song'),
        ),
        migrations.AddConstraint(
            model_name='emotionpair',
            constraint=models.UniqueConstraint(fields=('emotion_a', 'emotion_b'), name='unique_emotion_pair'),
        ),
        # Undoing drops both tables, which removes these rows with them.
        migrations.RunPython(add_pairs, migrations.RunPython.noop),
    ]
