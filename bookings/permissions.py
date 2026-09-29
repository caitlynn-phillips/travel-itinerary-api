from rest_framework import permissions


class IsBookingOwner(permissions.BasePermission):
    """
    Permission check: only booking owner can view/modify.
    """

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.user == request.user)
