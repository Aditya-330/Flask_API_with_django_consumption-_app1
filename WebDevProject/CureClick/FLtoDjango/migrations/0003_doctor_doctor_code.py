# Generated by Django 5.2 on 2025-04-09 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FLtoDjango', '0002_consultationtype'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='doctor_code',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True),
        ),
    ]
