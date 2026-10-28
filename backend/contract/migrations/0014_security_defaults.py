from django.db import migrations


def initialize_security(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    Permission = apps.get_model('contract', 'RolePermission')
    files = {'planning', 'finance', 'dean', 'nafath-centers', 'lifelong-learning',
             'educational-content', 'other-agreements', 'memorandum'}
    # Preserve existing Read/Write choices. Custom roles require an explicit download grant.
    Permission.objects.filter(role__code__in=['admin', 'dean', 'contract', 'planning', 'finance'],
                              feature__in=files, can_read=True).update(can_download=True)
    for role in Role.objects.all():
        Permission.objects.get_or_create(role=role, feature='security-settings', defaults={
            'can_read': role.code == 'admin', 'can_write': role.code == 'admin',
        })
    apps.get_model('contract', 'SecurityPolicy').objects.get_or_create(pk=1)
    # Legacy tokens have no expiry and must not remain valid after this upgrade.
    apps.get_model('authtoken', 'Token').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [('contract', '0013_loginattempt_securitypolicy_and_more'), ('authtoken', '0004_alter_tokenproxy_options')]
    operations = [migrations.RunPython(initialize_security, migrations.RunPython.noop)]
