from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from rest_framework.permissions import IsAdminUser, SAFE_METHODS, IsAuthenticated


# Allows admin users the ability to do anything, everybody else just gets GET/HEAD/OPTIONS
class IsAdminOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super(IsAdminOrReadOnly, self).has_permission(request, view)
        return is_admin or request.method in SAFE_METHODS


class IsMeOrAdmin(IsAdminUser):
    """
    Object-level permission to ensure the requesting user only has access to their own profile.
    """

    def has_object_permission(self, request, view, obj):
        is_admin = super(IsMeOrAdmin, self).has_object_permission(request, view, obj)
        return request.user == obj or is_admin


class IsAuthenticatedOrCreating(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        meth = request.method
        return is_authenticated or request.method == 'POST'
