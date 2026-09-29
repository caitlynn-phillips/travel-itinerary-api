from rest_framework import permissions


class IsTripOwner(permissions.BasePermission):
    """
    Permission check: strictly trip owner.
    """

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.owner == request.user)


class IsTripOwnerOrCollaborator(permissions.BasePermission):
    """
    Allow read access to owner or collaborators, but write access only to owner.
    """

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user or obj.collaborators.filter(id=request.user.id).exists()

        return obj.owner == request.user


class CanEditItinerary(permissions.BasePermission):
    """
    Check if user can edit itinerary based on ownership or collaborator role ('editor' or 'admin').
    """

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Owner can always perform any action
        if obj.owner == request.user:
            return True

        if request.method in permissions.SAFE_METHODS:
            return obj.collaborators.filter(id=request.user.id).exists()

        # For write methods (PUT, PATCH, POST), check collaboration role
        collaboration = obj.collaborations.filter(user=request.user).first()
        return bool(collaboration and collaboration.role in ['editor', 'admin'])
