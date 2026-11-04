from datetime import datetime, timedelta, timezone

import firebase_admin
from django.utils import timezone as django_timezone
from firebase_admin import auth as firebase_auth
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.integrations.firebase_admin.app import (
    FirebaseAdminAppFactory,
    FirebaseConfigurationError,
)
from .models import IdentitySession, SecurityEvent
from .security import authentication_dedupe_key, record_security_event
from .services import IdentityAccessDenied, IdentityService, VerifiedIdentity


class FirebaseIdentityAuthentication(BaseAuthentication):
    """Verify Firebase tokens and enforce a revocable Nexora API session."""

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
            if isinstance(auth_time, bool) or not isinstance(auth_time, (int, float)):
                raise ValueError
            authenticated_at = datetime.fromtimestamp(auth_time, tz=timezone.utc)
        except (OverflowError, OSError, TypeError, ValueError):
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

        provider_account = user.provider_accounts.get(provider="firebase")
        now = django_timezone.now()
        source_ip = request.META.get("REMOTE_ADDR") or None
        if source_ip and len(source_ip) > 45:
            source_ip = None
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]

        session, created = IdentitySession.objects.get_or_create(
            provider_account=provider_account,
            authenticated_at=authenticated_at,
            defaults={
                "last_seen_at": now,
                "source_ip": source_ip,
                "user_agent": user_agent,
            },
        )
        if session.revoked_at is not None:
            raise AuthenticationFailed("This Nexora session has been revoked.")

        # Avoid a database write on every API request while keeping activity fresh.
        if not created and session.last_seen_at < now - timedelta(minutes=5):
            IdentitySession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(
                last_seen_at=now,
                source_ip=source_ip,
                user_agent=user_agent,
            )
        request.nexora_session_id = session.pk

        if created:
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
