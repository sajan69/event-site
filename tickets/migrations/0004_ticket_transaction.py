# Generated by Django 5.1.2 on 2024-11-12 06:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_transaction_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='transaction',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='tickets.transaction'),
            preserve_default=False,
        ),
    ]
