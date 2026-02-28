from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_notification_messagetype"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jobs", "0003_phase2_changes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ผู้รับ",
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notifications",
                        to="jobs.job",
                        verbose_name="งาน",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="หัวข้อ")),
                ("message", models.TextField(blank=True, verbose_name="รายละเอียด")),
                (
                    "notif_type",
                    models.CharField(
                        choices=[
                            ("status_change", "เปลี่ยนสถานะ"),
                            ("payment", "ชำระเงิน"),
                            ("low_stock", "วัสดุใกล้หมด"),
                        ],
                        default="status_change",
                        max_length=20,
                        verbose_name="ประเภท",
                    ),
                ),
                ("is_read", models.BooleanField(db_index=True, default=False, verbose_name="อ่านแล้ว")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "การแจ้งเตือน",
                "verbose_name_plural": "การแจ้งเตือน",
                "ordering": ["-created_at"],
            },
        ),
    ]
