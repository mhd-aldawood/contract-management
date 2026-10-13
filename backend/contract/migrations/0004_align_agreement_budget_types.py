from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contract", "0003_agreement_lifelongagreement_nafathcenteragreement_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lifelongagreement",
            name="budget_type",
            field=models.CharField(
                choices=[("current", "Current"), ("investment", "Investment")],
                default="current",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="nafathcenteragreement",
            name="budget_type",
            field=models.CharField(
                choices=[("current", "Current"), ("investment", "Investment")],
                default="current",
                max_length=16,
            ),
        ),
    ]
