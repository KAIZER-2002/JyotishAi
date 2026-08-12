from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import types
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")
sys.modules.setdefault(
    "swisseph",
    types.SimpleNamespace(
        houses=types.SimpleNamespace(P_PLACIDUS=1),
        FLG_SWIEPH=2,
        FLG_MOSEPH=4,
        FLG_SIDEREAL=65536,
        SUN=0,
        MOON=1,
        MARS=4,
        MERCURY=2,
        JUPITER=5,
        VENUS=3,
        SATURN=6,
        TRUE_NODE=11,
        SIDM_LAHIRI=1,
        SIDM_RAMAN=3,
        SIDM_KRISHNAMURTI=5,
        SIDM_TRUE_CHITRA=27,
    ),
)

from app.api.v1.routes.astrology import get_astrology_service, router
from app.api.deps import get_current_user
from app.db.models.user import User


ENDPOINT = "/astrology/birth-chart"
NAVAMSA_ENDPOINT = "/astrology/navamsa"
DASAMSA_ENDPOINT = "/astrology/d10"
SHASTIAMSA_ENDPOINT = "/astrology/d60"
VIMSHOTTARI_DASHA_ENDPOINT = "/astrology/vimshottari-dasha"


def valid_request_body() -> dict:
    return {
        "date": "1990-01-01T12:00:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata",
        "ayanamsa": "Lahiri",
        "house_system": 1,
    }


def birth_chart_response() -> dict:
    return {
        "ascendant": {
            "zodiac_sign": "Aries",
            "longitude": 12.5,
            "nakshatra": "Ashwini",
            "pada": 1,
            "degree_within_sign": 12.5,
        },
        "planets": [
            {
                "planet": "Sun",
                "longitude": 45.0,
                "zodiac_sign": "Taurus",
                "house_number": 2,
                "retrograde": False,
                "nakshatra": "Rohini",
                "pada": 2,
                "degree_within_sign": 15.0,
            }
        ],
        "houses": [
            {
                "house_number": 1,
                "start_longitude": 12.5,
                "end_longitude": 42.5,
            }
        ],
    }


def navamsa_chart_response() -> dict:
    return {
        "ascendant": {
            "zodiac_sign": "Libra",
            "longitude": 180.0,
            "nakshatra": "Chitra",
            "pada": 3,
            "degree_within_sign": 0.0,
        },
        "planets": [
            {
                "planet": "Sun",
                "longitude": 0.0,
                "zodiac_sign": "Aries",
                "house_number": 7,
                "retrograde": False,
                "nakshatra": "Ashwini",
                "pada": 1,
                "degree_within_sign": 0.0,
            }
        ],
        "houses": [
            {
                "house_number": 1,
                "start_longitude": 180.0,
                "end_longitude": 210.0,
            }
        ],
    }


def dasamsa_chart_response() -> dict:
    return {
        "ascendant": {
            "zodiac_sign": "Capricorn",
            "longitude": 270.0,
            "nakshatra": "Uttara Ashadha",
            "pada": 2,
            "degree_within_sign": 0.0,
        },
        "planets": [
            {
                "planet": "Sun",
                "longitude": 0.0,
                "zodiac_sign": "Aries",
                "house_number": 4,
                "retrograde": False,
                "nakshatra": "Ashwini",
                "pada": 1,
                "degree_within_sign": 0.0,
            }
        ],
        "houses": [
            {
                "house_number": 1,
                "start_longitude": 270.0,
                "end_longitude": 300.0,
            }
        ],
    }


def shastiamsa_chart_response() -> dict:
    return {
        "ascendant": {
            "zodiac_sign": "Taurus",
            "longitude": 30.0,
            "nakshatra": "Krittika",
            "pada": 2,
            "degree_within_sign": 0.0,
        },
        "planets": [
            {
                "planet": "Sun",
                "longitude": 60.0,
                "zodiac_sign": "Gemini",
                "house_number": 2,
                "retrograde": False,
                "nakshatra": "Mrigasira",
                "pada": 3,
                "degree_within_sign": 0.0,
            }
        ],
        "houses": [
            {
                "house_number": 1,
                "start_longitude": 30.0,
                "end_longitude": 60.0,
            }
        ],
    }


