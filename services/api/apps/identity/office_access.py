from rest_framework.permissions import BasePermission


OFFICE_ROLE_PERMISSIONS = {
    "Office Owner": frozenset({"portfolio.view", "audit.view", "security.view", "sessions.manage", "access.manage", "access.view_self"}),
    "Office Security Admin": frozenset({"security.view", "sessions.manage", "access.manage", "access.view_self"}),
    "Office Portfolio Manager": frozenset({"portfolio.view", "audit.view", "access.view_self"}),
    "Office Auditor": frozenset({"audit.view", "security.view", "access.view_self"}),
    "Office Portfolio Viewer": frozenset({"portfolio.view", "access.view_self"}),
}


def get_office_roles(user):
    if not user or not getattr(user, "is_authenticated", False):
        return []
    return sorted(user.groups.filter(name__in=OFFICE_ROLE_PERMISSIONS).values_list("name", flat=True))


def get_office_permissions(user):
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    if user.is_superuser:
        return set().union(*OFFICE_ROLE_PERMISSIONS.values())
    permissions = set()
    for role in get_office_roles(user):
        permissions.update(OFFICE_ROLE_PERMISSIONS[role])
    return permissions


class OfficeAccessPermission(BasePermission):
    message = "Your Nexora Office role does not permit this operation."
    code = "office_role_required"

    def has_permission(self, request, view):
        user = request.user
        if not (
            user and user.is_authenticated and user.is_active and user.is_staff
            and getattr(request, "nexora_email_verified", False) is True
        ):
            return False
        required = getattr(view, "office_permission", None)
        return bool(required and required in get_office_permissions(user))
