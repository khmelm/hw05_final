# Generated by Django 2.2.19 on 2022-10-15 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20221015_1716'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['pub_date']},
        ),
        migrations.AlterOrderWithRespectTo(
            name='post',
            order_with_respect_to=None,
        ),
    ]
