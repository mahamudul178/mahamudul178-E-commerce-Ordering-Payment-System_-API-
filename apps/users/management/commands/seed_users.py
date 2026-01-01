"""
Seed Users Management Command
Location: apps/users/management/commands/seed_users.py

Django management command to seed database with sample users.

Usage:
    python manage.py seed_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to seed database with sample users
    
    This command creates:
    - 1 Admin user
    - 3 Customer users with complete profiles
    """
    
    help = 'Seed database with sample users (1 admin + 3 customers)'

    def add_arguments(self, parser):
        """Add custom command arguments"""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before seeding (DANGEROUS!)',
        )

    def handle(self, *args, **options):
        """Execute the command"""
        
        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('Starting User Seeding Process'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60 + '\n'))
        
        # Handle clear option
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing users...'))
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ All users cleared\n'))
        
        # Create admin user
        self._create_admin()
        
        # Create customer users
        self._create_customers()
        
        # Summary
        self._print_summary()

    def _create_admin(self):
        """Create admin user"""
        self.stdout.write(self.style.MIGRATE_LABEL('\n1. Creating Admin User...'))
        
        admin_data = {
            'email': 'admin@ecommerce.com',
            'password': 'Admin@123',
            'first_name': 'Admin',
            'last_name': 'User',
            'phone': '01700000000'
        }
        
        if not User.objects.filter(email=admin_data['email']).exists():
            admin = User.objects.create_superuser(**admin_data)
            
            # Create profile
            UserProfile.objects.create(
                user=admin,
                address_line_1='Admin Office, Level 10',
                address_line_2='E-Commerce Building',
                city='Dhaka',
                state='Dhaka',
                postal_code='1000',
                country='Bangladesh'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ Admin created: {admin.email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'   ✗ Admin already exists: {admin_data["email"]}')
            )

    def _create_customers(self):
        """Create customer users"""
        self.stdout.write(self.style.MIGRATE_LABEL('\n2. Creating Customer Users...'))
        
        customers_data = [
            {
                'user': {
                    'email': 'customer1@example.com',
                    'password': 'Customer@123',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone': '01711111111'
                },
                'profile': {
                    'address_line_1': '123 Main Street',
                    'address_line_2': 'Apartment 4B',
                    'city': 'Dhaka',
                    'state': 'Dhaka',
                    'postal_code': '1200',
                    'country': 'Bangladesh',
                    'date_of_birth': date(1990, 5, 15)
                }
            },
            {
                'user': {
                    'email': 'customer2@example.com',
                    'password': 'Customer@123',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'phone': '01722222222'
                },
                'profile': {
                    'address_line_1': '456 Park Avenue',
                    'address_line_2': 'House #25',
                    'city': 'Chittagong',
                    'state': 'Chittagong',
                    'postal_code': '4000',
                    'country': 'Bangladesh',
                    'date_of_birth': date(1992, 8, 20)
                }
            },
            {
                'user': {
                    'email': 'customer3@example.com',
                    'password': 'Customer@123',
                    'first_name': 'Bob',
                    'last_name': 'Wilson',
                    'phone': '01733333333'
                },
                'profile': {
                    'address_line_1': '789 Lake Road',
                    'address_line_2': 'Villa #12',
                    'city': 'Sylhet',
                    'state': 'Sylhet',
                    'postal_code': '3100',
                    'country': 'Bangladesh',
                    'date_of_birth': date(1988, 12, 10)
                }
            }
        ]
        
        for idx, customer_data in enumerate(customers_data, 1):
            user_data = customer_data['user']
            profile_data = customer_data['profile']
            email = user_data['email']
            
            if not User.objects.filter(email=email).exists():
                # Create user
                user = User.objects.create_user(**user_data)
                
                # Create profile
                UserProfile.objects.create(
                    user=user,
                    **profile_data
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✓ Customer {idx} created: {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ✗ Customer {idx} already exists: {email}')
                )

    def _print_summary(self):
        """Print seeding summary"""
        total_users = User.objects.count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()
        total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Seeding Complete!'))
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nDatabase Summary:'))
        self.stdout.write(f'  Total Users: {total_users}')
        self.stdout.write(f'  Admins: {total_admins}')
        self.stdout.write(f'  Customers: {total_customers}')
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nLogin Credentials:'))
        self.stdout.write(self.style.SUCCESS('  Admin:'))
        self.stdout.write('    Email: admin@ecommerce.com')
        self.stdout.write('    Password: Admin@123')
        
        self.stdout.write(self.style.SUCCESS('\n  Customers:'))
        self.stdout.write('    Email: customer1@example.com | Password: Customer@123')
        self.stdout.write('    Email: customer2@example.com | Password: Customer@123')
        self.stdout.write('    Email: customer3@example.com | Password: Customer@123')
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nNext Steps:'))
        self.stdout.write('  1. Start the development server: python manage.py runserver')
        self.stdout.write('  2. Visit API documentation: http://localhost:8000/swagger/')
        self.stdout.write('  3. Login with any of the above credentials')
        self.stdout.write('\n' + '='*60 + '\n')