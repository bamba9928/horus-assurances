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
    }


def test_openapi_schema_is_public_and_documents_api_paths():
    client = APIClient()

    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["info"]["title"] == "Horus Assurances API"
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
