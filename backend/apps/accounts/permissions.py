from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_general_admin(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "is_general_admin", False))


def is_group_admin(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "is_group_admin", False))


def is_contributor(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "is_contributor", False))


class IsGeneralAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_general_admin(request.user)


class PartnerGroupAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_general_admin(request.user)

    def has_object_permission(self, request, view, obj):
        if is_general_admin(request.user):
            return True
        return request.method in SAFE_METHODS and obj.id == request.user.partner_group_id


class UserAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action == "create":
            return is_general_admin(request.user) or is_group_admin(request.user)
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_general_admin(user):
            return True

        if is_group_admin(user):
            same_group = obj.partner_group_id == user.partner_group_id
            if request.method in SAFE_METHODS:
                return same_group
            return same_group and obj.is_contributor

        if is_contributor(user):
            return request.method in SAFE_METHODS and obj.id == user.id

        return False
