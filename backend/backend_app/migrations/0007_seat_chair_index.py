# Generated by Django 5.0.6 on 2025-05-02 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend_app', '0006_alter_seat_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='seat',
            name='chair_index',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
