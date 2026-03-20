from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permiso personalizado que permite solo al propietario acceder a sus datos.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, "cliente"):
            return obj.cliente == request.user

        return obj == request.user
