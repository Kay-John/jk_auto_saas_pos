import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, default='UGX')
    subscription_status = models.CharField(max_length=20, default='trial')
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=100)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('tenant', 'barcode')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-calculate low stock threshold if not manually set or as a basic logic
        # For now, let's say it defaults to 10% of some average monthly volume (placeholder logic)
        # Or just ensure it's at least 5
        if not self.low_stock_threshold:
            self.low_stock_threshold = 5
        super().save(*args, **kwargs)

class ProductUnit(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='units')
    unit_name = models.CharField(max_length=50)  # e.g., Piece, Box, Carton
    conversion_factor = models.DecimalField(max_digits=10, decimal_places=2, default=1) # conversion to base unit
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.unit_name})"

class Supplier(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_info = models.TextField(blank=True)

    def __str__(self):
        return self.name

class BranchStock(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stocks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='branch_stocks')
    quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Quantity in base units

    class Meta:
        unique_together = ('branch', 'product')

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2) # Quantity in the selected unit
    quantity_base = models.DecimalField(max_digits=15, decimal_places=2) # Calculated quantity in base units
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Sale(models.Model):
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CARD', 'Card'),
    ]
    TRANSACTION_STATUS = [
        ('PAID', 'Paid'),
        ('CREDIT', 'Credit'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('RENT', 'Rent'),
        ('UTILITIES', 'Utilities'),
        ('SALARIES', 'Salaries'),
        ('LOGISTICS', 'Logistics'),
        ('MARKETING', 'Marketing'),
        ('MISC', 'Miscellaneous'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='expenses', null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    recorded_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(AbstractUser):
    ROLES = [
        ('TENANT_ADMIN', 'Tenant Admin'),
        ('BRANCH_MANAGER', 'Branch Manager'),
        ('CASHIER', 'Cashier'),
    ]
    role = models.CharField(max_length=20, choices=ROLES)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
