"""
Seed Products Management Command
Location: apps/products/management/commands/seed_products.py

Creates sample categories and products with hierarchical structure.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample categories and products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products and categories before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('Starting Product Seeding Process'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60 + '\n'))
        
        # Handle clear option
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing products and categories...'))
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared\n'))
        
        # Get admin user for created_by
        admin = User.objects.filter(is_staff=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('❌ No admin user found. Run seed_users first.'))
            return
        
        # Create hierarchical categories
        categories = self._create_categories()
        
        # Create products
        self._create_products(categories, admin)
        
        # Summary
        self._print_summary()

    def _create_categories(self):
        """Create hierarchical category structure"""
        self.stdout.write(self.style.MIGRATE_LABEL('\n1. Creating Categories...'))
        
        categories = {}
        
        # Root categories
        electronics = self._create_or_get_category('Electronics', None)
        fashion = self._create_or_get_category('Fashion', None)
        home = self._create_or_get_category('Home & Living', None)
        
        # Electronics subcategories
        mobile = self._create_or_get_category('Mobile Phones', electronics)
        laptop = self._create_or_get_category('Laptops', electronics)
        accessories = self._create_or_get_category('Accessories', electronics)
        
        # Mobile subcategories
        smartphones = self._create_or_get_category('Smartphones', mobile)
        feature_phones = self._create_or_get_category('Feature Phones', mobile)
        
        # Fashion subcategories
        men_fashion = self._create_or_get_category('Men Fashion', fashion)
        women_fashion = self._create_or_get_category('Women Fashion', fashion)
        
        # Men Fashion subcategories
        mens_shirts = self._create_or_get_category('Shirts', men_fashion)
        mens_pants = self._create_or_get_category('Pants', men_fashion)
        
        categories.update({
            'electronics': electronics,
            'fashion': fashion,
            'home': home,
            'mobile': mobile,
            'laptop': laptop,
            'accessories': accessories,
            'smartphones': smartphones,
            'feature_phones': feature_phones,
            'men_fashion': men_fashion,
            'women_fashion': women_fashion,
            'mens_shirts': mens_shirts,
            'mens_pants': mens_pants,
        })
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories)} categories\n'))
        return categories

    def _create_or_get_category(self, name, parent):
        """Create or get existing category"""
        category, created = Category.objects.get_or_create(
            name=name,
            parent=parent,
            defaults={
                'description': f'{name} category',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'   ✓ {category.get_full_path()}')
        else:
            self.stdout.write(self.style.WARNING(f'   ✗ Already exists: {name}'))
        
        return category

    def _create_products(self, categories, admin):
        """Create sample products"""
        self.stdout.write(self.style.MIGRATE_LABEL('\n2. Creating Products...'))
        
        products_data = [
            # Smartphones
            {
                'name': 'iPhone 15 Pro Max',
                'sku': 'APL-IP15PM-256',
                'description': 'Latest iPhone with A17 Pro chip, 256GB storage, Titanium design',
                'category': categories['smartphones'],
                'price': Decimal('149999.00'),
                'stock': 25,
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'sku': 'SAM-GS24U-512',
                'description': 'Flagship Samsung phone with S Pen, 512GB, 200MP camera',
                'category': categories['smartphones'],
                'price': Decimal('139999.00'),
                'stock': 30,
            },
            {
                'name': 'Google Pixel 8 Pro',
                'sku': 'GOG-P8P-256',
                'description': 'Pure Android experience, AI-powered camera, 256GB',
                'category': categories['smartphones'],
                'price': Decimal('89999.00'),
                'stock': 15,
            },
            
            # Laptops
            {
                'name': 'MacBook Pro 16" M3 Max',
                'sku': 'APL-MBP16-M3M',
                'description': 'Professional laptop with M3 Max chip, 36GB RAM, 1TB SSD',
                'category': categories['laptop'],
                'price': Decimal('349999.00'),
                'stock': 10,
            },
            {
                'name': 'Dell XPS 15',
                'sku': 'DEL-XPS15-I9',
                'description': 'Premium Windows laptop, Intel i9, 32GB RAM, RTX 4060',
                'category': categories['laptop'],
                'price': Decimal('224999.00'),
                'stock': 12,
            },
            {
                'name': 'Lenovo ThinkPad X1 Carbon',
                'sku': 'LEN-X1C-I7',
                'description': 'Business ultrabook, Intel i7, 16GB RAM, 512GB SSD',
                'category': categories['laptop'],
                'price': Decimal('169999.00'),
                'stock': 8,
            },
            
            # Accessories
            {
                'name': 'AirPods Pro (2nd Gen)',
                'sku': 'APL-APP2-WHT',
                'description': 'Active Noise Cancellation, Adaptive Audio, USB-C',
                'category': categories['accessories'],
                'price': Decimal('29999.00'),
                'stock': 50,
            },
            {
                'name': 'Samsung 45W Fast Charger',
                'sku': 'SAM-CHG45-BLK',
                'description': 'Super Fast Charging 2.0, USB-C, 45W output',
                'category': categories['accessories'],
                'price': Decimal('3999.00'),
                'stock': 100,
            },
            
            # Men's Shirts
            {
                'name': 'Cotton Casual Shirt - Blue',
                'sku': 'FSH-MCS-BLU-L',
                'description': '100% Cotton, Casual fit, Blue color, Size: L',
                'category': categories['mens_shirts'],
                'price': Decimal('1299.00'),
                'stock': 45,
            },
            {
                'name': 'Formal White Shirt',
                'sku': 'FSH-MFS-WHT-M',
                'description': 'Premium formal shirt, Wrinkle-free, Size: M',
                'category': categories['mens_shirts'],
                'price': Decimal('1899.00'),
                'stock': 35,
            },
            
            # Men's Pants
            {
                'name': 'Denim Jeans - Dark Blue',
                'sku': 'FSH-MJN-DBL-32',
                'description': 'Slim fit jeans, Dark blue wash, Size: 32',
                'category': categories['mens_pants'],
                'price': Decimal('2499.00'),
                'stock': 40,
            },
            {
                'name': 'Formal Trousers - Black',
                'sku': 'FSH-MFT-BLK-34',
                'description': 'Office wear trousers, Black, Size: 34',
                'category': categories['mens_pants'],
                'price': Decimal('2199.00'),
                'stock': 30,
            },
            
            # Home & Living
            {
                'name': 'LED Smart Bulb',
                'sku': 'HOM-LSB-RGB',
                'description': 'WiFi enabled, RGB colors, Voice control, 9W',
                'category': categories['home'],
                'price': Decimal('899.00'),
                'stock': 75,
            },
            {
                'name': 'Coffee Maker Machine',
                'sku': 'HOM-CFM-AUTO',
                'description': 'Automatic coffee maker, 12 cups, Timer function',
                'category': categories['home'],
                'price': Decimal('8999.00'),
                'stock': 20,
            },
            
            # Out of stock product
            {
                'name': 'Limited Edition Smartwatch',
                'sku': 'GAD-SMW-LTD',
                'description': 'Limited edition smartwatch, Sold out!',
                'category': categories['accessories'],
                'price': Decimal('24999.00'),
                'stock': 0,
            },
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults={
                    **product_data,
                    'created_by': admin
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✓ {product.name} (Stock: {product.stock})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ✗ Already exists: {product.name}')
                )

    def _print_summary(self):
        """Print seeding summary"""
        total_categories = Category.objects.count()
        total_products = Product.objects.count()
        active_products = Product.objects.filter(status=Product.Status.ACTIVE).count()
        out_of_stock = Product.objects.filter(status=Product.Status.OUT_OF_STOCK).count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Seeding Complete!'))
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nDatabase Summary:'))
        self.stdout.write(f'  Categories: {total_categories}')
        self.stdout.write(f'  Products: {total_products}')
        self.stdout.write(f'  Active: {active_products}')
        self.stdout.write(f'  Out of Stock: {out_of_stock}')
        
        # Show category tree
        self.stdout.write(self.style.MIGRATE_HEADING('\nCategory Tree Structure:'))
        self._print_category_tree()
        
        self.stdout.write(self.style.MIGRATE_HEADING('\nNext Steps:'))
        self.stdout.write('  1. Visit: http://localhost:8000/api/products/')
        self.stdout.write('  2. Try: http://localhost:8000/api/categories/tree/')
        self.stdout.write('  3. Admin: http://localhost:8000/admin/products/')
        self.stdout.write('\n' + '='*60 + '\n')

    def _print_category_tree(self, parent=None, prefix=''):
        """Print category tree structure"""
        categories = Category.objects.filter(parent=parent)
        
        for i, category in enumerate(categories):
            is_last = i == len(categories) - 1
            connector = '└── ' if is_last else '├── '
            
            product_count = category.products.count()
            self.stdout.write(f'{prefix}{connector}{category.name} ({product_count} products)')
            
            # Recursive call for children
            new_prefix = prefix + ('    ' if is_last else '│   ')
            self._print_category_tree(category, new_prefix)