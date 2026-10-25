from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contract", "0004_align_agreement_budget_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreement",
            name="reminder_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="educationalcontent",
            name="reminder_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="lifelongagreement",
            name="reminder_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nafathcenteragreement",
            name="reminder_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