def vimshottari_dasha_response() -> dict:
    return {
        "mahadashas": [
            {
                "lord": "Ketu",
                "start_datetime": "1990-01-01T12:00:00Z",
                "end_datetime": "1991-01-01T12:00:00Z",
                "duration_days": 365.0,
                "level": "Mahadasha",
                "antardashas": [
                    {
                        "lord": "Ketu",
                        "start_datetime": "1990-01-01T12:00:00Z",
                        "end_datetime": "1990-02-01T12:00:00Z",
                        "duration_days": 31.0,
                        "level": "Antardasha",
                        "pratyantars": [
                            {
                                "lord": "Ketu",
                                "start_datetime": "1990-01-01T12:00:00Z",
                                "end_datetime": "1990-01-03T12:00:00Z",
                                "duration_days": 2.0,
                                "level": "Pratyantar Dasha",
                            }
                        ],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def astrology_service_mock() -> AsyncMock:
    service = AsyncMock()
    service.generate_birth_chart.return_value = birth_chart_response()
    service.generate_navamsa_chart.return_value = navamsa_chart_response()
    service.generate_dasamsa_chart.return_value = dasamsa_chart_response()
    service.generate_shastiamsa_chart.return_value = shastiamsa_chart_response()
    service.generate_vimshottari_dasha.return_value = vimshottari_dasha_response()
    return service


@pytest.fixture
def client(astrology_service_mock: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    
    # Mock authentication
    mock_user = User(id="00000000-0000-0000-0000-000000000000", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_astrology_service] = lambda: astrology_service_mock

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_birth_chart_generation_success(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    assert response.json() == birth_chart_response()

    astrology_service_mock.generate_birth_chart.assert_awaited_once()
    call_kwargs = astrology_service_mock.generate_birth_chart.await_args.kwargs
    assert call_kwargs["birth_datetime"] == datetime(
        1990, 1, 1, 12, 0, tzinfo=timezone.utc
    )
    assert call_kwargs["latitude"] == 28.6139
    assert call_kwargs["longitude"] == 77.2090
    assert call_kwargs["ayanamsa"].value == "Lahiri"
    assert call_kwargs["house_system"] == 1


def test_birth_chart_invalid_latitude(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["latitude"] = 91

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_invalid_longitude(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["longitude"] = 181

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_invalid_datetime(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["date"] = "not-a-date"

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_naive_datetime(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["date"] = "1990-01-01T12:00:00"

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_invalid_ayanamsa(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["ayanamsa"] = "Invalid"

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_invalid_house_system(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["house_system"] = 0

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


@pytest.mark.parametrize(
    "field",
    ["date", "latitude", "longitude", "timezone", "ayanamsa", "house_system"],
)
def test_birth_chart_missing_required_fields(
    client: TestClient,
    astrology_service_mock: AsyncMock,
    field: str,
) -> None:
    body = valid_request_body()
    del body[field]

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_missing_house_system(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    del body["house_system"]

    response = client.post(ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_invalid_request_body(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(ENDPOINT, json=["not", "an", "object"])

    assert response.status_code == 422
    astrology_service_mock.generate_birth_chart.assert_not_awaited()


def test_birth_chart_service_exception_handling(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_birth_chart.side_effect = ValueError(
        "Invalid birth chart input."
    )

    response = client.post(ENDPOINT, json=valid_request_body())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid birth chart input."}
    astrology_service_mock.generate_birth_chart.assert_awaited_once()


def test_birth_chart_response_serialization(client: TestClient) -> None:
    response = client.post(ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["ascendant"]["zodiac_sign"] == "Aries"
    assert body["planets"][0]["planet"] == "Sun"
    assert body["planets"][0]["house_number"] == 2
    assert body["houses"][0]["house_number"] == 1


def test_birth_chart_route_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/astrology/birth-chart" in paths


def test_navamsa_chart_generation_success(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(NAVAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    assert response.json() == navamsa_chart_response()

    astrology_service_mock.generate_navamsa_chart.assert_awaited_once()
    call_kwargs = astrology_service_mock.generate_navamsa_chart.await_args.kwargs
    assert call_kwargs["birth_datetime"] == datetime(
        1990, 1, 1, 12, 0, tzinfo=timezone.utc
    )
    assert call_kwargs["latitude"] == 28.6139
    assert call_kwargs["longitude"] == 77.2090
    assert call_kwargs["ayanamsa"].value == "Lahiri"
    assert call_kwargs["house_system"] == 1


def test_navamsa_request_validation(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["latitude"] = 91

    response = client.post(NAVAMSA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_navamsa_chart.assert_not_awaited()


def test_navamsa_service_exception_handling(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_navamsa_chart.side_effect = ValueError(
        "Invalid Navamsa input."
    )

    response = client.post(NAVAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Navamsa input."}
    astrology_service_mock.generate_navamsa_chart.assert_awaited_once()


def test_navamsa_response_serialization(client: TestClient) -> None:
    response = client.post(NAVAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["ascendant"]["zodiac_sign"] == "Libra"
    assert body["planets"][0]["planet"] == "Sun"
    assert body["planets"][0]["house_number"] == 7
    assert body["houses"][0]["house_number"] == 1


def test_navamsa_route_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/astrology/navamsa" in paths


def test_dasamsa_chart_generation_success(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(DASAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    assert response.json() == dasamsa_chart_response()

    astrology_service_mock.generate_dasamsa_chart.assert_awaited_once()
    call_kwargs = astrology_service_mock.generate_dasamsa_chart.await_args.kwargs
    assert call_kwargs["birth_datetime"] == datetime(
        1990, 1, 1, 12, 0, tzinfo=timezone.utc
    )
    assert call_kwargs["latitude"] == 28.6139
    assert call_kwargs["longitude"] == 77.2090
    assert call_kwargs["ayanamsa"].value == "Lahiri"
    assert call_kwargs["house_system"] == 1


def test_dasamsa_request_validation(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["longitude"] = 181

    response = client.post(DASAMSA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_dasamsa_chart.assert_not_awaited()


def test_dasamsa_service_exception_handling(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_dasamsa_chart.side_effect = ValueError(
        "Invalid Dasamsa input."
    )

    response = client.post(DASAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Dasamsa input."}
    astrology_service_mock.generate_dasamsa_chart.assert_awaited_once()


def test_dasamsa_response_serialization(client: TestClient) -> None:
    response = client.post(DASAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["ascendant"]["zodiac_sign"] == "Capricorn"
    assert body["planets"][0]["planet"] == "Sun"
    assert body["planets"][0]["house_number"] == 4
    assert body["houses"][0]["house_number"] == 1


def test_dasamsa_route_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/astrology/d10" in paths


def test_shastiamsa_chart_generation_success(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(SHASTIAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    assert response.json() == shastiamsa_chart_response()

    astrology_service_mock.generate_shastiamsa_chart.assert_awaited_once()
    call_kwargs = astrology_service_mock.generate_shastiamsa_chart.await_args.kwargs
    assert call_kwargs["birth_datetime"] == datetime(
        1990, 1, 1, 12, 0, tzinfo=timezone.utc
    )
    assert call_kwargs["latitude"] == 28.6139
    assert call_kwargs["longitude"] == 77.2090
    assert call_kwargs["ayanamsa"].value == "Lahiri"
    assert call_kwargs["house_system"] == 1


def test_shastiamsa_request_validation(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["date"] = "not-a-date"

    response = client.post(SHASTIAMSA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_shastiamsa_chart.assert_not_awaited()


def test_shastiamsa_service_exception_handling(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_shastiamsa_chart.side_effect = ValueError(
        "Invalid Shastiamsa input."
    )

    response = client.post(SHASTIAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Shastiamsa input."}
    astrology_service_mock.generate_shastiamsa_chart.assert_awaited_once()


def test_shastiamsa_response_serialization(client: TestClient) -> None:
    response = client.post(SHASTIAMSA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["ascendant"]["zodiac_sign"] == "Taurus"
    assert body["planets"][0]["planet"] == "Sun"
    assert body["planets"][0]["house_number"] == 2
    assert body["houses"][0]["house_number"] == 1


def test_shastiamsa_route_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/astrology/d60" in paths


def test_vimshottari_dasha_generation_success(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    assert response.json() == vimshottari_dasha_response()

    astrology_service_mock.generate_vimshottari_dasha.assert_awaited_once()
    call_kwargs = astrology_service_mock.generate_vimshottari_dasha.await_args.kwargs
    assert call_kwargs["birth_datetime"] == datetime(
        1990, 1, 1, 12, 0, tzinfo=timezone.utc
    )
    assert call_kwargs["latitude"] == 28.6139
    assert call_kwargs["longitude"] == 77.2090
    assert call_kwargs["ayanamsa"].value == "Lahiri"
    assert call_kwargs["house_system"] == 1


def test_vimshottari_dasha_invalid_request_body(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=["not", "an", "object"])

    assert response.status_code == 422
    astrology_service_mock.generate_vimshottari_dasha.assert_not_awaited()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", 91),
        ("longitude", 181),
    ],
)
def test_vimshottari_dasha_invalid_coordinates(
    client: TestClient,
    astrology_service_mock: AsyncMock,
    field: str,
    value: float,
) -> None:
    body = valid_request_body()
    body[field] = value

    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_vimshottari_dasha.assert_not_awaited()


@pytest.mark.parametrize("date", ["not-a-date", "1990-01-01T12:00:00"])
def test_vimshottari_dasha_invalid_datetime(
    client: TestClient,
    astrology_service_mock: AsyncMock,
    date: str,
) -> None:
    body = valid_request_body()
    body["date"] = date

    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_vimshottari_dasha.assert_not_awaited()


def test_vimshottari_dasha_invalid_ayanamsa(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    body = valid_request_body()
    body["ayanamsa"] = "Invalid"

    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=body)

    assert response.status_code == 422
    astrology_service_mock.generate_vimshottari_dasha.assert_not_awaited()


def test_vimshottari_dasha_service_value_error(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_vimshottari_dasha.side_effect = ValueError(
        "Invalid Vimshottari Dasha input."
    )

    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Vimshottari Dasha input."}
    astrology_service_mock.generate_vimshottari_dasha.assert_awaited_once()


def test_vimshottari_dasha_service_unexpected_exception(
    client: TestClient,
    astrology_service_mock: AsyncMock,
) -> None:
    astrology_service_mock.generate_vimshottari_dasha.side_effect = RuntimeError(
        "Service unavailable."
    )

    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "An unexpected error occurred while generating the Vimshottari Dasha "
            "timeline: Service unavailable."
        )
    }
    astrology_service_mock.generate_vimshottari_dasha.assert_awaited_once()


def test_vimshottari_dasha_response_serialization(client: TestClient) -> None:
    response = client.post(VIMSHOTTARI_DASHA_ENDPOINT, json=valid_request_body())

    assert response.status_code == 200
    body = response.json()
    assert body["mahadashas"][0]["lord"] == "Ketu"
    assert body["mahadashas"][0]["level"] == "Mahadasha"
    assert body["mahadashas"][0]["antardashas"][0]["level"] == "Antardasha"
    assert (
        body["mahadashas"][0]["antardashas"][0]["pratyantars"][0]["level"]
        == "Pratyantar Dasha"
    )


def test_vimshottari_dasha_route_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/astrology/vimshottari-dasha" in paths
