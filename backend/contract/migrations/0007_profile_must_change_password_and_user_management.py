from django.db import migrations, models


def add_user_management_permissions(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    RolePermission = apps.get_model('contract', 'RolePermission')

    for role in Role.objects.all():
        RolePermission.objects.update_or_create(
            role=role,
            feature='user-management',
            defaults={
                'can_read': role.code == 'admin',
                'can_write': role.code == 'admin',
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0006_role_rolepermission_profile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(add_user_management_permissions, migrations.RunPython.noop),
    ]
