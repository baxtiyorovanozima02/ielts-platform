from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_telegramotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='streak_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='last_visit_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='xp_total',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='daily_goal_done',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='daily_goal_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
