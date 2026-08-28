import uuid

from django.db import migrations, models


def backfill_access_tokens(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.filter(access_token__isnull=True):
        order.access_token = uuid.uuid4()
        order.save(update_fields=["access_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        # Step 1: add the column as nullable so existing rows aren't broken.
        migrations.AddField(
            model_name="order",
            name="access_token",
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: backfill a unique token for every existing order.
        migrations.RunPython(backfill_access_tokens, migrations.RunPython.noop),
        # Step 3: now that every row has a value, enforce NOT NULL + UNIQUE
        # and switch on the default for all future inserts.
        migrations.AlterField(
            model_name="order",
            name="access_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
