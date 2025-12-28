from rest_framework import permissions
from .models import Permission

class DynamicHierarchicalPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role and request.user.role.name.lower() == 'admin':
            return True
        try:
            model_name = view.queryset.model.__name__
        except AttributeError:
             return False

        action = request.method
        
        perm_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        perm_type = perm_map.get(action)
        if not perm_type:
            return False

        has_perm = Permission.objects.filter(
            role=request.user.role,
            model_name=model_name,
            **{perm_type: True}
        ).exists()

        return has_perm

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.role and user.role.name.lower() == 'admin':
            return True

    
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True

    
        if hasattr(obj, 'created_by') and obj.created_by:
             creator_role = obj.created_by.role
             if creator_role and creator_role.parent_role == user.role:
                 return True

        if isinstance(obj, type(user)):
             if obj == user: return True
             if obj.role and obj.role.parent_role == user.role:
                 return True

        return False