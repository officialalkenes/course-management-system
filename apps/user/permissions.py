from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to access it.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the owner of the object or an admin.
        """
        # Admin users can access any object
        if request.user.user_type == "ADMIN" or request.user.is_staff:
            return True

        # Check if the object has an owner field and if the current user is the owner
        if hasattr(obj, "id") and request.user.id == obj.id:
            return True

        return False


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and an admin.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.user_type == "ADMIN" or request.user.is_staff)
        )
