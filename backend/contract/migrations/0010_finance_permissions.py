from django.db import migrations


def seed_finance_permissions(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    RolePermission = apps.get_model('contract', 'RolePermission')
    for role in Role.objects.all():
        RolePermission.objects.get_or_create(role=role, feature='finance', defaults={
            'can_read': role.code in {'admin', 'finance', 'dean'},
            'can_write': role.code in {'admin', 'finance'},
        })


class Migration(migrations.Migration):
    dependencies = [('contract', '0009_disbursement_orders')]
    operations = [migrations.RunPython(seed_finance_permissions, migrations.RunPython.noop)]
