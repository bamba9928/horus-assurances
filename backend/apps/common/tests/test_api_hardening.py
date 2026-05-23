import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

import config.settings.base as base_settings
from apps.clients.models import Client
from apps.clients.views import ClientViewSet
from apps.common.pagination import StandardResultsSetPagination
from apps.groups.models import PartnerGroup

User = get_user_model()


@pytest.fixture
def api_hardening_context():
    group = PartnerGroup.objects.create(name="Groupe API", slug="groupe-api")
    general_admin = User.objects.create_user(
        username="phase11-admin",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    contributor = User.objects.create_user(
        username="phase11-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )

    for index in range(3):
        Client.objects.create(
            partner_group=group,
            contributor=contributor,
            created_by=contributor,
            first_name=f"Client {index}",
            last_name="API",
            phone=f"77110000{index}",
        )

    return {
        "general_admin": general_admin,
        "contributor": contributor,
    }


def test_openapi_schema_is_public_and_documents_api_paths():
    client = APIClient()

    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["info"]["title"] == "Horus Assurances API"
    assert "/api/clients/" in response.data["paths"]
    assert "/api/contributors/" in response.data["paths"]
    assert "/api/dashboard/" in response.data["paths"]
    assert "/api/auth/me/" in response.data["paths"]
    assert "/api/v1/clients/" in response.data["paths"]
    assert "/api/v1/contracts/{id}/issue/" in response.data["paths"]


def test_swagger_and_redoc_pages_are_available():
    client = APIClient()

    swagger_response = client.get("/api/docs/")
    redoc_response = client.get("/api/redoc/")

    assert swagger_response.status_code == status.HTTP_200_OK
    assert redoc_response.status_code == status.HTTP_200_OK


def test_cors_allows_local_nextjs_origin():
    client = APIClient()

    response = client.options(
        "/api/v1/auth/token/",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.django_db
def test_auth_me_is_available_on_initial_and_versioned_api_paths(api_hardening_context):
    client = APIClient()
    client.force_authenticate(api_hardening_context["contributor"])

    initial_response = client.get("/api/auth/me/")
    versioned_response = client.get("/api/v1/auth/me/")

    assert initial_response.status_code == status.HTTP_200_OK
    assert versioned_response.status_code == status.HTTP_200_OK
    assert initial_response.data["username"] == "phase11-apporteur"
    assert versioned_response.data["username"] == "phase11-apporteur"


@pytest.mark.django_db
def test_initial_api_paths_keep_role_scoping(api_hardening_context):
    client = APIClient()
    client.force_authenticate(api_hardening_context["general_admin"])

    users_response = client.get("/api/users/")
    contributors_response = client.get("/api/contributors/")

    assert users_response.status_code == status.HTTP_200_OK
    assert contributors_response.status_code == status.HTTP_200_OK
    assert {user["username"] for user in users_response.data} == {
        "phase11-admin",
        "phase11-apporteur",
    }
    assert [user["username"] for user in contributors_response.data] == [
        "phase11-apporteur"
    ]


@pytest.mark.django_db
def test_dashboard_counts_are_scoped_to_the_group():
    group_a = PartnerGroup.objects.create(name="Dashboard A", slug="dashboard-a")
    group_b = PartnerGroup.objects.create(name="Dashboard B", slug="dashboard-b")
    group_admin_a = User.objects.create_user(
        username="dashboard-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="dashboard-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="dashboard-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )
    Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Scoped",
        last_name="A",
        phone="779900001",
    )
    Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Scoped",
        last_name="B",
        phone="779900002",
    )
    client = APIClient()
    client.force_authenticate(group_admin_a)

    response = client.get("/api/dashboard/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["scope"] == "group"
    assert response.data["counts"]["groups"] == 1
    assert response.data["counts"]["users"] == 2
    assert response.data["counts"]["contributors"] == 1
    assert response.data["counts"]["clients"] == 1


@pytest.mark.django_db
def test_standard_pagination_can_be_enabled_for_api_lists(
    api_hardening_context,
    monkeypatch,
):
    client = APIClient()
    client.force_authenticate(api_hardening_context["general_admin"])
    monkeypatch.setattr(ClientViewSet, "pagination_class", StandardResultsSetPagination)

    rest_framework_settings = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
        "PAGE_SIZE": 2,
    }

    with override_settings(REST_FRAMEWORK=rest_framework_settings):
        response = client.get("/api/v1/clients/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 3
    assert len(response.data["results"]) == 2
    assert response.data["next"] is not None


def test_base_settings_define_throttle_limits():
    throttle_classes = base_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
    throttle_rates = base_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    assert "rest_framework.throttling.AnonRateThrottle" in throttle_classes
    assert "rest_framework.throttling.UserRateThrottle" in throttle_classes
    assert throttle_rates["anon"] == "100/hour"
    assert throttle_rates["user"] == "1000/hour"
