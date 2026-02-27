from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="line_display_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="LINE Display Name"),
        ),
    ]
