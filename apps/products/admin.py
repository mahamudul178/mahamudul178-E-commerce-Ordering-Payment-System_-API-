"""
Product Management Admin Configuration
Location: apps/products/admin.py

Django admin panel configuration for products and categories.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, ProductImage


class ProductImageInline(admin.TabularInline):
    """Inline admin for product images"""
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model"""
    
    list_display = [
        'name',
        'parent',
        'full_path_display',
        'depth_display',
        'product_count_display',
        'is_active',
        'created_at'
    ]
    
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def full_path_display(self, obj):
        """Display full category path"""
        return obj.get_full_path()
    full_path_display.short_description = 'Full Path'
    
    def depth_display(self, obj):
        """Display category depth"""
        depth = obj.get_depth()
        return format_html(
            '<span style="padding-left: {}px;">└─ Level {}</span>',
            depth * 20,
            depth
        )
    depth_display.short_description = 'Depth'
    
    def product_count_display(self, obj):
        """Display product count including descendants"""
        count = obj.get_all_products().count()
        return format_html(
            '<strong>{}</strong> products',
            count
        )
    product_count_display.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model"""
    
    list_display = [
        'name',
        'sku',
        'category',
        'price_display',
        'stock_display',
        'status_badge',
        'created_at'
    ]
    
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description')
        }),
        ('Categorization', {
            'fields': ('category',)
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock', 'status')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def price_display(self, obj):
        """Display formatted price"""
        return format_html(
            '<strong>৳{:,.2f}</strong>',
            obj.price
        )
    price_display.short_description = 'Price'
    
    def stock_display(self, obj):
        """Display stock with color coding"""
        if obj.stock == 0:
            color = 'red'
            icon = '✗'
        elif obj.stock <= 10:
            color = 'orange'
            icon = '⚠'
        else:
            color = 'green'
            icon = '✓'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.stock
        )
    stock_display.short_description = 'Stock'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'out_of_stock': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['activate_products', 'deactivate_products', 'mark_out_of_stock']
    
    def activate_products(self, request, queryset):
        """Bulk activate products"""
        count = queryset.update(status=Product.Status.ACTIVE)
        self.message_user(request, f'{count} product(s) activated successfully.')
    activate_products.short_description = 'Activate selected products'
    
    def deactivate_products(self, request, queryset):
        """Bulk deactivate products"""
        count = queryset.update(status=Product.Status.INACTIVE)
        self.message_user(request, f'{count} product(s) deactivated successfully.')
    deactivate_products.short_description = 'Deactivate selected products'
    
    def mark_out_of_stock(self, request, queryset):
        """Mark products as out of stock"""
        count = queryset.update(status=Product.Status.OUT_OF_STOCK, stock=0)
        self.message_user(request, f'{count} product(s) marked as out of stock.')
    mark_out_of_stock.short_description = 'Mark as out of stock'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Admin configuration for ProductImage model"""
    
    list_display = [
        'product',
        'image_thumbnail',
        'is_primary',
        'order',
        'created_at'
    ]
    
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name']
    ordering = ['product', 'order']
    
    def image_thumbnail(self, obj):
        """Display image thumbnail"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "No Image"
    image_thumbnail.short_description = 'Thumbnail'