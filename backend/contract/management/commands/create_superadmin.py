import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from contract.models import Profile, Role


class Command(BaseCommand):
    help = 'Idempotently creates the superuser configured through environment variables.'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true')

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

        if not username or not password:
            raise CommandError(
                'DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are required.'
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )

        changed_fields = []
        if not user.is_staff:
            user.is_staff = True
            changed_fields.append('is_staff')
        if not user.is_superuser:
            user.is_superuser = True
            changed_fields.append('is_superuser')
        if not user.is_active:
            user.is_active = True
            changed_fields.append('is_active')
        if email and user.email != email:
            user.email = email
            changed_fields.append('email')
        if created:
            user.set_password(password)
            changed_fields.append('password')
        if changed_fields:
            user.save(update_fields=changed_fields)

        admin_role = Role.objects.get(code='admin')
        profile, _ = Profile.objects.get_or_create(user=user)
        profile_fields = []
        if profile.role_id != admin_role.id:
            profile.role = admin_role
            profile_fields.append('role')
        if profile.must_change_password:
            profile.must_change_password = False
            profile_fields.append('must_change_password')
        if profile_fields:
            profile.save(update_fields=profile_fields)

        message = 'created' if created else 'already exists'
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {message} and has the Admin role."))
