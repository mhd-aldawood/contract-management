"""
Create (or update) a Django super admin idempotently.

Usage examples
--------------
Explicit flags:

    python manage.py create_superadmin \
        --username admin --email admin@example.com --password 'S3cret!pass'

From environment variables (handy for Docker / CI):

    DJANGO_SUPERUSER_USERNAME=admin \
    DJANGO_SUPERUSER_EMAIL=admin@example.com \
    DJANGO_SUPERUSER_PASSWORD='S3cret!pass' \
    python manage.py create_superadmin

Behavior
--------
* If the user does not exist, it is created with ``is_staff``,
  ``is_superuser`` and ``is_active`` all set to ``True``.
* If the user already exists, its flags are promoted to superuser and the
  password is only reset when ``--update-password`` is passed (or when the
  password comes from an explicit flag/env and no password was set before).
* The command is safe to run repeatedly (idempotent).
"""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

UserModel = get_user_model()


class Command(BaseCommand):
    help = "Create or promote a Django super admin (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.environ.get("DJANGO_SUPERUSER_USERNAME"),
            help="Super admin username. Falls back to DJANGO_SUPERUSER_USERNAME.",
        )
        parser.add_argument(
            "--email",
            default=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
            help="Super admin email. Falls back to DJANGO_SUPERUSER_EMAIL.",
        )
        parser.add_argument(
            "--password",
            default=os.environ.get("DJANGO_SUPERUSER_PASSWORD"),
            help="Super admin password. Falls back to DJANGO_SUPERUSER_PASSWORD.",
        )
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="Reset the password even if the user already exists.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            dest="noinput",
            help="Do not prompt for any input.",
        )

    def handle(self, *args, **options):
        username = (options.get("username") or "").strip()
        email = (options.get("email") or "").strip()
        password = options.get("password") or ""
        update_password = options.get("update_password", False)
        noinput = options.get("noinput", False)

        if not username:
            if noinput:
                raise CommandError(
                    "A username is required. Pass --username or set "
                    "DJANGO_SUPERUSER_USERNAME."
                )
            username = input("Username: ").strip()
            if not username:
                raise CommandError("Username cannot be empty.")

        if not email and not noinput:
            email = input("Email: ").strip()

        if not password:
            if noinput:
                raise CommandError(
                    "A password is required. Pass --password or set "
                    "DJANGO_SUPERUSER_PASSWORD."
                )
            from getpass import getpass

            password = getpass("Password: ")
            confirm = getpass("Password (again): ")
            if password != confirm:
                raise CommandError("Passwords do not match.")
            if not password:
                raise CommandError("Password cannot be empty.")

        self._run(
            username=username,
            email=email,
            password=password,
            update_password=update_password,
        )

    @transaction.atomic
    def _run(self, *, username, email, password, update_password):
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            user = None

        if user is None:
            user = UserModel(username=username, email=email)
            if hasattr(user, "is_staff"):
                user.is_staff = True
            if hasattr(user, "is_superuser"):
                user.is_superuser = True
            if hasattr(user, "is_active"):
                user.is_active = True
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Super admin '{username}' created successfully."
                )
            )
            return

        changed_fields = []
        if email and user.email != email:
            user.email = email
            changed_fields.append("email")
        if hasattr(user, "is_staff") and not user.is_staff:
            user.is_staff = True
            changed_fields.append("is_staff")
        if hasattr(user, "is_superuser") and not user.is_superuser:
            user.is_superuser = True
            changed_fields.append("is_superuser")
        if hasattr(user, "is_active") and not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")

        # Reset the password when explicitly requested, or when the account
        # had no usable password yet.
        if update_password or not user.has_usable_password():
            user.set_password(password)
            changed_fields.append("password")

        if changed_fields:
            user.save(update_fields=changed_fields)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Super admin '{username}' updated "
                    f"({', '.join(changed_fields)})."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Super admin '{username}' already exists; nothing to change. "
                    "Use --update-password to reset the password."
                )
            )
