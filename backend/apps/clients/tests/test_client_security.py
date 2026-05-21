import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup

User = get_user_model()


@pytest.fixture
def client_context():
    group_a = PartnerGroup.objects.create(name="Groupe Clients A", slug="clients-a")
    group_b = PartnerGroup.objects.create(name="Groupe Clients B", slug="clients-b")
    general_admin = User.objects.create_user(
        username="general-client",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="admin-client-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="apporteur-client-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="apporteur-client-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="apporteur-client-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )
    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Awa",
        last_name="Ndiaye",
        phone="770000001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Moussa",
        last_name="Diop",
        phone="770000002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Fatou",
        last_name="Fall",
        phone="770000003",
    )
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "contributor_a2": contributor_a2,
        "contributor_b": contributor_b,
        "client_a": client_a,
        "client_a2": client_a2,
        "client_b": client_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_clients(client_context):
    client = APIClient()
    client.force_authenticate(client_context["general_admin"])

    response = client.get("/api/v1/clients/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["phone"] for item in response.data} == {
        "770000001",
        "770000002",
        "770000003",
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_clients_from_own_group(client_context):
    client = APIClient()
    client.force_authenticate(client_context["group_admin_a"])

    response = client.get("/api/v1/clients/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["phone"] for item in response.data} == {"770000001", "770000002"}


@pytest.mark.django_db
def test_contributor_can_only_list_own_clients(client_context):
    client = APIClient()
    client.force_authenticate(client_context["contributor_a"])

    response = client.get("/api/v1/clients/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["phone"] for item in response.data] == ["770000001"]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_client_from_another_group(client_context):
    client = APIClient()
    client.force_authenticate(client_context["group_admin_a"])

    response = client.get(f"/api/v1/clients/{client_context['client_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_create_client_for_another_group(client_context):
    client = APIClient()
    client.force_authenticate(client_context["contributor_a"])

    response = client.post(
        "/api/v1/clients/",
        {
            "partner_group": client_context["group_b"].id,
            "contributor": client_context["contributor_a"].id,
            "first_name": "Test",
            "last_name": "Cross",
            "phone": "770000010",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_group_admin_cannot_create_client_for_another_group(client_context):
    client = APIClient()
    client.force_authenticate(client_context["group_admin_a"])

    response = client.post(
        "/api/v1/clients/",
        {
            "partner_group": client_context["group_b"].id,
            "contributor": client_context["contributor_b"].id,
            "first_name": "Test",
            "last_name": "Cross",
            "phone": "770000011",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_contributor_create_client_is_forced_to_self_and_own_group(client_context):
    client = APIClient()
    client.force_authenticate(client_context["contributor_a"])

    response = client.post(
        "/api/v1/clients/",
        {
            "first_name": "New",
            "last_name": "Client",
            "phone": "770000012",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Client.objects.get(phone="770000012")
    assert created.partner_group == client_context["group_a"]
    assert created.contributor == client_context["contributor_a"]
