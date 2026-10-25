from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('contract', '0007_profile_must_change_password_and_user_management')]

    operations = [
        migrations.AlterField(
            model_name='agreement', name='type',
            field=models.CharField(max_length=50, default='other-agreements', choices=[
                ('other-agreements', 'Other Agreements'), ('memorandum', 'Memorandum'),
            ]),
        ),
    ]
