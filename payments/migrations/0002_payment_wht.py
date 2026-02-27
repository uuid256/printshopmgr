from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="wht_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                verbose_name="อัตรา WHT (%)",
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="wht_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name="WHT หัก ณ ที่จ่าย",
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="wht_certificate",
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name="เลขที่หนังสือรับรอง WHT",
            ),
        ),
    ]
