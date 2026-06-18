from django.test import TestCase
from .models import Tenant, Branch, Product, ProductUnit, Sale, UserProfile
import uuid

class ModelTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main Branch")
        self.product = Product.objects.create(tenant=self.tenant, name="Laptop", barcode="123456789")
        self.product_unit = ProductUnit.objects.create(
            product=self.product,
            unit_name="Piece",
            retail_price=1000.00,
            wholesale_price=900.00
        )

    def test_tenant_creation(self):
        self.assertEqual(self.tenant.name, "Test Tenant")

    def test_sale_uuid(self):
        sale = Sale.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            payment_mode='CASH',
            status='PAID',
            total_amount=1000.00
        )
        self.assertIsInstance(sale.id, uuid.UUID)

    def test_user_role(self):
        user = UserProfile.objects.create_user(
            username='cashier1',
            password='password123',
            role='CASHIER',
            tenant=self.tenant,
            branch=self.branch
        )
        self.assertEqual(user.role, 'CASHIER')
