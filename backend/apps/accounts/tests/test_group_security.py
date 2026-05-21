import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.models import PartnerGroup

User = get_user_model()


@pytest.fixture
def security_context():
    group_a = PartnerGroup.objects.create(name="Groupe A", slug="groupe-a")
    group_b = PartnerGroup.objects.create(name="Groupe B", slug="groupe-b")
    general_admin = User.objects.create_user(
        username="general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    group_admin_b = User.objects.create_user(
        username="admin-b",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_b,
    )
    contributor_b = User.objects.create_user(
        username="apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "group_admin_b": group_admin_b,
        "contributor_b": contributor_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_users_and_groups(security_context):
    client = APIClient()
    client.force_authenticate(security_context["general_admin"])

    groups_response = client.get("/api/v1/groups/")
    users_response = client.get("/api/v1/users/")

    assert groups_response.status_code == status.HTTP_200_OK
    assert users_response.status_code == status.HTTP_200_OK
    assert {group["slug"] for group in groups_response.data} == {"groupe-a", "groupe-b"}
    assert {user["username"] for user in users_response.data} == {
        "general",
        "admin-a",
        "apporteur-a",
        "admin-b",
        "apporteur-b",
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_users_from_own_group(security_context):
    client = APIClient()
    client.force_authenticate(security_context["group_admin_a"])

    response = client.get("/api/v1/users/")

    assert response.status_code == status.HTTP_200_OK
    assert {user["username"] for user in response.data} == {"admin-a", "apporteur-a"}


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_user_from_another_group(security_context):
    client = APIClient()
    client.force_authenticate(security_context["group_admin_a"])

    response = client.get(f"/api/v1/users/{security_context['contributor_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_can_only_list_self(security_context):
    client = APIClient()
    client.force_authenticate(security_context["contributor_a"])

    response = client.get("/api/v1/users/")

    assert response.status_code == status.HTTP_200_OK
    assert [user["username"] for user in response.data] == ["apporteur-a"]


@pytest.mark.django_db
def test_unauthenticated_user_is_rejected():
    client = APIClient()

    response = client.get("/api/v1/users/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_non_general_admin_user_without_group_is_invalid():
    user = User(username="invalid", role=User.Role.CONTRIBUTOR)

    with pytest.raises(ValidationError):
        user.full_clean()
