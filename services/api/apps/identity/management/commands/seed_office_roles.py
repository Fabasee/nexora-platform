from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.identity.office_access import OFFICE_ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Create standard Nexora Office RBAC groups without assigning users."

    def handle(self, *args, **options):
        for role in OFFICE_ROLE_PERMISSIONS:
            group, created = Group.objects.get_or_create(name=role)
            self.stdout.write(f'{"Created" if created else "Exists"}: {group.name}')
        self.stdout.write(self.style.SUCCESS("Nexora Office roles are ready. No users were assigned."))
