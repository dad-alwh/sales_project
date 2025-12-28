from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Role, Permission, Customer, Product, Invoice, InvoiceProduct
)

class CustomUserAdmin(UserAdmin):
    model = User
    
    list_display = ('email', 'username', 'name', 'role', 'status', 'is_staff')
    search_fields = ('email', 'username', 'name')
    fieldsets = UserAdmin.fieldsets + (

        ('Custom Fields', {'fields': ('name', 'role', 'status', 'created_by', 'updated_by')}),
    )

class InvoiceProductInline(admin.TabularInline):
    model = InvoiceProduct
    extra = 1

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent_role', 'status')
    search_fields = ('name',)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'model_name', 'create', 'read', 'update', 'delete')
    list_filter = ('role', 'model_name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile')
    search_fields = ('name', 'email', 'mobile')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity')
    search_fields = ('name',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'invoice_date', 'total_amount', 'status')
    list_filter = ('status', 'invoice_date')
    inlines = [InvoiceProductInline] 

admin.site.register(User, CustomUserAdmin)