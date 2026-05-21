import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def vehicle_context():
    group_a = PartnerGroup.objects.create(name="Groupe Vehicles A", slug="vehicles-a")
    group_b = PartnerGroup.objects.create(name="Groupe Vehicles B", slug="vehicles-b")
    general_admin = User.objects.create_user(
        username="general-vehicle",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="admin-vehicle-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="apporteur-vehicle-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="apporteur-vehicle-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="apporteur-vehicle-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )
    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Client",
        last_name="A",
        phone="780000001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Client",
        last_name="A2",
        phone="780000002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Client",
        last_name="B",
        phone="780000003",
    )
    vehicle_a = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        registration_number="DK-001-AA",
        brand="Toyota",
        model="Yaris",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    vehicle_a2 = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        registration_number="DK-002-AA",
        brand="Hyundai",
        model="i10",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    vehicle_b = Vehicle.objects.create(
        partner_group=group_b,
        client=client_b,
        contributor=contributor_b,
        created_by=contributor_b,
        registration_number="DK-003-BB",
        brand="Kia",
        model="Rio",
        genre="VP",
        energy=Vehicle.Energy.DIESEL,
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
        "vehicle_a": vehicle_a,
        "vehicle_a2": vehicle_a2,
        "vehicle_b": vehicle_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_vehicles(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["general_admin"])

    response = client.get("/api/v1/vehicles/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["registration_number"] for item in response.data} == {
        "DK-001-AA",
        "DK-002-AA",
        "DK-003-BB",
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_vehicles_from_own_group(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["group_admin_a"])

    response = client.get("/api/v1/vehicles/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["registration_number"] for item in response.data} == {
        "DK-001-AA",
        "DK-002-AA",
    }


@pytest.mark.django_db
def test_contributor_can_only_list_own_vehicles(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["contributor_a"])

    response = client.get("/api/v1/vehicles/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["registration_number"] for item in response.data] == ["DK-001-AA"]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_vehicle_from_another_group(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["group_admin_a"])

    response = client.get(f"/api/v1/vehicles/{vehicle_context['vehicle_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_create_vehicle_for_another_group(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["contributor_a"])

    response = client.post(
        "/api/v1/vehicles/",
        {
            "partner_group": vehicle_context["group_b"].id,
            "client": vehicle_context["client_b"].id,
            "registration_number": "DK-010-XX",
            "brand": "Nissan",
            "model": "Micra",
            "genre": "VP",
            "energy": Vehicle.Energy.GASOLINE,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_vehicle_cannot_use_client_from_another_group(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["group_admin_a"])

    response = client.post(
        "/api/v1/vehicles/",
        {
            "partner_group": vehicle_context["group_a"].id,
            "client": vehicle_context["client_b"].id,
            "registration_number": "DK-011-XX",
            "brand": "Nissan",
            "model": "Micra",
            "genre": "VP",
            "energy": Vehicle.Energy.GASOLINE,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_contributor_create_vehicle_is_forced_to_self_and_own_group(vehicle_context):
    client = APIClient()
    client.force_authenticate(vehicle_context["contributor_a"])

    response = client.post(
        "/api/v1/vehicles/",
        {
            "client": vehicle_context["client_a"].id,
            "registration_number": "DK-012-XX",
            "brand": "Suzuki",
            "model": "Swift",
            "genre": "VP",
            "energy": Vehicle.Energy.GASOLINE,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Vehicle.objects.get(registration_number="DK-012-XX")
    assert created.partner_group == vehicle_context["group_a"]
    assert created.contributor == vehicle_context["contributor_a"]
