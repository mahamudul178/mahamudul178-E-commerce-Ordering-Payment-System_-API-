"""
Product Management Views
Location: apps/products/views.py

Views for products and categories with Redis caching.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Product, Category, ProductImage
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    CategorySerializer,
    CategoryTreeSerializer,
    ProductImageSerializer,
    StockUpdateSerializer,
    ProductSearchSerializer
)
from apps.users.permissions import IsAdmin

logger = logging.getLogger(__name__)

# Cache timeout (15 minutes)
CACHE_TTL = 60 * 15


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations
    
    Implements DFS for category tree and caching
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_permissions(self):
        """Admin-only for create/update/delete, public for read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Use tree serializer for tree action"""
        if self.action == 'tree':
            return CategoryTreeSerializer
        return CategorySerializer
    
    @swagger_auto_schema(
        operation_description="Get complete category tree using DFS",
        responses={200: CategoryTreeSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get complete category tree structure using DFS
        
        Cached in Redis for performance
        """
        cache_key = 'category_tree_full'
        
        # Try to get from cache
        cached_tree = cache.get(cache_key)
        if cached_tree:
            logger.info("Category tree retrieved from cache")
            return Response({
                'message': 'Category tree retrieved successfully (cached)',
                'tree': cached_tree
            })
        
        # Build tree using DFS
        tree = Category.build_full_tree_dfs()
        
        # Cache the result
        cache.set(cache_key, tree, CACHE_TTL)
        logger.info("Category tree built using DFS and cached")
        
        return Response({
            'message': 'Category tree retrieved successfully',
            'tree': tree
        })
    
    @swagger_auto_schema(
        operation_description="Get all root categories (no parent)",
        responses={200: CategorySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get all root categories"""
        cache_key = 'category_roots'
        
        # Try cache first
        cached_roots = cache.get(cache_key)
        if cached_roots:
            return Response({
                'message': 'Root categories retrieved (cached)',
                'categories': cached_roots
            })
        
        roots = Category.get_root_categories()
        serializer = self.get_serializer(roots, many=True)
        
        # Cache the result
        cache.set(cache_key, serializer.data, CACHE_TTL)
        
        return Response({
            'message': 'Root categories retrieved successfully',
            'categories': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get all descendants of a category using DFS",
        responses={200: CategorySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def descendants(self, request, slug=None):
        """Get all descendant categories using DFS"""
        category = self.get_object()
        cache_key = f'category_descendants_{slug}'
        
        # Try cache
        cached_descendants = cache.get(cache_key)
        if cached_descendants:
            return Response({
                'message': f'Descendants of {category.name} (cached)',
                'descendants': cached_descendants
            })
        
        # Get descendants using DFS
        descendants = category.get_descendants_dfs()
        serializer = self.get_serializer(descendants, many=True)
        
        # Cache
        cache.set(cache_key, serializer.data, CACHE_TTL)
        
        return Response({
            'message': f'Descendants of {category.name}',
            'count': len(descendants),
            'descendants': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get all products in category and descendants",
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get all products in this category and descendants"""
        category = self.get_object()
        products = category.get_all_products()
        
        serializer = ProductListSerializer(
            products,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'message': f'Products in {category.name}',
            'count': products.count(),
            'products': serializer.data
        })
    
    def perform_create(self, serializer):
        """Clear cache when creating category"""
        serializer.save()
        self._clear_category_cache()
    
    def perform_update(self, serializer):
        """Clear cache when updating category"""
        serializer.save()
        self._clear_category_cache()
    
    def perform_destroy(self, instance):
        """Clear cache when deleting category"""
        instance.delete()
        self._clear_category_cache()
    
    def _clear_category_cache(self):
        """Clear all category-related caches"""
        cache.delete('category_tree_full')
        cache.delete('category_roots')
        # Clear all descendant caches
        for category in Category.objects.all():
            cache.delete(f'category_descendants_{category.slug}')
        logger.info("Category cache cleared")


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations
    
    Includes search, filtering, and Redis caching
    """
    queryset = Product.objects.select_related('category', 'created_by').prefetch_related('images')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_permissions(self):
        """Admin-only for create/update/delete, public for read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_stock']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'update_stock':
            return StockUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        """Custom queryset with filtering"""
        queryset = super().get_queryset()
        
        # Filter by stock availability
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock__gt=0, status=Product.Status.ACTIVE)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock=0)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve product with caching"""
        slug = kwargs.get('slug')
        cache_key = f'product_detail_{slug}'
        
        # Try cache first
        cached_product = cache.get(cache_key)
        if cached_product:
            logger.info(f"Product {slug} retrieved from cache")
            return Response({
                'message': 'Product retrieved successfully (cached)',
                'product': cached_product
            })
        
        # Get from database
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache the result
        cache.set(cache_key, serializer.data, CACHE_TTL)
        logger.info(f"Product {slug} cached")
        
        return Response({
            'message': 'Product retrieved successfully',
            'product': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Search products with filters",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Search query"),
            openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Category ID"),
            openapi.Parameter('min_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Minimum price"),
            openapi.Parameter('max_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Maximum price"),
            openapi.Parameter('in_stock', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description="In stock only"),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced product search with caching
        """
        query = request.query_params.get('q', '')
        
        # Build cache key from query params
        cache_key = f'product_search_{hash(str(request.query_params))}'
        
        # Try cache
        cached_results = cache.get(cache_key)
        if cached_results:
            logger.info(f"Search results retrieved from cache: {query}")
            return Response({
                'message': 'Search results (cached)',
                'results': cached_results
            })
        
        # Perform search
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query)
            )
        
        serializer = ProductListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        
        # Cache results
        cache.set(cache_key, serializer.data, CACHE_TTL // 2)  # Cache for 7.5 minutes
        
        return Response({
            'message': f'Search results for "{query}"',
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Update product stock",
        request_body=StockUpdateSerializer,
        responses={200: ProductDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def update_stock(self, request, slug=None):
        """Update product stock (increase/decrease)"""
        product = self.get_object()
        serializer = StockUpdateSerializer(
            data=request.data,
            context={'product': product}
        )
        serializer.is_valid(raise_exception=True)
        updated_product = serializer.save()
        
        # Clear cache
        self._clear_product_cache(slug)
        
        return Response({
            'message': 'Stock updated successfully',
            'product': ProductDetailSerializer(updated_product, context={'request': request}).data
        })
    
    @swagger_auto_schema(
        operation_description="Get related products",
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Get related products using category DFS"""
        product = self.get_object()
        cache_key = f'product_related_{slug}'
        
        # Try cache
        cached_related = cache.get(cache_key)
        if cached_related:
            return Response({
                'message': 'Related products (cached)',
                'products': cached_related
            })
        
        related = product.get_related_products(limit=5)
        serializer = ProductListSerializer(
            related,
            many=True,
            context={'request': request}
        )
        
        # Cache
        cache.set(cache_key, serializer.data, CACHE_TTL)
        
        return Response({
            'message': 'Related products',
            'count': len(serializer.data),
            'products': serializer.data
        })
    
    def perform_create(self, serializer):
        """Clear cache when creating product"""
        serializer.save()
        self._clear_all_product_cache()
    
    def perform_update(self, serializer):
        """Clear cache when updating product"""
        product = serializer.save()
        self._clear_product_cache(product.slug)
    
    def perform_destroy(self, instance):
        """Clear cache when deleting product"""
        slug = instance.slug
        instance.delete()
        self._clear_product_cache(slug)
    
    def _clear_product_cache(self, slug):
        """Clear cache for specific product"""
        cache.delete(f'product_detail_{slug}')
        cache.delete(f'product_related_{slug}')
        logger.info(f"Cache cleared for product: {slug}")
    
    def _clear_all_product_cache(self):
        """Clear all product caches"""
        # In production, use cache.delete_pattern('product_*')
        # For now, just log
        logger.info("All product cache should be cleared")


class ProductImageViewSet(viewsets.ModelViewSet):
    """ViewSet for Product Images"""
    
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        """Filter images by product if provided"""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset