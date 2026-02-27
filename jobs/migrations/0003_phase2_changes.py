"""
Phase 2 model changes:
- JobStatusHistory.changed_by: make nullable (customer-initiated transitions)
- JobApproval: add approved_by_name, approved_by_ip for public approval tracking
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobstatushistory",
            name="changed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="เปลี่ยนโดย",
            ),
        ),
        migrations.AddField(
            model_name="jobapproval",
            name="approved_by_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="ชื่อลูกค้า"),
        ),
        migrations.AddField(
            model_name="jobapproval",
            name="approved_by_ip",
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name="IP ลูกค้า"),
        ),
    ]
