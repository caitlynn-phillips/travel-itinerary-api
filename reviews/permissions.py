from rest_framework import permissions


class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    """
    Read access permitted for any request; write access only to review owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and obj.user == request.user)
