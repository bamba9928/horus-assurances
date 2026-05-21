from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def quote_context():
    group_a = PartnerGroup.objects.create(name="Groupe Quotes A", slug="quotes-a")
    group_b = PartnerGroup.objects.create(name="Groupe Quotes B", slug="quotes-b")
    general_admin = User.objects.create_user(
        username="general-quote",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="admin-quote-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="apporteur-quote-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="apporteur-quote-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="apporteur-quote-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )

    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Client",
        last_name="Quote A",
        phone="790000001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Client",
        last_name="Quote A2",
        phone="790000002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Client",
        last_name="Quote B",
        phone="790000003",
    )

    vehicle_a = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        registration_number="DK-Q01-AA",
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
        registration_number="DK-Q02-AA",
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
        registration_number="DK-Q03-BB",
        brand="Kia",
        model="Rio",
        genre="VP",
        energy=Vehicle.Energy.DIESEL,
    )

    quote_a = Quote.objects.create(
        partner_group=group_a,
        client=client_a,
        vehicle=vehicle_a,
        contributor=contributor_a,
        created_by=contributor_a,
        premium_amount=Decimal("10000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("11000.00"),
    )
    quote_a2 = Quote.objects.create(
        partner_group=group_a,
        client=client_a2,
        vehicle=vehicle_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        premium_amount=Decimal("20000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("21000.00"),
    )
    quote_b = Quote.objects.create(
        partner_group=group_b,
        client=client_b,
        vehicle=vehicle_b,
        contributor=contributor_b,
        created_by=contributor_b,
        premium_amount=Decimal("30000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("31000.00"),
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
        "quote_a": quote_a,
        "quote_a2": quote_a2,
        "quote_b": quote_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_quotes(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["general_admin"])

    response = client.get("/api/v1/quotes/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        quote_context["quote_a"].id,
        quote_context["quote_a2"].id,
        quote_context["quote_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_quotes_from_own_group(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["group_admin_a"])

    response = client.get("/api/v1/quotes/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        quote_context["quote_a"].id,
        quote_context["quote_a2"].id,
    }


@pytest.mark.django_db
def test_contributor_can_only_list_own_quotes(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["contributor_a"])

    response = client.get("/api/v1/quotes/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [quote_context["quote_a"].id]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_quote_from_another_group(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["group_admin_a"])

    response = client.get(f"/api/v1/quotes/{quote_context['quote_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_create_quote_for_another_group(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["contributor_a"])

    response = client.post(
        "/api/v1/quotes/",
        {
            "partner_group": quote_context["group_b"].id,
            "client": quote_context["client_b"].id,
            "vehicle": quote_context["vehicle_b"].id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_quote_cannot_use_vehicle_from_another_group(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["group_admin_a"])

    response = client.post(
        "/api/v1/quotes/",
        {
            "partner_group": quote_context["group_a"].id,
            "client": quote_context["client_a"].id,
            "vehicle": quote_context["vehicle_b"].id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_quote_cannot_use_vehicle_from_another_client(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["group_admin_a"])

    response = client.post(
        "/api/v1/quotes/",
        {
            "partner_group": quote_context["group_a"].id,
            "client": quote_context["client_a"].id,
            "vehicle": quote_context["vehicle_a2"].id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_contributor_create_quote_is_forced_to_self_and_own_group(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["contributor_a"])

    response = client.post(
        "/api/v1/quotes/",
        {
            "client": quote_context["client_a"].id,
            "vehicle": quote_context["vehicle_a"].id,
            "effective_date": timezone.localdate().isoformat(),
            "premium_amount": "15000.00",
            "fees_amount": "1500.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Quote.objects.get(id=response.data["id"])
    assert created.partner_group == quote_context["group_a"]
    assert created.contributor == quote_context["contributor_a"]
    assert created.total_amount == Decimal("16500.00")


@pytest.mark.django_db
def test_calculate_sets_quote_amounts_without_external_call(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["contributor_a"])

    response = client.post(
        f"/api/v1/quotes/{quote_context['quote_a'].id}/calculate/",
        {
            "civil_liability_amount": "18688.00",
            "premium_amount": "25000.00",
            "fees_amount": "3000.00",
            "coverage_options": [1, 2, 4],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    quote_context["quote_a"].refresh_from_db()
    assert quote_context["quote_a"].status == Quote.Status.CALCULATED
    assert quote_context["quote_a"].civil_liability_amount == Decimal("18688.00")
    assert quote_context["quote_a"].total_amount == Decimal("28000.00")
    assert quote_context["quote_a"].coverage_options == [1, 2, 4]


@pytest.mark.django_db
def test_contributor_cannot_calculate_quote_from_another_contributor(quote_context):
    client = APIClient()
    client.force_authenticate(quote_context["contributor_a"])

    response = client.post(
        f"/api/v1/quotes/{quote_context['quote_a2'].id}/calculate/",
        {"premium_amount": "25000.00"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
