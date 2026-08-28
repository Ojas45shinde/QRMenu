import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("menus", "0003_alter_restaurantsubscription_end_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="restaurantsubscription",
            name="requested_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="menus.subscriptionplan",
            ),
        ),
        migrations.AddField(
            model_name="restaurantsubscription",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("pending_verification", "Pending Verification"),
                    ("active", "Active"),
                    ("rejected", "Rejected"),
                ],
                default="pending_verification",
                max_length=25,
            ),
        ),
        migrations.AlterField(
            model_name="restaurantsubscription",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]
