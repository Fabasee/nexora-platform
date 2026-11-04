from rest_framework.permissions import BasePermission


class VerifiedEmailRequired(BasePermission):
    """Require an email_verified claim verified by Firebase Admin."""

    message = "Verify your email address before accessing this resource."
    code = "email_verification_required"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request, "nexora_email_verified", False) is True
        )


class VerifiedMFARequired(BasePermission):
    """Require a Firebase-verified second factor on the current Nexora session."""

    message = "Complete multi-factor authentication before accessing this resource."
    code = "mfa_required"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request, "nexora_mfa_verified", False) is True
        )
