import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.models import PartnerGroup
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

User = get_user_model()


@pytest.fixture
def notification_security_context():
    group = PartnerGroup.objects.create(name="Notifications Groupe", slug="notif-groupe")
    user_a = User.objects.create_user(
        username="notif-user-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group,
    )
    user_b = User.objects.create_user(
        username="notif-user-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    notification_a = create_notification(
        recipient=user_a,
        partner_group=group,
        notification_type=Notification.Type.PAYMENT_CONFIRMED,
        title="Paiement A",
        message="Notification A",
        metadata={"safe": "visible"},
    )
    notification_b = create_notification(
        recipient=user_b,
        partner_group=group,
        notification_type=Notification.Type.PAYMENT_CONFIRMED,
        title="Paiement B",
        message="Notification B",
    )
    return {
        "group": group,
        "user_a": user_a,
        "user_b": user_b,
        "notification_a": notification_a,
        "notification_b": notification_b,
    }


@pytest.mark.django_db
def test_user_can_only_list_own_notifications(notification_security_context):
    client = APIClient()
    client.force_authenticate(notification_security_context["user_a"])

    response = client.get("/api/v1/notifications/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [
        notification_security_context["notification_a"].id
    ]


@pytest.mark.django_db
def test_user_cannot_retrieve_other_users_notification(notification_security_context):
    client = APIClient()
    client.force_authenticate(notification_security_context["user_a"])

    response = client.get(
        f"/api/v1/notifications/{notification_security_context['notification_b'].id}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_cannot_mark_other_users_notification_read(notification_security_context):
    client = APIClient()
    client.force_authenticate(notification_security_context["user_a"])

    response = client.post(
        f"/api/v1/notifications/{notification_security_context['notification_b'].id}/mark-read/",
        {},
        format="json",
    )

    notification_security_context["notification_b"].refresh_from_db()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert notification_security_context["notification_b"].read_at is None


@pytest.mark.django_db
def test_mark_read_marks_own_notification(notification_security_context):
    client = APIClient()
    client.force_authenticate(notification_security_context["user_a"])

    response = client.post(
        f"/api/v1/notifications/{notification_security_context['notification_a'].id}/mark-read/",
        {},
        format="json",
    )

    notification_security_context["notification_a"].refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert notification_security_context["notification_a"].read_at is not None
    assert response.data["is_read"] is True


@pytest.mark.django_db
def test_mark_all_read_only_marks_own_notifications(notification_security_context):
    create_notification(
        recipient=notification_security_context["user_a"],
        partner_group=notification_security_context["group"],
        notification_type=Notification.Type.CONTRACT_ISSUED,
        title="Contrat A",
    )
    client = APIClient()
    client.force_authenticate(notification_security_context["user_a"])

    response = client.post("/api/v1/notifications/mark-all-read/", {}, format="json")

    notification_security_context["notification_a"].refresh_from_db()
    notification_security_context["notification_b"].refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert response.data["marked_read"] == 2
    assert notification_security_context["notification_a"].read_at is not None
    assert notification_security_context["notification_b"].read_at is None


@pytest.mark.django_db
def test_notification_metadata_is_sanitized(notification_security_context):
    notification = create_notification(
        recipient=notification_security_context["user_a"],
        partner_group=notification_security_context["group"],
        notification_type=Notification.Type.PAYMENT_CONFIRMED,
        title="Sanitized",
        metadata={
            "password": "raw-password",
            "token": "raw-token",
            "safe": "visible",
        },
    )

    notification.refresh_from_db()
    assert notification.metadata["password"] == "***REDACTED***"
    assert notification.metadata["token"] == "***REDACTED***"
    assert notification.metadata["safe"] == "visible"
