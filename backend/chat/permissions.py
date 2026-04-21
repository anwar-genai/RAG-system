from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users whose UserProfile.role == 'admin'."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role == 'admin'
        )
