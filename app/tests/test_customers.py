import sys
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import Customer, db
from werkzeug.security import generate_password_hash


class CustomerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.auth_customer = Customer(
                name="Auth User",
                email="auth@customers.com",
                password=generate_password_hash("123456"),
                make_model="Toyota Corolla",
                date=date(2026, 6, 21),
            )
            db.session.add(self.auth_customer)
            db.session.commit()
            self.customer_id = self.auth_customer.id

        login_response = self.client.post(
            "/customers/login",
            json={"email": "auth@customers.com", "password": "123456"},
        )
        self.token = login_response.get_json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

        self.customer_payload = {
            "name": "John Doe",
            "email": "john@test.com",
            "password": "123456",
            "make_model": "Honda Civic",
            "date": "2026-06-21",
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_info_endpoint(self):
        res = self.client.get("/customers/info")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertIn("message", body)
        self.assertIn("endpoints", body)

    def test_create_customer(self):
        res = self.client.post("/customers/", json=self.customer_payload)
        self.assertEqual(res.status_code, 201)

    def test_create_customer_validation_error(self):
        res = self.client.post(
            "/customers/",
            json={"name": "Missing Fields", "email": "bad@test.com"},
        )
        self.assertEqual(res.status_code, 400)

    def test_login_customer(self):
        res = self.client.post(
            "/customers/login",
            json={"email": "auth@customers.com", "password": "123456"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("token", res.get_json())

    def test_login_customer_invalid_password(self):
        res = self.client.post(
            "/customers/login",
            json={"email": "auth@customers.com", "password": "wrong"},
        )
        self.assertEqual(res.status_code, 401)

    def test_get_customers(self):
        res = self.client.get("/customers/")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertIn("items", body)
        self.assertTrue(len(body["items"]) >= 1)

    def test_get_customer_by_id(self):
        res = self.client.get(f"/customers/{self.customer_id}")
        self.assertEqual(res.status_code, 200)

    def test_get_customer_not_found(self):
        res = self.client.get("/customers/9999")
        self.assertEqual(res.status_code, 404)

    def test_get_my_tickets(self):
        create_ticket = self.client.post(
            "/service-tickets/",
            json={"description": "Brake inspection"},
            headers=self.auth_headers,
        )
        self.assertEqual(create_ticket.status_code, 201)

        res = self.client.get("/customers/my-tickets", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_update_customer(self):
        res = self.client.put(
            f"/customers/{self.customer_id}",
            json={"name": "Updated Name"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_update_customer_forbidden(self):
        res = self.client.put(
            f"/customers/{self.customer_id + 1}",
            json={"name": "Updated Name"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 403)

    def test_delete_customer(self):
        res = self.client.delete(
            f"/customers/{self.customer_id}", headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_customer_forbidden(self):
        res = self.client.delete(
            f"/customers/{self.customer_id + 1}", headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()