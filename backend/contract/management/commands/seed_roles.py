from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from contract.models import Profile, Role, RolePermission
from contract.rbac import FEATURES


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
ADMIN_ONLY_FEATURES = {'access-control', 'user-management'}


def default_access(role_code, feature):
    if role_code == 'admin':
        return True, True
    if feature == 'dean':
        return role_code == 'dean', role_code == 'dean'
    if feature == 'finance':
        return role_code in {'finance', 'dean'}, role_code == 'finance'
    if role_code in {'dean', 'finance'}:
        return feature not in ADMIN_ONLY_FEATURES, False
    if role_code == 'contract':
        return (
            feature in CONTRACT_FEATURES or feature in {'home', 'profile', 'about', 'planning'},
            feature in CONTRACT_FEATURES,
        )
    if role_code == 'planning':
        return (
            feature in CONTRACT_FEATURES or feature in {'home', 'profile', 'about', 'planning'},
            feature == 'planning',
        )
    return False, False


class Command(BaseCommand):
    help = 'Idempotently creates the application roles and missing feature permissions.'

    def handle(self, *args, **options):
        roles = {}
        for code, name in ROLE_NAMES.items():
            roles[code], _ = Role.objects.update_or_create(
                code=code,
                defaults={'name': name},
            )

        for code, role in roles.items():
            for feature in FEATURES:
                feature_code = feature['code']
                can_read, can_write = default_access(code, feature_code)
                RolePermission.objects.get_or_create(
                    role=role,
                    feature=feature_code,
                    defaults={
                        'can_read': can_read,
                        'can_write': can_write,
                    },
                )

        User = get_user_model()
        for user in User.objects.filter(is_superuser=True):
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.role_id is None:
                profile.role = roles['admin']
                profile.save(update_fields=['role'])

        self.stdout.write(self.style.SUCCESS('Roles and permissions are ready.'))
