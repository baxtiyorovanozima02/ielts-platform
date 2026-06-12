from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='topic',
            field=models.CharField(
                choices=[('Kunlik', 'Kunlik'), ('Akademik', 'Akademik'), ('IELTS', 'IELTS')],
                default='Kunlik',
                max_length=50
            ),
        ),
    ]
