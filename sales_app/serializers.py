from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role, Permission, Customer, Product, Invoice, InvoiceProduct

User = get_user_model()
AUDIT_FIELDS = ['created_at', 'created_by', 'updated_at', 'updated_by']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'model_name', 'create', 'read', 'update', 'delete', 'role'] + AUDIT_FIELDS
        read_only_fields = AUDIT_FIELDS

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'parent_role', 'status', 'permissions'] + AUDIT_FIELDS
        read_only_fields = ['parent_role'] + AUDIT_FIELDS 

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'username', 'password', 'status', 'role', 'role_name'] + AUDIT_FIELDS
        extra_kwargs = {
            'password': {'write_only': True}, 
            'username': {'required': False, 'allow_blank': True} 
        }
        read_only_fields = ['role_name'] + AUDIT_FIELDS

    def create(self, validated_data):
        if not validated_data.get('username'):
            validated_data['username'] = validated_data.get('email')
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = AUDIT_FIELDS

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = AUDIT_FIELDS

class InvoiceProductSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    class Meta:
        model = InvoiceProduct
        fields = ['id', 'product', 'product_name', 'quantity', 'amount'] + AUDIT_FIELDS
        read_only_fields = AUDIT_FIELDS

class InvoiceSerializer(serializers.ModelSerializer):
    
    items = InvoiceProductSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.name')

    class Meta:
        model = Invoice
        fields = [
            'id', 'customer', 'customer_name', 'invoice_date', 'total_amount', 
            'status', 'items', 'created_by', 'created_by_name'
        ] + AUDIT_FIELDS

        read_only_fields = ['total_amount', 'invoice_date'] + AUDIT_FIELDS