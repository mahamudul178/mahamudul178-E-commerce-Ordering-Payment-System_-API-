from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.products.models import Product
from apps.orders.models import Order

User = get_user_model()


# ============================
# 1️⃣ MODEL TESTS
# ============================
class OrderModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="123456"
        )

        self.product = Product.objects.create(
            name="Test Product",
            sku="TP001",
            price=Decimal("10.00"),
            stock=100
        )

    def test_create_order(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address="Address",
            shipping_city="City",
            shipping_postal_code="12345",
            shipping_phone="0123456789",
        )

        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.total_amount, Decimal("0.00"))

    def test_add_item_to_order(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address="Address",
            shipping_city="City",
            shipping_postal_code="12345",
            shipping_phone="0123456789",
        )

        item = order.add_item(self.product, quantity=2)
        order.refresh_from_db()

        self.assertEqual(item.subtotal, Decimal("20.00"))
        self.assertEqual(order.subtotal, Decimal("20.00"))
        self.assertEqual(order.total_amount, Decimal("21.00"))  # 5% tax


# ============================
# SERIALIZER TESTS
# ============================
class OrderSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="serializer@test.com",
            password="123456"
        )

        self.product = Product.objects.create(
            name="Serializer Product",
            sku="SP001",
            price=Decimal("15.00"),
            stock=50
        )

    def test_order_create_serializer_valid(self):
        from apps.orders.serializers import OrderCreateSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/fake-url/")
        request.user = self.user

        data = {
            "shipping_address": "Address",
            "shipping_city": "City",
            "shipping_postal_code": "12345",
            "shipping_phone": "0123456789",
            "items": [
                {"product_id": self.product.id, "quantity": 3}
            ],
        }

        serializer = OrderCreateSerializer(
            data=data,
            context={"request": request}
        )

        self.assertTrue(serializer.is_valid())
        order = serializer.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal("47.25"))  # 45 + 5% tax


# ============================
# 3️⃣ VIEW / API TESTS
# ============================
class OrderViewSetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="123456"
        )

        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123"
        )

        self.product = Product.objects.create(
            name="API Product",
            sku="API001",
            price=Decimal("20.00"),
            stock=10
        )

        self.client = APIClient()

        # IMPORTANT: namespace included
        self.order_list_url = reverse("orders:order-list")

    def test_create_order_api(self):
        self.client.force_authenticate(user=self.user)

        data = {
            "shipping_address": "Address",
            "shipping_city": "City",
            "shipping_postal_code": "12345",
            "shipping_phone": "0123456789",
            "items": [
                {"product_id": self.product.id, "quantity": 2}
            ],
        }

        response = self.client.post(
            self.order_list_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(response.data["order"]["total_amount"]),
            Decimal("42.00")  # 40 + 5% tax
        )

    def test_update_order_status_api(self):
        self.client.force_authenticate(user=self.admin)

        order = Order.objects.create(
            user=self.user,
            shipping_address="A",
            shipping_city="B",
            shipping_postal_code="123",
            shipping_phone="000",
        )
        order.add_item(self.product, 1)

        url = reverse(
            "orders:order-update-status",
            kwargs={"pk": order.id}
        )

        response = self.client.post(
            url,
            {"status": Order.Status.PAID},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.paid_at)

    def test_cancel_order_api(self):
        self.client.force_authenticate(user=self.user)

        order = Order.objects.create(
            user=self.user,
            shipping_address="Addr",
            shipping_city="City",
            shipping_postal_code="12345",
            shipping_phone="012345",
        )
        order.add_item(self.product, 1)

        url = reverse(
            "orders:order-cancel",
            kwargs={"pk": order.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELED)

    def test_update_order_item_quantity_api(self):
        self.client.force_authenticate(user=self.user)

        order = Order.objects.create(
            user=self.user,
            shipping_address="Addr",
            shipping_city="City",
            shipping_postal_code="12345",
            shipping_phone="012345",
        )
        item = order.add_item(self.product, 2)

        url = reverse(
            "orders:order-update-item",
            kwargs={"pk": order.id, "item_id": item.id}
        )

        response = self.client.patch(
            url,
            {"quantity": 3},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
