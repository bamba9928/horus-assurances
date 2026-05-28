import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.reference_data.models import (
    EnergyType,
    FormRule,
    GuaranteeReference,
    VehicleCategory,
    VehicleGenre,
    VehicleSubCategory,
)

User = get_user_model()


@pytest.fixture
def reference_user():
    return User.objects.create_user(
        username="reference-admin",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )


@pytest.fixture
def authenticated_client(reference_user):
    client = APIClient()
    client.force_authenticate(reference_user)
    return client


@pytest.mark.django_db
def test_reference_data_requires_authentication():
    response = APIClient().get("/api/v1/reference-data/products/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_products_endpoint_returns_seeded_ass_products(authenticated_client):
    response = authenticated_client.get("/api/v1/reference-data/products/")

    assert response.status_code == status.HTTP_200_OK
    product_codes = {item["code"] for item in response.data}
    assert {"AUTO", "MOTO", "FLEET", "TRAILER", "SCHOOL_BUS", "GARAGE"}.issubset(
        product_codes
    )
    auto_product = next(item for item in response.data if item["code"] == "AUTO")
    garage_product = next(item for item in response.data if item["code"] == "GARAGE")
    assert auto_product["source"] == "SANDBOX_VALIDATION"
    assert auto_product["is_verified"] is True
    assert garage_product["source"] == "POSTMAN"
    assert garage_product["is_verified"] is False
    assert garage_product["metadata"]["is_exhaustive"] is False


@pytest.mark.django_db
def test_reference_data_is_active_by_default(authenticated_client):
    EnergyType.objects.filter(code="HYBRIDE").update(is_active=False)

    active_response = authenticated_client.get("/api/v1/reference-data/energies/")
    include_inactive_response = authenticated_client.get(
        "/api/v1/reference-data/energies/",
        {"include_inactive": "true"},
    )

    assert active_response.status_code == status.HTTP_200_OK
    assert "HYBRIDE" not in {item["code"] for item in active_response.data}
    assert "HYBRIDE" in {item["code"] for item in include_inactive_response.data}


@pytest.mark.django_db
def test_guarantees_expose_rc_and_cedeao_as_mandatory_readonly(
    authenticated_client,
):
    response = authenticated_client.get("/api/v1/reference-data/guarantees/")

    assert response.status_code == status.HTTP_200_OK
    guarantees = {item["code"]: item for item in response.data}
    for code in ("RC", "CEDEAO"):
        assert guarantees[code]["is_mandatory"] is True
        assert guarantees[code]["is_default_selected"] is True
        assert guarantees[code]["is_readonly"] is True
        assert guarantees[code]["source"] == "NATIVE_ACCOUNT"
        assert guarantees[code]["is_verified"] is False


@pytest.mark.django_db
def test_vehicle_genres_expose_trailer_visibility_only_for_tpc(
    authenticated_client,
):
    response = authenticated_client.get(
        "/api/v1/reference-data/vehicle-genres/",
        {"requires_trailer_section": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {item["code"] for item in response.data} == {
        "TPC_MOINS_3T500",
        "TPC_PLUS_3T500",
    }
    assert {item["source"] for item in response.data} == {"NATIVE_ACCOUNT"}
    assert {item["is_verified"] for item in response.data} == {False}


@pytest.mark.django_db
def test_reference_data_can_be_filtered_by_verification_status(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/reference-data/vehicle-genres/",
        {"is_verified": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {item["code"] for item in response.data} == {"VP", "REMORQUE"}


@pytest.mark.django_db
def test_vehicle_subcategories_can_be_filtered_by_category_code(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/reference-data/vehicle-subcategories/",
        {"category_code": "TRANSPORT_COMMERCIAL"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {item["code"] for item in response.data} == {
        "TPC_MOINS_3T500",
        "TPC_PLUS_3T500",
    }


@pytest.mark.django_db
def test_form_rules_can_be_filtered_by_genre_code(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/reference-data/form-rules/",
        {"genre_code": "TPC_MOINS_3T500"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [item["field_name"] for item in response.data] == ["trailer_section"]
    assert response.data[0]["rule_type"] == FormRule.RuleType.SHOW
    assert response.data[0]["metadata"]["is_exhaustive"] is False


@pytest.mark.django_db
def test_product_scoped_reference_data_accepts_product_code(authenticated_client):
    usage_response = authenticated_client.get(
        "/api/v1/reference-data/usages/",
        {"product": "MOTO"},
    )
    duration_response = authenticated_client.get(
        "/api/v1/reference-data/durations/",
        {"product": "AUTO"},
    )

    assert usage_response.status_code == status.HTTP_200_OK
    assert {"NON_COMMERCIAL", "COMMERCIAL"}.issubset(
        {item["code"] for item in usage_response.data}
    )
    assert duration_response.status_code == status.HTTP_200_OK
    assert {"1_MONTH", "3_MONTHS", "6_MONTHS", "12_MONTHS"}.issubset(
        {item["code"] for item in duration_response.data}
    )


@pytest.mark.django_db
def test_reference_data_endpoints_are_read_only(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/reference-data/products/",
        {"code": "NEW_PRODUCT", "label": "New product"},
        format="json",
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_vehicle_genre_rejects_subcategory_from_another_category():
    category = VehicleCategory.objects.get(code="TOURISME")
    other_subcategory = VehicleSubCategory.objects.get(code="MOTO")

    genre = VehicleGenre(
        category=category,
        subcategory=other_subcategory,
        code="INVALID_GENRE",
        ass_code="INVALID_GENRE",
        label="Invalid genre",
    )

    with pytest.raises(ValidationError):
        genre.full_clean()


@pytest.mark.django_db
def test_seeded_guarantee_codes_are_unique_and_stable():
    assert GuaranteeReference.objects.filter(code="RC").count() == 1
    assert GuaranteeReference.objects.filter(code="CEDEAO").count() == 1
