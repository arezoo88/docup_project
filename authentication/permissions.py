from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:  # agar method haye get bashe va taghiri dar
            # database ijad nakonand mese method update ,unvaght ejaze dastresi dare
            return True

        if request.user.is_authenticated and request.user.is_staff:  # if uswer loged in and is admin can access to all method
            return True

        # Instance must have an attribute named `owner`.
        return obj.user == request.user

