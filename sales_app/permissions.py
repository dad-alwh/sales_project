from rest_framework import permissions
from .models import Permission, Role

def get_all_child_roles(role):
    
    if not role:
        return []
    children = Role.objects.filter(parent_role=role)
    result = list(children)
    for child in children:
        result.extend(get_all_child_roles(child))
    return result

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
            model_name__iexact=model_name, 
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
            child_roles = get_all_child_roles(user.role)
            
            
            if creator_role in child_roles:
                return True
        
        if isinstance(obj, type(user)):
             if obj == user: return True
             if obj.role in get_all_child_roles(user.role):
                 return True

        return False