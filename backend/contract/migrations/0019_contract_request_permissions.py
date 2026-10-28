from django.db import migrations


def seed_permissions(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    Permission = apps.get_model('contract', 'RolePermission')
    for role in Role.objects.all():
        Permission.objects.get_or_create(role=role, feature='contract-requests', defaults={
            'can_read': role.code in {'admin', 'contract', 'dean', 'planning', 'finance'},
            'can_write': role.code in {'admin', 'contract'}, 'can_download': False,
        })


class Migration(migrations.Migration):
    dependencies = [('contract', '0018_contractrequest_bidminute')]
    operations = [migrations.RunPython(seed_permissions, migrations.RunPython.noop)]
