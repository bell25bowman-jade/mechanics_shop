import sys
import unittest
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import Customer, db
from werkzeug.security import generate_password_hash


class MechanicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            customer = Customer(
                name="Auth User",
                email="auth@mechanics.com",
                password=generate_password_hash("123456"),
                make_model="Honda Accord",
                date=date(2026, 6, 21),
            )
            db.session.add(customer)
            db.session.commit()
            self.customer_id = customer.id

        login_response = self.client.post(
            "/customers/login",
            json={"email": "auth@mechanics.com", "password": "123456"},
        )
        self.token = login_response.get_json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

        self.mechanic_payload: dict[str, object] = {
            "name": "Mike Wrench",
            "email": "mike@shop.com",
            "address": "123 Main St",
            "phone": "555-1234",
            "salary": 65000,
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_mechanic(self) -> Any:
        return self.client.post("/mechanics/", json=self.mechanic_payload)

    def test_create_mechanic(self):
        res = self._create_mechanic()
        self.assertEqual(res.status_code, 201)

    def test_create_mechanic_duplicate(self):
        self._create_mechanic()
        res = self._create_mechanic()
        self.assertEqual(res.status_code, 400)

    def test_get_mechanics(self):
        self._create_mechanic()
        res = self.client.get("/mechanics/")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_get_mechanic_by_id(self):
        created = self._create_mechanic().get_json()
        res = self.client.get(f"/mechanics/{created['id']}")
        self.assertEqual(res.status_code, 200)

    def test_get_mechanic_not_found(self):
        res = self.client.get("/mechanics/9999")
        self.assertEqual(res.status_code, 404)

    def test_get_mechanic_service_tickets(self):
        mechanic = self._create_mechanic().get_json()
        ticket = self.client.post(
            "/service-tickets/",
            json={"description": "Brake inspection", "mechanic_id": mechanic["id"]},
            headers=self.auth_headers,
        )
        self.assertEqual(ticket.status_code, 201)

        res = self.client.get(f"/mechanics/{mechanic['id']}/service-tickets")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_get_mechanics_by_most_tickets(self):
        mech1 = self._create_mechanic().get_json()
        self.client.post(
            "/mechanics/",
            json={
                "name": "Second Wrench",
                "email": "second@shop.com",
                "address": "456 Side St",
                "phone": "555-5678",
                "salary": 64000,
            },
        )
        self.client.post(
            "/service-tickets/",
            json={"description": "Ticket 1", "mechanic_id": mech1["id"]},
            headers=self.auth_headers,
        )
        self.client.post(
            "/service-tickets/",
            json={"description": "Ticket 2", "mechanic_id": mech1["id"]},
            headers=self.auth_headers,
        )

        res = self.client.get("/mechanics/most-tickets")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(len(body) >= 1)

    def test_update_mechanic(self):
        created = self._create_mechanic().get_json()
        res = self.client.put(
            f"/mechanics/{created['id']}",
            json={"phone": "555-0000"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_update_mechanic_not_found(self):
        res = self.client.put(
            "/mechanics/9999",
            json={"phone": "555-0000"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 404)

    def test_delete_mechanic(self):
        created = self._create_mechanic().get_json()
        res = self.client.delete(
            f"/mechanics/{created['id']}", headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_mechanic_not_found(self):
        res = self.client.delete("/mechanics/9999", headers=self.auth_headers)
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
