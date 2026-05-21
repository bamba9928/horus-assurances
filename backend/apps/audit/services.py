from .models import AuditLog


def record_audit_event(
    *,
    action,
    partner_group=None,
    actor=None,
    target=None,
    metadata=None,
):
    return AuditLog.objects.create(
        partner_group=partner_group,
        actor=actor if getattr(actor, "is_authenticated", True) else None,
        action=action,
        target_type=_target_type(target),
        target_id=_target_id(target),
        metadata=metadata or {},
    )


def _target_type(target):
    if target is None:
        return ""
    return target._meta.label


def _target_id(target):
    if target is None or target.pk is None:
        return ""
    return str(target.pk)
