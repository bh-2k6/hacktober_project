import io
import json
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from app.database import init_db, get_db_connection

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    with get_db_connection() as conn:
        conn.execute("DELETE FROM matches")
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM contact_requests")
    yield


def create_test_image(format="PNG", size=(100, 100), color="red"):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf


class TestCreateItem:
    def test_create_item_without_image(self):
        response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["type"] == "lost"
        assert data["image_path"] is None
        assert data["status"] == "active"

    def test_create_item_with_image(self):
        img_buf = create_test_image()
        response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item with Image",
                "description": "A test item with image",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
            files={"image": ("test.png", img_buf, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Item with Image"
        assert data["image_path"] is not None
        assert data["image_path"].startswith("/uploads/")

    def test_create_item_invalid_image_format(self):
        response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
            files={"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert response.status_code == 400
        assert "Invalid image format" in response.json()["detail"]

    def test_create_item_oversized_image(self):
        large_buf = io.BytesIO(b"x" * (11 * 1024 * 1024))
        response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
            files={"image": ("large.png", large_buf, "image/png")},
        )
        assert response.status_code == 400
        assert "Image too large" in response.json()["detail"]

    def test_create_item_invalid_type(self):
        response = client.post(
            "/api/items",
            data={
                "type": "invalid",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        assert response.status_code == 400


class TestListItem:
    def test_list_items_empty(self):
        response = client.get("/api/items")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_items_with_filter(self):
        client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Lost Item",
                "description": "A lost item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        client.post(
            "/api/items",
            data={
                "type": "found",
                "title": "Found Item",
                "description": "A found item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )

        response = client.get("/api/items?type=lost")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "lost"


class TestGetItem:
    def test_get_item_not_found(self):
        response = client.get("/api/items/9999")
        assert response.status_code == 404

    def test_get_item_success(self):
        create_response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        item_id = create_response.json()["id"]

        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Item"


class TestUpdateItem:
    def test_update_item_status(self):
        create_response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        item_id = create_response.json()["id"]

        response = client.patch(
            f"/api/items/{item_id}",
            json={"status": "reunited"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "reunited"


class TestDeleteItem:
    def test_delete_item(self):
        create_response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
        )
        item_id = create_response.json()["id"]

        response = client.delete(f"/api/items/{item_id}")
        assert response.status_code == 200

        get_response = client.get(f"/api/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_item_with_image(self):
        img_buf = create_test_image()
        create_response = client.post(
            "/api/items",
            data={
                "type": "lost",
                "title": "Test Item with Image",
                "description": "A test item",
                "location": "Test Location",
                "date_time": "2026-10-05T12:00:00",
            },
            files={"image": ("test.png", img_buf, "image/png")},
        )
        item_id = create_response.json()["id"]
        image_path = create_response.json()["image_path"]

        response = client.delete(f"/api/items/{item_id}")
        assert response.status_code == 200

        if image_path and image_path.startswith("/uploads/"):
            filename = image_path[len("/uploads/"):]
            filepath = Path(__file__).parent.parent / "data" / "uploads" / filename
            assert not filepath.exists()
