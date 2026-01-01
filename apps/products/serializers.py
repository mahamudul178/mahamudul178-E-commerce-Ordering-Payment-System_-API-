"""
Product Management Serializers
Location: apps/products/serializers.py

Serializers for products, categories, and images.
"""

from rest_framework import serializers
from .models import Product, Category, ProductImage
from django.contrib.auth import get_user_model

User = get_user_model()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for nested category tree structure
    Uses DFS-generated tree data
    """
    
    children = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'full_path', 'depth', 'product_count',
            'children', 'is_active', 'created_at'
        ]
    
    def get_children(self, obj):
        """Get child categories using DFS"""
        children = obj.children.filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data
    
    def get_depth(self, obj):
        """Get category depth in tree"""
        return obj.get_depth()
    
    def get_full_path(self, obj):
        """Get full category path"""
        return obj.get_full_path()
    
    def get_product_count(self, obj):
        """Get total products in this category and descendants"""
        return obj.get_all_products().count()


class CategorySerializer(serializers.ModelSerializer):
    """Basic category serializer"""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_path = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'parent', 'parent_name', 'full_path',
            'is_active', 'product_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_full_path(self, obj):
        return obj.get_full_path()
    
    def validate_parent(self, value):
        """Prevent circular references"""
        if value:
            instance = self.instance
            if instance and value == instance:
                raise serializers.ValidationError("Category cannot be its own parent.")
            
            # Check if parent is a descendant
            if instance:
                descendants = instance.get_descendants_dfs()
                if value in descendants:
                    raise serializers.ValidationError("Cannot set descendant as parent.")
        
        return value


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        """Get full image URL"""
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view (minimal data)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku',
            'category_name', 'category_path',
            'price', 'stock', 'status',
            'is_in_stock', 'primary_image',
            'created_at'
        ]
    
    def get_category_path(self, obj):
        """Get full category path"""
        if obj.category:
            return obj.category.get_full_path()
        return None
    
    def get_primary_image(self, obj):
        """Get primary product image"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ProductImageSerializer(primary, context=self.context).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view (complete data)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.SerializerMethodField()
    category_details = CategorySerializer(source='category', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    related_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description',
            'category', 'category_name', 'category_path', 'category_details',
            'price', 'stock', 'status',
            'is_in_stock', 'is_low_stock',
            'images', 'related_products',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_category_path(self, obj):
        """Get full category path"""
        if obj.category:
            return obj.category.get_full_path()
        return None
    
    def get_related_products(self, obj):
        """Get related products using category DFS"""
        related = obj.get_related_products(limit=5)
        return ProductListSerializer(related, many=True, context=self.context).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'description',
            'category', 'price', 'stock', 'status'
        ]
    
    def validate_sku(self, value):
        """Validate SKU uniqueness"""
        instance = self.instance
        if Product.objects.filter(sku=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_stock(self, value):
        """Validate stock is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value
    
    def create(self, validated_data):
        """Create product with current user as creator"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class StockUpdateSerializer(serializers.Serializer):
    """Serializer for updating product stock"""
    
    action = serializers.ChoiceField(choices=['increase', 'decrease'])
    quantity = serializers.IntegerField(min_value=1)
    
    def validate(self, attrs):
        """Validate stock update"""
        product = self.context.get('product')
        action = attrs['action']
        quantity = attrs['quantity']
        
        if action == 'decrease' and quantity > product.stock:
            raise serializers.ValidationError(
                f"Cannot decrease stock by {quantity}. Available stock: {product.stock}"
            )
        
        return attrs
    
    def save(self):
        """Update product stock"""
        product = self.context['product']
        action = self.validated_data['action']
        quantity = self.validated_data['quantity']
        
        if action == 'increase':
            product.increase_stock(quantity)
        else:
            product.reduce_stock(quantity)
        
        return product


class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search parameters"""
    
    q = serializers.CharField(required=False, help_text="Search query")
    category = serializers.IntegerField(required=False, help_text="Category ID")
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        required=False, min_value=0
    )
    max_price = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, min_value=0
    )
    status = serializers.ChoiceField(
        choices=Product.Status.choices,
        required=False
    )
    in_stock = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'name', '-name',
            'price', '-price',
            'created_at', '-created_at',
            'stock', '-stock'
        ],
        required=False,
        default='-created_at'
    )
    
