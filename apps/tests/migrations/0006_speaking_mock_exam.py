from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tests', '0005_test_audio_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='part',
            field=models.IntegerField(
                blank=True,
                null=True,
                choices=[(1, 'Part 1 - Introduction & Interview'), (2, 'Part 2 - Cue Card'), (3, 'Part 3 - Discussion')],
                help_text="Faqat speaking testlar uchun to'ldiriladi (1, 2 yoki 3).",
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='prep_seconds',
            field=models.IntegerField(default=0, help_text="Tayyorlanish vaqti (soniya). Part 2 uchun odatda 60."),
        ),
        migrations.AddField(
            model_name='question',
            name='answer_seconds',
            field=models.IntegerField(default=120, help_text="Javob berish uchun ajratilgan vaqt (soniya)."),
        ),
        migrations.AddField(
            model_name='question',
            name='cue_card_points',
            field=models.TextField(blank=True, help_text="Part 2 cue card punktlari. Har birini yangi qatordan yozing."),
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['test', 'part', 'order']},
        ),
        migrations.CreateModel(
            name='ExaminerVoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Masalan: 'Emma (British)'", max_length=50)),
                ('gender', models.CharField(choices=[('male', 'Erkak'), ('female', 'Ayol')], max_length=10)),
                ('accent', models.CharField(choices=[('british', 'British'), ('american', 'American'), ('australian', 'Australian')], max_length=20)),
                ('tts_voice_id', models.CharField(help_text='TTS provayderdagi ovoz identifikatori (masalan, ElevenLabs voice_id).', max_length=100)),
                ('preview_audio_url', models.URLField(blank=True, help_text="Foydalanuvchi tanlashdan oldin eshitib ko'radigan namuna audio.", null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SpeakingSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_part', models.IntegerField(default=1)),
                ('current_question_order', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('in_progress', 'Davom etmoqda'), ('completed', 'Tugallangan'), ('abandoned', 'Tashlab ketilgan')], default='in_progress', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speaking_sessions', to='tests.test')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speaking_sessions', to=settings.AUTH_USER_MODEL)),
                ('voice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='tests.examinervoice')),
            ],
        ),
        migrations.CreateModel(
            name='SpeakingSessionAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='speaking_session_audio/')),
                ('transcript', models.TextField(blank=True)),
                ('duration_seconds', models.IntegerField(default=0)),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speaking_answers', to='tests.question')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='tests.speakingsession')),
            ],
            options={
                'ordering': ['session', 'answered_at'],
            },
        ),
        migrations.AddField(
            model_name='speakingresult',
            name='session',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='results',
                to='tests.speakingsession',
                help_text="Agar bu natija to'liq Part1-3 mock sessiyasidan bo'lsa, shu sessiyaga bog'lanadi.",
            ),
        ),
    ]