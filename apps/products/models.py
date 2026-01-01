"""
Product Management Models
Location: apps/products/models.py

This module contains Product and Category models with hierarchical structure.
Implements DFS for category tree traversal.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Category(models.Model):
    """
    Hierarchical Category Model using Adjacency List
    
    Supports unlimited depth category tree.
    Uses DFS for traversal and recommendations.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        verbose_name='Category Name'
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        verbose_name='URL Slug'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Parent Category'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active Status'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.get_full_path()
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """
        Get full category path (e.g., Electronics > Mobile > Smartphones)
        """
        path = [self.name]
        parent = self.parent
        
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        
        return ' > '.join(path)
    
    def get_depth(self):
        """Get depth level of category in tree"""
        depth = 0
        parent = self.parent
        
        while parent:
            depth += 1
            parent = parent.parent
        
        return depth
    
    def get_ancestors(self):
        """
        Get all ancestor categories
        Returns list from root to immediate parent
        """
        ancestors = []
        parent = self.parent
        
        while parent:
            ancestors.insert(0, parent)
            parent = parent.parent
        
        return ancestors
    
    def get_descendants_dfs(self):
        """
        Get all descendant categories using DFS (Depth-First Search)
        
        This is the REQUIRED DFS algorithm implementation.
        Returns flat list of all descendants.
        """
        descendants = []
        
        def dfs(category):
            """Recursive DFS traversal"""
            for child in category.children.filter(is_active=True):
                descendants.append(child)
                dfs(child)  # Recursive call
        
        dfs(self)
        return descendants
    
    def get_category_tree_dfs(self):
        """
        Get category tree structure using DFS
        Returns nested dictionary structure
        """
        def build_tree_dfs(category):
            """Build tree structure recursively"""
            return {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'children': [
                    build_tree_dfs(child) 
                    for child in category.children.filter(is_active=True)
                ]
            }
        
        return build_tree_dfs(self)
    
    def get_all_products(self):
        """
        Get all products in this category and all descendant categories
        Uses DFS to traverse tree
        """
        from django.db.models import Q
        
        # Start with products in current category
        category_ids = [self.id]
        
        # Get all descendant category IDs using DFS
        descendants = self.get_descendants_dfs()
        category_ids.extend([cat.id for cat in descendants])
        
        # Get all products from these categories
        return Product.objects.filter(category_id__in=category_ids)
    
    @classmethod
    def get_root_categories(cls):
        """Get all root categories (no parent)"""
        return cls.objects.filter(parent=None, is_active=True)
    
    @classmethod
    def build_full_tree_dfs(cls):
        """
        Build complete category tree using DFS
        Returns list of root categories with nested children
        """
        roots = cls.get_root_categories()
        return [root.get_category_tree_dfs() for root in roots]


class Product(models.Model):
    """
    Product Model with category relationship and stock management
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'
    
    # Basic Information
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Product Name'
    )
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='URL Slug'
    )
    
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='SKU (Stock Keeping Unit)'
    )
    
    description = models.TextField(
        verbose_name='Product Description'
    )
    
    # Category
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name='Category'
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Price'
    )
    
    # Stock Management
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock Quantity'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Product Status'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
        verbose_name='Created By'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and update status based on stock"""
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-update status based on stock
        if self.stock == 0 and self.status == self.Status.ACTIVE:
            self.status = self.Status.OUT_OF_STOCK
        elif self.stock > 0 and self.status == self.Status.OUT_OF_STOCK:
            self.status = self.Status.ACTIVE
        
        super().save(*args, **kwargs)
        logger.info(f"Product saved: {self.name} (SKU: {self.sku})")
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0 and self.status == self.Status.ACTIVE
    
    @property
    def is_low_stock(self, threshold=10):
        """Check if product has low stock"""
        return 0 < self.stock <= threshold
    
    def reduce_stock(self, quantity):
        """
        Reduce stock by given quantity
        Used after successful payment
        """
        if quantity > self.stock:
            raise ValueError(f"Insufficient stock. Available: {self.stock}, Requested: {quantity}")
        
        self.stock -= quantity
        if self.stock == 0:
            self.status = self.Status.OUT_OF_STOCK
        self.save()
        
        logger.info(f"Stock reduced for {self.name}: -{quantity}, Remaining: {self.stock}")
    
    def increase_stock(self, quantity):
        """Increase stock by given quantity"""
        self.stock += quantity
        if self.stock > 0 and self.status == self.Status.OUT_OF_STOCK:
            self.status = self.Status.ACTIVE
        self.save()
        
        logger.info(f"Stock increased for {self.name}: +{quantity}, Total: {self.stock}")
    
    def get_related_products(self, limit=5):
        """
        Get related products from same category and parent categories
        Uses category DFS for finding related products
        """
        if not self.category:
            return Product.objects.none()
        
        # Get products from same category
        related = Product.objects.filter(
            category=self.category,
            status=self.Status.ACTIVE
        ).exclude(id=self.id)
        
        # If not enough, get from parent category
        if related.count() < limit and self.category.parent:
            parent_products = Product.objects.filter(
                category=self.category.parent,
                status=self.Status.ACTIVE
            ).exclude(id=self.id)
            
            related = related.union(parent_products)
        
        return related[:limit]


class ProductImage(models.Model):
    """Product Images Model"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Product'
    )
    
    image = models.ImageField(
        upload_to='products/%Y/%m/',
        verbose_name='Product Image'
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Primary Image'
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name='Display Order'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary image per product"""
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)