"""Initial notifications models: CustomerLineBinding and NotificationLog."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("jobs", "0003_phase2_changes"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerLineBinding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_user_id", models.CharField(max_length=50, unique=True, verbose_name="LINE User ID")),
                ("display_name", models.CharField(blank=True, max_length=100, verbose_name="ชื่อ LINE")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="line_binding",
                        to="customers.customer",
                        verbose_name="ลูกค้า",
                    ),
                ),
            ],
            options={
                "verbose_name": "LINE Binding",
                "verbose_name_plural": "LINE Bindings",
            },
        ),
        migrations.CreateModel(
            name="NotificationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_user_id", models.CharField(max_length=50, verbose_name="LINE User ID")),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("status_change", "เปลี่ยนสถานะ"),
                            ("proof_ready", "proof พร้อม"),
                            ("approval_reminder", "แจ้งเตือนอนุมัติ"),
                        ],
                        max_length=20,
                        verbose_name="ประเภท",
                    ),
                ),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                ("success", models.BooleanField(default=True)),
                ("error_message", models.TextField(blank=True)),
                (
                    "job",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notification_logs",
                        to="jobs.job",
                        verbose_name="งาน",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notification Log",
                "verbose_name_plural": "Notification Logs",
                "ordering": ["-sent_at"],
            },
        ),
    ]
