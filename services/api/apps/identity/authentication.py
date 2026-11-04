from datetime import datetime, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.integrations.firebase_admin.app import (
    FirebaseAdminAppFactory,
    FirebaseConfigurationError,
)
from .services import IdentityAccessDenied, IdentityService, VerifiedIdentity
from .models import SecurityEvent
from .security import authentication_dedupe_key, record_security_event


class FirebaseIdentityAuthentication(BaseAuthentication):
    """Verify Firebase ID tokens, then resolve the internal Nexora UUID."""

    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid bearer authorization header.")

        try:
            token = parts[1].decode("ascii")
            app = FirebaseAdminAppFactory.get_app()
            claims = firebase_auth.verify_id_token(token, app=app, check_revoked=True)
        except (
            UnicodeDecodeError,
            ValueError,
            FirebaseConfigurationError,
            firebase_admin.exceptions.FirebaseError,
        ):
            raise AuthenticationFailed("The supplied identity token is invalid.") from None

        subject = claims.get("uid") or claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationFailed("The identity token has no valid subject.")

        auth_time = claims.get("auth_time")
        try:
            authenticated_at = (
                datetime.fromtimestamp(auth_time, tz=timezone.utc)
                if isinstance(auth_time, (int, float))
                else None
            )
        except (OverflowError, OSError, ValueError):
            raise AuthenticationFailed("The identity token has an invalid authentication time.") from None

        try:
            user = IdentityService.resolve_verified_identity(
                VerifiedIdentity(
                    provider="firebase",
                    subject=subject,
                    authenticated_at=authenticated_at,
                )
            )
        except IdentityAccessDenied:
            raise AuthenticationFailed("This Nexora account is not active.") from None

        if authenticated_at is not None:
            dedupe_key = authentication_dedupe_key(user.pk, "firebase", authenticated_at)
            record_security_event(
                user=user,
                event_type=SecurityEvent.EventType.AUTHENTICATED,
                request=request,
                provider="firebase",
                dedupe_key=dedupe_key,
            )

        return user, None

    def authenticate_header(self, request):
        return "Bearer"
