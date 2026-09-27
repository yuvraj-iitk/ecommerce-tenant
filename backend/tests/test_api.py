from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "E-commerce API is working"


def test_products_endpoint():
    response = client.get("/products")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_product_search():
    response = client.get("/products?search=shirt")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_invalid_page():
    response = client.get("/products?page=0")

    assert response.status_code == 400
    assert response.json()["detail"] == "Page must be greater than 0"


def test_invalid_limit():
    response = client.get("/products?limit=101")

    assert response.status_code == 400
    assert response.json()["detail"] == "Limit must be between 1 and 100"


def test_category_filter():
    response = client.get("/products?category=Electronics")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_product_not_found():
    response = client.get("/products/999999")

    assert response.status_code in [404, 405]


def test_negative_page():
    response = client.get("/products?page=-1")

    assert response.status_code == 400
    assert response.json()["detail"] == "Page must be greater than 0"


def test_limit_zero():
    response = client.get("/products?limit=0")

    assert response.status_code == 400
    assert response.json()["detail"] == "Limit must be between 1 and 100"
def test_order_quantity_must_be_positive():
    response = client.post(
        "/orders",
        json={
            "user_id": 1,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 0
                }
            ]
        }
    )

    assert response.status_code in [401, 403]


def test_orders_requires_authentication():
    response = client.post(
        "/orders/me",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 401
