from django.db import transaction

from .models import PortfolioAuditEvent, ProductPortfolioEntry


AUDITED_FIELDS = (
    "name",
    "entry_type",
    "category",
    "description",
    "parent_id",
    "lifecycle_status",
    "decision_status",
    "priority",
    "delivery_model",
    "activation_product_id",
    "sort_order",
)


def _json_value(value):
    return str(value) if value is not None else None


@transaction.atomic
def save_portfolio_entry(*, entry, source, actor=None):
    """Persist a portfolio entry and its audit event in one database transaction."""
    if source not in PortfolioAuditEvent.Source.values:
        raise ValueError("Unsupported portfolio audit source.")

    current = None
    if entry.pk:
        current = ProductPortfolioEntry.objects.select_for_update().filter(pk=entry.pk).first()

    if current is None:
        entry.full_clean()
        entry.save()
        changes = {
            field: {"before": None, "after": _json_value(getattr(entry, field))}
            for field in AUDITED_FIELDS
        }
        action = PortfolioAuditEvent.Action.CREATED
    else:
        changes = {}
        for field in AUDITED_FIELDS:
            before = getattr(current, field)
            after = getattr(entry, field)
            if before != after:
                changes[field.removesuffix("_id")] = {
                    "before": _json_value(before),
                    "after": _json_value(after),
                }
        if not changes:
            return current, False

        for field in AUDITED_FIELDS:
            setattr(current, field, getattr(entry, field))
        current.full_clean()
        current.save()
        entry = current
        action = PortfolioAuditEvent.Action.UPDATED

    actor_label = ""
    if actor is not None and getattr(actor, "is_authenticated", False):
        actor_label = actor.get_username() or str(actor.pk)

    PortfolioAuditEvent.objects.create(
        entry=entry,
        entry_key=entry.key,
        entry_name=entry.name,
        action=action,
        source=source,
        actor=actor if actor is not None and getattr(actor, "is_authenticated", False) else None,
        actor_label=actor_label,
        changes=changes,
    )
    return entry, True
