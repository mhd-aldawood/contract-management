from django.db import migrations


def seed_dean_permissions(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    RolePermission = apps.get_model('contract', 'RolePermission')
    for role in Role.objects.all():
        RolePermission.objects.get_or_create(role=role, feature='dean', defaults={
            'can_read': role.code in {'admin', 'dean'},
            'can_write': role.code in {'admin', 'dean'},
        })


class Migration(migrations.Migration):
    dependencies = [('contract', '0011_disbursement_order_details')]
    operations = [migrations.RunPython(seed_dean_permissions, migrations.RunPython.noop)]
