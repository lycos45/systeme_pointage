# Generated by Django 5.1.5 on 2025-02-04 20:03

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_remove_employee_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='check_in_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.CharField(choices=[('on_time', "À l'heure"), ('late', 'En retard'), ('absent', 'Absent')], max_length=20),
        ),
    ]
