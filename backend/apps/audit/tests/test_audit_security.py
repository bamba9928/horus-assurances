import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.groups.models import PartnerGroup

User = get_user_model()


@pytest.fixture
def audit_security_context():
    group_a = PartnerGroup.objects.create(name="Audit Groupe A", slug="audit-a")
    group_b = PartnerGroup.objects.create(name="Audit Groupe B", slug="audit-b")
    general_admin = User.objects.create_user(
        username="audit-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="audit-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="audit-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    log_a = record_audit_event(
        action=AuditLog.Action.PAYMENT_CONFIRMED,
        partner_group=group_a,
        actor=group_admin_a,
        metadata={"payment": "a"},
    )
    log_b = record_audit_event(
        action=AuditLog.Action.PAYMENT_CONFIRMED,
        partner_group=group_b,
        actor=general_admin,
        metadata={"payment": "b"},
    )
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "log_a": log_a,
        "log_b": log_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_audit_logs(audit_security_context):
    client = APIClient()
    client.force_authenticate(audit_security_context["general_admin"])

    response = client.get("/api/v1/audit-logs/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        audit_security_context["log_a"].id,
        audit_security_context["log_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_own_group_audit_logs(audit_security_context):
    client = APIClient()
    client.force_authenticate(audit_security_context["group_admin_a"])

    response = client.get("/api/v1/audit-logs/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [audit_security_context["log_a"].id]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_other_group_audit_log(audit_security_context):
    client = APIClient()
    client.force_authenticate(audit_security_context["group_admin_a"])

    response = client.get(f"/api/v1/audit-logs/{audit_security_context['log_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_read_audit_logs(audit_security_context):
    client = APIClient()
    client.force_authenticate(audit_security_context["contributor_a"])

    response = client.get("/api/v1/audit-logs/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_audit_metadata_is_sanitized(audit_security_context):
    log = record_audit_event(
        action=AuditLog.Action.PAYMENT_CONFIRMED,
        partner_group=audit_security_context["group_a"],
        actor=audit_security_context["group_admin_a"],
        metadata={
            "password": "raw-password",
            "token": "raw-token",
            "safe": "visible",
        },
    )

    log.refresh_from_db()
    assert log.metadata["password"] == "***REDACTED***"
    assert log.metadata["token"] == "***REDACTED***"
    assert log.metadata["safe"] == "visible"
