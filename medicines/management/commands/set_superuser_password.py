from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Set password for superuser'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='superadmin')
            user.set_password('superadmin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser password set successfully!'))
            self.stdout.write(f'Username: superadmin')
            self.stdout.write(f'Password: superadmin123')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Superuser not found!'))