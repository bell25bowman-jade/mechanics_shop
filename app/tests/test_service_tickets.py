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


class ServiceTicketTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            customer = Customer(
                name="Test User",
                email="test@tickets.com",
                password=generate_password_hash("123456"),
                make_model="Ford F-150",
                date=date(2026, 6, 21),
            )
            db.session.add(customer)
            db.session.commit()
            self.customer_id = customer.id

        login = self.client.post(
            "/customers/login",
            json={"email": "test@tickets.com", "password": "123456"},
        )
        self.token = login.get_json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

        self.mechanic_payload: dict[str, object] = {
            "name": "Sam Fixit",
            "email": "sam@shop.com",
            "address": "456 Garage Rd",
            "phone": "555-9999",
            "salary": 55000.0,
        }

        self.inventory_payload: dict[str, object] = {
            "name": "Brake Pad",
            "price": 79.99,
        }

        self.ticket_payload: dict[str, object] = {
            "description": "Customer reports squeaking brakes",
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_mechanic(self) -> Any:
        return self.client.post("/mechanics/", json=self.mechanic_payload)

    def _create_inventory_item(self) -> Any:
        return self.client.post(
            "/inventory/", json=self.inventory_payload, headers=self.auth_headers
        )

    def _create_ticket(self, payload: dict[str, object] | None = None) -> Any:
        return self.client.post(
            "/service-tickets/",
            json=payload or self.ticket_payload,
            headers=self.auth_headers,
        )

    def test_create_ticket(self):
        res = self._create_ticket()
        self.assertEqual(res.status_code, 201)

    def test_create_ticket_missing_description(self):
        res = self.client.post(
            "/service-tickets/",
            json={},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 400)

    def test_get_service_tickets(self):
        self._create_ticket()
        res = self.client.get("/service-tickets/")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_get_service_ticket(self):
        ticket = self._create_ticket().get_json()
        res = self.client.get(f"/service-tickets/{ticket['id']}")
        self.assertEqual(res.status_code, 200)

    def test_get_service_ticket_not_found(self):
        res = self.client.get("/service-tickets/9999")
        self.assertEqual(res.status_code, 404)

    def test_update_service_ticket(self):
        ticket = self._create_ticket().get_json()
        res = self.client.put(
            f"/service-tickets/{ticket['id']}",
            json={"description": "Updated description"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_service_ticket(self):
        ticket = self._create_ticket().get_json()
        res = self.client.delete(
            f"/service-tickets/{ticket['id']}", headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)

    def test_assign_mechanic(self):
        mechanic = self._create_mechanic().get_json()
        ticket = self._create_ticket().get_json()
        res = self.client.put(
            f"/service-tickets/{ticket['id']}/assign-mechanic",
            json={"mechanic_id": mechanic["id"]},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_remove_mechanic(self):
        mechanic = self._create_mechanic().get_json()
        ticket = self._create_ticket({"description": "Needs mechanic", "mechanic_id": mechanic["id"]}).get_json()
        res = self.client.put(
            f"/service-tickets/{ticket['id']}/remove-mechanic",
            json={},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_edit_service_ticket_mechanics(self):
        mechanic = self._create_mechanic().get_json()
        ticket = self._create_ticket().get_json()
        res = self.client.put(
            f"/service-tickets/{ticket['id']}/edit",
            json={"add_ids": [mechanic["id"]], "remove_ids": []},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_add_part_to_service_ticket(self):
        inventory_item = self._create_inventory_item().get_json()
        ticket = self._create_ticket().get_json()
        res = self.client.put(
            f"/service-tickets/{ticket['id']}/add-part",
            json={"inventory_id": inventory_item["id"]},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()