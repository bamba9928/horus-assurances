import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.models import PartnerGroup

User = get_user_model()


@pytest.fixture
def groups_context():
    group_a = PartnerGroup.objects.create(name="Courtier A", slug="courtier-a")
    group_b = PartnerGroup.objects.create(name="Courtier B", slug="courtier-b")
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
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_own_group(groups_context):
    client = APIClient()
    client.force_authenticate(groups_context["group_admin_a"])

    response = client.get("/api/v1/groups/")

    assert response.status_code == status.HTTP_200_OK
    assert [group["slug"] for group in response.data] == ["courtier-a"]


@pytest.mark.django_db
def test_group_admin_cannot_create_group(groups_context):
    client = APIClient()
    client.force_authenticate(groups_context["group_admin_a"])

    response = client.post(
        "/api/v1/groups/",
        {"name": "Courtier C", "slug": "courtier-c"},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_general_admin_can_create_group(groups_context):
    client = APIClient()
    client.force_authenticate(groups_context["general_admin"])

    response = client.post(
        "/api/v1/groups/",
        {"name": "Courtier C", "slug": "courtier-c"},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert PartnerGroup.objects.filter(slug="courtier-c").exists()


@pytest.mark.django_db
def test_contributor_cannot_retrieve_another_group(groups_context):
    client = APIClient()
    client.force_authenticate(groups_context["contributor_a"])

    response = client.get(f"/api/v1/groups/{groups_context['group_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
