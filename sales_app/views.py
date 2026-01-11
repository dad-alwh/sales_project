from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from django.db import transaction
from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
#from .models import*
from .models import User, Role, Customer, Product, Invoice, InvoiceProduct, Permission
from .serializers import (
    UserSerializer, RoleSerializer, CustomerSerializer, 
    ProductSerializer, InvoiceSerializer
)
from .validators import (
    UserValidator, ProductValidator, InvoiceValidator, CustomerValidator
)
from .permissions import DynamicHierarchicalPermission, get_all_child_roles

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        permissions = []
        if user.role:
            perms = Permission.objects.filter(role=user.role)
            for p in perms:
                permissions.append({
                    "model_name": p.model_name,
                    "read": p.read,
                    "create": p.create,
                    "update": p.update,
                    "delete": p.delete
                })

        data['user_data'] = {
            'id': user.id,
            'name': user.name,
            'role_name': user.role.name.lower() if user.role else None,
            'permissions': permissions
        }
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class BaseSalesViewSet(viewsets.ModelViewSet):

    permission_classes = [DynamicHierarchicalPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user or not user.is_authenticated:
            return queryset.none()

      
        if user.is_superuser or (user.role and user.role.name.lower() == 'admin'):
            return queryset

        model_name = self.queryset.model.__name__

    
        if model_name in ['Product', 'Customer'] and self.action in ['list', 'retrieve']:
            return queryset

        
        child_roles = get_all_child_roles(user.role)
        child_role_ids = [r.id for r in child_roles]
        
        return queryset.filter(
            Q(created_by=user) | 
            Q(created_by__role_id__in=child_role_ids)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)




class UserViewSet(BaseSalesViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):

        validator = UserValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        validator = UserValidator(request.data)
        if not validator.is_valid(exclude_id=instance.id):
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

class RoleViewSet(BaseSalesViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, 
            parent_role=self.request.user.role
        )

class CustomerViewSet(BaseSalesViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
    def create(self, request, *args, **kwargs):
        validator = CustomerValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        validator = CustomerValidator(request.data)
        if not validator.is_valid(exclude_id=instance.id):
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

class ProductViewSet(BaseSalesViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        validator = ProductValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        validator = ProductValidator(request.data)
        if not validator.is_valid(exclude_id=instance.id):
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

class InvoiceViewSet(BaseSalesViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def create(self, request, *args, **kwargs):

        validator = InvoiceValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                customer_obj = Customer.objects.get(id=request.data.get('customer_id'))
                
                invoice = Invoice.objects.create(
                    customer=customer_obj,
                    created_by=request.user,
                    status='pending' 
                )

                total_amount = 0
                items_data = request.data.get('items', [])
                
                for item in items_data:
                    product = Product.objects.select_for_update().get(id=item['product_id'])
                    qty = int(item['quantity'])
                    
                    if product.quantity < qty:
                        raise ValueError(f"Insufficient stock for product: {product.name}")

                    line_amount = product.price * qty
                    InvoiceProduct.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=qty,
                        amount=line_amount,
                        created_by=request.user
                    )
                    

                    product.quantity -= qty
                    product.save()
                    total_amount += line_amount

                invoice.total_amount = total_amount
                invoice.save()

                serializer = self.get_serializer(invoice)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):

        user = request.user
        allowed_roles = ['admin', 'sales manager']
        user_role_name = user.role.name.lower() if user.role else ""

        if 'status' in request.data:
            new_status = request.data['status']
            if new_status in ['paid', 'refused']:
                 is_manager = 'sales manager' in user_role_name or 'admin' == user_role_name
                 if not is_manager:
                     return Response(
                        {"error": "Permission Denied: Only Managers can change invoice status to Paid/Refused."}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        return super().update(request, *args, **kwargs)