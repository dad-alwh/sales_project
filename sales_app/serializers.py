from rest_framework import serializers
from .models import User, Role, Permission, Customer, Product, Invoice, InvoiceProduct

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'model_name', 'create', 'read', 'update', 'delete']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    class Meta:
        model = Role
        fields = ['id', 'name', 'parent_role', 'status', 'permissions']
        read_only_fields = ['parent_role'] 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'status', 'role']
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
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

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class InvoiceProductSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    class Meta:
        model = InvoiceProduct
        fields = ['id', 'product', 'product_name', 'quantity', 'amount']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceProductSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.name')

    class Meta:
        model = Invoice
        fields = [
            'id', 'customer', 'customer_name', 'invoice_date', 
            'total_amount', 'status', 'items', 'created_by_name'
        ]
        read_only_fields = ['total_amount', 'status', 'invoice_date']