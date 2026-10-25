import secrets

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from contract.models import Role


class Command(BaseCommand):
    help = 'Explicitly create local role test accounts. Never runs during application startup.'

    def handle(self, *args, **options):
        call_command('seed_roles', stdout=self.stdout)
        User = get_user_model()
        for code in ['admin', 'dean', 'finance', 'contract', 'planning']:
            username = f'cm_demo_{code}'
            with transaction.atomic():
                if User.objects.filter(username=username).exists():
                    self.stdout.write(f'{username}: already exists; password and role unchanged.')
                    continue
                password = f'Cm!{secrets.token_urlsafe(10)}7'
                user = User.objects.create_user(username=username, password=password)
                user.profile.role = Role.objects.get(code=code)
                # Purpose-built test accounts can open their dashboard immediately.
                user.profile.must_change_password = False
                user.profile.save(update_fields=['role', 'must_change_password'])
            self.stdout.write(f'{code}\t{username}\t{password}')
