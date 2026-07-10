from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_speaking_mock_exam'),
    ]

    operations = [
        migrations.AddField(
            model_name='examinervoice',
            name='avatar_id',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                help_text="Avatar provayderdagi (masalan, HeyGen) avatar identifikatori. Bo'sh bo'lsa standart avatar ishlatiladi.",
            ),
        ),
    ]