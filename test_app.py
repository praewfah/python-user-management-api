from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # ใช้ SQLite สำหรับเทสต์เพื่อให้รันเร็วและแยกจาก DB จริง
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _user_payload(index: int, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": f"User {index}",
        "age": 20 + index,
        "email": f"user{index}@example.com",
        "avatarUrl": f"https://example.com/avatar-{index}.png",
    }
    payload.update(overrides)
    return payload


def test_health_check_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/user",
        json=_user_payload(1, name="  Alice  ", email="ALICE@EXAMPLE.COM"),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Alice"
    assert data["age"] == 21
    assert data["email"] == "alice@example.com"
    assert data["avatar_url"] == "https://example.com/avatar-1.png"


def test_create_user_duplicate_email_returns_conflict(client: TestClient) -> None:
    first = client.post("/api/user", json=_user_payload(2, email="dupe@example.com"))
    assert first.status_code == 201

    duplicate = client.post("/api/user", json=_user_payload(3, email="DUPE@example.com"))
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email already exists in the system"


def test_create_user_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post("/api/user", json=_user_payload(4, email="not-an-email"))
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload_override",
    [
        {"age": "twenty"},
        {"name": "   "},
        {"avatarUrl": ""},
        {"email": {"unexpected": "object"}},
    ],
)
def test_create_user_rejects_unexpected_input_shapes(
    client: TestClient, payload_override: dict[str, object]
) -> None:
    response = client.post("/api/user", json=_user_payload(5, **payload_override))
    assert response.status_code == 422


def test_get_users_pagination_returns_stable_slice(client: TestClient) -> None:
    for i in range(1, 6):
        created = client.post("/api/user", json=_user_payload(i))
        assert created.status_code == 201

    response = client.get("/api/user", params={"start": 1, "limit": 2})
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["total_pages"] == 3
    assert len(data["items"]) == 2
    assert data["items"][0]["email"] == "user2@example.com"
    assert data["items"][1]["email"] == "user3@example.com"


def test_get_users_short_query_does_not_apply_search_filter(client: TestClient) -> None:
    for i in range(1, 4):
        created = client.post("/api/user", json=_user_payload(i))
        assert created.status_code == 201

    response = client.get("/api/user", params={"q": "us", "start": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_get_users_contains_search_applied_for_query_length_three(client: TestClient) -> None:
    created_1 = client.post("/api/user", json=_user_payload(1, email="alice@example.com"))
    created_2 = client.post("/api/user", json=_user_payload(2, email="my-alice@example.com"))
    created_3 = client.post("/api/user", json=_user_payload(3, email="bob@example.com"))
    assert created_1.status_code == 201
    assert created_2.status_code == 201
    assert created_3.status_code == 201

    response = client.get("/api/user", params={"q": "ali", "start": 0, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    emails = {item["email"] for item in data["items"]}
    assert emails == {"alice@example.com", "my-alice@example.com"}


def test_delete_user_twice_returns_failed_on_second_attempt(client: TestClient) -> None:
    created = client.post("/api/user", json=_user_payload(9))
    assert created.status_code == 201
    user_id = created.json()["id"]

    first_delete = client.delete(f"/api/user/{user_id}")
    assert first_delete.status_code == 200
    assert first_delete.json() == {"status": "success"}

    second_delete = client.delete(f"/api/user/{user_id}")
    assert second_delete.status_code == 200
    assert second_delete.json() == {"status": "failed", "message": "User already deleted"}


def test_deleted_user_not_returned_in_list(client: TestClient) -> None:
    created = client.post("/api/user", json=_user_payload(10))
    assert created.status_code == 201
    user_id = created.json()["id"]

    client.delete(f"/api/user/{user_id}")
    response = client.get("/api/user")
    assert response.status_code == 200
    assert all(user["id"] != user_id for user in response.json()["items"])
