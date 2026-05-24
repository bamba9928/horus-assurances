from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def create_notification(
    *,
    recipient,
    notification_type,
    title,
    message="",
    partner_group=None,
    target=None,
    metadata=None,
):
    if recipient is None or not recipient.is_active:
        return None
    return Notification.objects.create(
        partner_group=partner_group,
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        target_type=_target_type(target),
        target_id=_target_id(target),
        metadata=metadata or {},
    )


def create_client_notification(
    *,
    client,
    notification_type,
    title,
    message="",
    partner_group=None,
    target=None,
    metadata=None,
):
    if client is None or not client.is_active:
        return None
    notification = Notification(
        partner_group=partner_group or client.partner_group,
        client=client,
        notification_type=notification_type,
        title=title,
        message=message,
        target_type=_target_type(target),
        target_id=_target_id(target),
        metadata=metadata or {},
    )
    notification.full_clean()
    notification.save()
    return notification


def create_notifications_for_group(
    *,
    partner_group,
    contributor=None,
    include_contributor=True,
    include_group_admins=True,
    notification_type,
    title,
    message="",
    target=None,
    metadata=None,
):
    recipients = []
    if include_contributor and contributor is not None:
        recipients.append(contributor)
    if include_group_admins:
        recipients.extend(
            User.objects.filter(
                role=User.Role.GROUP_ADMIN,
                partner_group=partner_group,
                is_active=True,
            )
        )

    notifications = []
    seen_recipient_ids = set()
    for recipient in recipients:
        if recipient.id in seen_recipient_ids:
            continue
        seen_recipient_ids.add(recipient.id)
        notification = create_notification(
            recipient=recipient,
            partner_group=partner_group,
            notification_type=notification_type,
            title=title,
            message=message,
            target=target,
            metadata=metadata,
        )
        if notification:
            notifications.append(notification)
    return notifications


def _target_type(target):
    if target is None:
        return ""
    return target._meta.label


def _target_id(target):
    if target is None or target.pk is None:
        return ""
    return str(target.pk)
