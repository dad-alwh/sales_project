from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import User, Role, Customer, Product, Invoice, InvoiceProduct
from .serializers import *
from .validators import * 
from .permissions import DynamicHierarchicalPermission
from django.db import transaction
from django.db.models import Q

class BaseSalesViewSet(viewsets.ModelViewSet):
  
    permission_classes = [DynamicHierarchicalPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_authenticated:
            return queryset.none()
        if user.role and user.role.name.lower() == 'admin':
            return queryset
        child_roles = Role.objects.filter(parent_role=user.role)
        child_users = User.objects.filter(role__in=child_roles)
        return queryset.filter(
            Q(created_by=user) | Q(created_by__in=child_users)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
        validator = UserValidator(request.data, instance_id=instance.id)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

class RoleViewSet(BaseSalesViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def perform_create(self, serializer):
        user = self.request.user
        parent = None
        
        if user.role.name.lower() == 'admin':
            parent = user.role 
        else:
            parent = user.role
            
        serializer.save(created_by=user, parent_role=parent)

class ProductViewSet(BaseSalesViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        validator = ProductValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class InvoiceViewSet(BaseSalesViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def create(self, request, *args, **kwargs):
       
        validator = InvoiceValidator(request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            customer_id = request.data.get('customer_id')
            invoice = Invoice.objects.create(
                customer_id=customer_id,
                created_by=request.user,
                status='pending' 
            )

            total_amount = 0
            items_data = request.data.get('items')
            
            for item in items_data:
                product = Product.objects.get(id=item['product_id'])
                qty = int(item['quantity'])
                amount = product.price * qty
                
                InvoiceProduct.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=qty,
                    amount=amount,
                    created_by=request.user
                )
                
            
                product.quantity -= qty
                product.save()
                
                total_amount += amount

            invoice.total_amount = total_amount
            invoice.save()

            serializer = self.get_serializer(invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
    
        user = request.user
        allowed_roles = ['admin', 'sales manager']
        
        if user.role and user.role.name.lower() not in allowed_roles:
             if 'status' in request.data:
                 return Response({"error": "Only Managers can update invoice status"}, status=403)
        
        return super().update(request, *args, **kwargs)