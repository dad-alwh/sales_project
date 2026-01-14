from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# ---------------------------------------------------------
# 1. Abstract Base Model 
# ---------------------------------------------------------
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


# ---------------------------------------------------------
# 2. Roles Model (Master)
# ---------------------------------------------------------
class Role(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    parent_role = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='child_roles'
    )
    status = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)


# ---------------------------------------------------------
# 3. Users Model (Master)
# ---------------------------------------------------------
class User(AbstractUser, BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    status = models.BooleanField(default=True)
    
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='users'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    def __str__(self):
        return f"{self.email} ({self.role})"


# ---------------------------------------------------------
# 4. Permissions Model (Detail for Roles)
# ---------------------------------------------------------
class Permission(BaseModel):
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE, 
        related_name='permissions',
        null=True, blank=True
    )
    model_name = models.CharField(max_length=100, null=True, blank=True)
    
    create = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        # Always lower case model name to avoid mismatches
        if self.model_name:
            self.model_name = self.model_name.lower()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.role} -> {self.model_name}"


# ---------------------------------------------------------
# 5. Customers Model (Master)
# ---------------------------------------------------------
class Customer(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return str(self.name)


# ---------------------------------------------------------
# 6. Products Model (Master)
# ---------------------------------------------------------
class Product(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


# ---------------------------------------------------------
# 7. Invoices Model (Master)
# ---------------------------------------------------------
class Invoice(BaseModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
    )
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.PROTECT, 
        null=True, blank=True
    )
    invoice_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        null=True, blank=True
    )

    def __str__(self):
        return f"Invoice #{self.id} - {self.status}"


# ---------------------------------------------------------
# 8. InvoiceProducts Model (Detail)
# ---------------------------------------------------------
class InvoiceProduct(BaseModel):
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='items',
        null=True, blank=True
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    quantity = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product} x {self.quantity}"
