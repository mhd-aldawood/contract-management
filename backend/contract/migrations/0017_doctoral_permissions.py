from django.db import migrations


def seed_permissions(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    Permission = apps.get_model('contract', 'RolePermission')
    for role in Role.objects.all():
        read = role.code in {'admin', 'dean', 'finance', 'planning', 'contract'}
        Permission.objects.get_or_create(role=role, feature='doctoral-contracts', defaults={
            'can_read': read, 'can_write': role.code in {'admin', 'contract'}, 'can_download': read,
        })


class Migration(migrations.Migration):
    dependencies = [('contract', '0016_doctoralcontract_and_more')]
    operations = [migrations.RunPython(seed_permissions, migrations.RunPython.noop)]
