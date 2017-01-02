from rest_framework.permissions import IsAdminUser, SAFE_METHODS


#Allows admin users the ability to do anything, everybody else just gets GET/HEAD/OPTIONS
class IsAdminOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super(IsAdminOrReadOnly, self).has_permission(request, view)
        return is_admin or request.method in SAFE_METHODS
