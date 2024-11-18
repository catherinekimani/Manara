# Generated by Django 5.1.2 on 2024-11-01 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('COMMUTER', 'Commuter'), ('SACCO_OWNER', 'Sacco Owner'), ('OPERATOR', 'Operator')], default='COMMUTER', max_length=20, verbose_name='user type'),
        ),
    ]