from django.db import migrations, models
import django.db.models.deletion


FEATURES = [
    'home',
    'profile',
    'settings',
    'about',
    'planning',
    'nafath-centers',
    'memorandum',
    'lifelong-learning',
    'other-agreements',
    'educational-content',
    'access-control',
]

ROLE_NAMES = {
    'admin': 'Admin',
    'dean': 'Dean',
    'contract': 'Contract',
    'planning': 'Planning',
    'finance': 'Finance',
}

CONTRACT_FEATURES = {
    'nafath-centers',
    'memorandum',
    'lifelong-learning',
    'other-agreements',
    'educational-content',
}


def seed_roles(apps, schema_editor):
    Role = apps.get_model('contract', 'Role')
    RolePermission = apps.get_model('contract', 'RolePermission')
    Profile = apps.get_model('contract', 'Profile')

    roles = {}
    for code, name in ROLE_NAMES.items():
        roles[code], _ = Role.objects.update_or_create(
            code=code,
            defaults={'name': name},
        )

    for code, role in roles.items():
        for feature in FEATURES:
            can_read = code == 'admin'
            can_write = code == 'admin'

            if code in {'dean', 'finance'}:
                can_read = feature != 'access-control'
            elif code == 'contract':
                can_read = feature in CONTRACT_FEATURES or feature in {'home', 'profile', 'about', 'planning'}
                can_write = feature in CONTRACT_FEATURES
            elif code == 'planning':
                can_read = feature in CONTRACT_FEATURES or feature in {'home', 'profile', 'about', 'planning'}
                can_write = feature == 'planning'

            RolePermission.objects.update_or_create(
                role=role,
                feature=feature,
                defaults={
                    'can_read': can_read,
                    'can_write': can_write,
                },
            )

    Profile.objects.filter(user__is_superuser=True, role__isnull=True).update(role=roles['admin'])


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0005_add_reminder_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature', models.SlugField(max_length=80)),
                ('can_read', models.BooleanField(default=False)),
                ('can_write', models.BooleanField(default=False)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='contract.role')),
            ],
            options={'ordering': ['role__name', 'feature']},
        ),
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profiles', to='contract.role'),
        ),
        migrations.AddConstraint(
            model_name='rolepermission',
            constraint=models.UniqueConstraint(fields=('role', 'feature'), name='unique_role_feature_permission'),
        ),
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
