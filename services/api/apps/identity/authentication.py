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
from .models import IdentityProviderAccount, IdentitySession, SecurityEvent
from .security import (
    auth_context_dedupe_key,
    authentication_dedupe_key,
    mfa_authentication_dedupe_key,
    record_security_event,
)
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

        provider_account = IdentityProviderAccount.objects.get(
            user=user, provider="firebase", provider_subject=subject
        )
        email_verified = claims.get("email_verified") is True
        firebase_claims = claims.get("firebase")
        firebase_claims = firebase_claims if isinstance(firebase_claims, dict) else {}
        second_factor = firebase_claims.get("sign_in_second_factor")
        # Firebase reserves this claim and sets it only when this sign-in
        # completed a configured second factor. Never accept a client flag.
        second_factor = second_factor if second_factor in {"phone", "totp"} else ""
        mfa_verified = bool(second_factor)

        now = django_timezone.now()
        source_ip = request.META.get("REMOTE_ADDR") or None
        if source_ip and len(source_ip) > 45:
            source_ip = None
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]

        previous_session = (
            IdentitySession.objects.filter(provider_account=provider_account)
            .order_by("-authenticated_at")
            .first()
        )
        session, created = IdentitySession.objects.get_or_create(
            provider_account=provider_account,
            authenticated_at=authenticated_at,
            defaults={
                "last_seen_at": now,
                "email_verified": email_verified,
                "mfa_verified": mfa_verified,
                "second_factor_type": second_factor,
                "source_ip": source_ip,
                "user_agent": user_agent,
            },
        )
        if session.revoked_at is not None:
            raise AuthenticationFailed("This Nexora session has been revoked.")

        was_email_verified = session.email_verified
        was_mfa_verified = session.mfa_verified
        updates = {}
        if session.last_seen_at < now - timedelta(minutes=5):
            updates.update(last_seen_at=now, source_ip=source_ip, user_agent=user_agent)
        if session.email_verified != email_verified:
            updates["email_verified"] = email_verified
        if mfa_verified and not session.mfa_verified:
            updates.update(mfa_verified=True, second_factor_type=second_factor)
        if updates:
            IdentitySession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(**updates)
            for field, value in updates.items():
                setattr(session, field, value)
        if not IdentitySession.objects.filter(pk=session.pk, revoked_at__isnull=True).exists():
            raise AuthenticationFailed("This Nexora session has been revoked.")

        request.nexora_session_id = session.pk
        request.nexora_email_verified = email_verified
        request.nexora_mfa_verified = session.mfa_verified
        request.nexora_second_factor_type = session.second_factor_type

        if email_verified and not was_email_verified:
            record_security_event(
                user=user,
                event_type=SecurityEvent.EventType.EMAIL_VERIFICATION_CONFIRMED,
                request=request,
                provider="firebase",
            )

        if session.mfa_verified and not was_mfa_verified:
            record_security_event(
                user=user,
                event_type=SecurityEvent.EventType.MFA_AUTHENTICATED,
                request=request,
                provider="firebase",
                dedupe_key=mfa_authentication_dedupe_key(session.pk),
            )

        if created:
            record_security_event(
                user=user,
                event_type=SecurityEvent.EventType.AUTHENTICATED,
                request=request,
                provider="firebase",
                dedupe_key=authentication_dedupe_key(user.pk, "firebase", authenticated_at),
            )
            if previous_session is not None:
                ip_changed = bool(
                    source_ip and previous_session.source_ip
                    and source_ip != previous_session.source_ip
                )
                agent_changed = bool(
                    user_agent and previous_session.user_agent
                    and user_agent != previous_session.user_agent
                )
                if ip_changed or agent_changed:
                    record_security_event(
                        user=user,
                        event_type=SecurityEvent.EventType.AUTH_CONTEXT_CHANGED,
                        request=request,
                        provider="firebase",
                        dedupe_key=auth_context_dedupe_key(session.pk),
                    )

        return user, None

    def authenticate_header(self, request):
        return "Bearer"
