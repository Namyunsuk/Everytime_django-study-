# Generated by Django 3.2.8 on 2021-11-02 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='regist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('etaId', models.CharField(max_length=20)),
                ('etaPw', models.CharField(max_length=30)),
                ('ssgId', models.CharField(max_length=20)),
                ('ssgPw', models.CharField(max_length=30)),
            ],
        ),
    ]
