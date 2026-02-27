from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationlog",
            name="message_type",
            field=models.CharField(
                choices=[
                    ("status_change", "เปลี่ยนสถานะ"),
                    ("proof_ready", "proof พร้อม"),
                    ("approval_reminder", "แจ้งเตือนอนุมัติ"),
                    ("payment_reminder", "แจ้งเตือนชำระเงิน"),
                    ("daily_summary", "สรุปประจำวัน"),
                ],
                max_length=20,
                verbose_name="ประเภท",
            ),
        ),
    ]
