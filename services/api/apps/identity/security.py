import hashlib

from .models import SecurityEvent


def record_security_event(*, user, event_type, request, provider="", dedupe_key=None):
    """Persist a minimal security audit record; never store tokens or request bodies."""
    meta = request.META
    source_ip = meta.get("REMOTE_ADDR") or None
    if source_ip and len(source_ip) > 45:
        source_ip = None

    return SecurityEvent.objects.get_or_create(
        dedupe_key=dedupe_key,
        defaults={
            "user": user,
            "event_type": event_type,
            "provider": provider[:32],
            "source_ip": source_ip,
            "user_agent": meta.get("HTTP_USER_AGENT", "")[:512],
            "request_id": meta.get("HTTP_X_REQUEST_ID", "")[:128],
        },
    )[0]


def authentication_dedupe_key(user_id, provider, authenticated_at):
    raw = f"{user_id}:{provider}:{authenticated_at.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def auth_context_dedupe_key(session_id):
    raw = f"auth-context-changed:{session_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
