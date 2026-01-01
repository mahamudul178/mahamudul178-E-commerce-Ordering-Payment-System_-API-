"""
Seed Orders Management Command
Location: apps/orders/management/commands/seed_orders.py

Creates sample orders for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of orders to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing orders before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('Starting Order Seeding Process'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60 + '\n'))
        
        # Handle clear option
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing orders...'))
            Order.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared\n'))
        
        # Get users and products
        customers = User.objects.filter(role=User.Role.CUSTOMER)
        products = Product.objects.filter(status=Product.Status.ACTIVE, stock__gt=0)
        
        if not customers.exists():
            self.stdout.write(self.style.ERROR('❌ No customers found. Run seed_users first.'))
            return
        
        if not products.exists():
            self.stdout.write(self.style.ERROR('❌ No products found. Run seed_products first.'))
            return
        
        # Create orders
        count = options['count']
        self._create_orders(customers, products, count)
        
        # Summary
        self._print_summary()

    def _create_orders(self, customers, products, count):
        """Create sample orders"""
        self.stdout.write(self.style.MIGRATE_LABEL('\nCreating Orders...'))
        
        cities = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna']
        statuses = [
            Order.Status.PENDING,
            Order.Status.PAID,
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED
        ]
        
        created_count = 0
        
        for i in range(count):
            try:
                # Random customer
                customer = random.choice(customers)
                
                # Random city
                city = random.choice(cities)
                
                # Create order
                order = Order.objects.create(
                    user=customer,
                    shipping_address=f"{random.randint(1, 999)} Main Street, Block {chr(65 + random.randint(0, 25))}",
                    shipping_city=city,
                    shipping_postal_code=f"{random.randint(1000, 9999)}",
                    shipping_phone=f"017{random.randint(10000000, 99999999)}",
                    shipping_cost=Decimal(str(random.choice([0, 50, 100, 150]))),
                    discount=Decimal(str(random.choice([0, 0, 0, 100, 200, 500]))),
                    notes=f"Sample order #{i+1}"
                )
                
                # Add random items (2-5 items per order)
                num_items = random.randint(2, 5)
                selected_products = random.sample(list(products), min(num_items, len(products)))
                
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    
                    # Check stock
                    if quantity <= product.stock:
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price
                        )
                
                # Calculate totals
                order.calculate_totals()
                
                # Random status
                order.status = random.choice(statuses)
                
                # Set timestamps based on status
                if order.status in [Order.Status.PAID, Order.Status.PROCESSING, 
                                   Order.Status.SHIPPED, Order.Status.DELIVERED]:
                    from django.utils import timezone
                    order.paid_at = timezone.now()
                    
                    if order.status in [Order.Status.SHIPPED, Order.Status.DELIVERED]:
                        order.shipped_at = timezone.now()
                    
                    if order.status == Order.Status.DELIVERED:
                        order.delivered_at = timezone.now()
                
                order.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✓ Order {order.order_number} created '
                        f'({order.item_count} items, ৳{order.total_amount:.2f})'
                    )
                )
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ✗ Failed to create order: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} orders')
        )

    def _print_summary(self):
        """Print seeding summary"""
        total_orders = Order.objects.count()
        pending = Order.objects.filter(status=Order.Status.PENDING).count()
        paid = Order.objects.filter(status=Order.Status.PAID).count()
        processing = Order.objects.filter(status=Order.Status.PROCESSING).count()
        shipped = Order.objects.filter(status=Order.Status.SHIPPED).count()
        delivered = Order.objects.filter(status=Order.Status.DELIVERED).count()
        
        total_revenue = Order.objects.filter(
            status__in=[Order.Status.PAID, Order.Status.PROCESSING, 
                       Order.Status.SHIPPED, Order.Status.DELIVERED]
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        from django.db import models
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Seeding Complete!'))
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nOrder Summary:'))
        self.stdout.write(f'  Total Orders: {total_orders}')
        self.stdout.write(f'  Pending: {pending}')
        self.stdout.write(f'  Paid: {paid}')
        self.stdout.write(f'  Processing: {processing}')
        self.stdout.write(f'  Shipped: {shipped}')
        self.stdout.write(f'  Delivered: {delivered}')
        self.stdout.write(f'  Total Revenue: ৳{total_revenue:,.2f}')
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nNext Steps:'))
        self.stdout.write('  1. Visit: http://localhost:8000/api/orders/')
        self.stdout.write('  2. Try: http://localhost:8000/api/orders/my_orders/')
        self.stdout.write('  3. Admin: http://localhost:8000/admin/orders/')
        self.stdout.write('\n' + '='*60 + '\n')