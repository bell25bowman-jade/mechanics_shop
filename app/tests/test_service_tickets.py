import sys
import unittest
from datetime import date
from pathlib import Path

# Support running this file directly via "Run Python File".
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

        login = self.client.post(
            "/customers/login",
            json={"email": "test@tickets.com", "password": "123456"},
        )
        self.token = login.get_json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

        self.mechanic_payload = {
            "name": "Sam Fixit",
            "email": "sam@shop.com",
            "address": "456 Garage Rd",
            "phone": "555-9999",
            "salary": 55000.0,
        }

        self.ticket_payload = {
            "description": "Customer reports squeaking brakes",
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_ticket(self):
        res = self.client.post(
            "/service-tickets/", json=self.ticket_payload, headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 201)

    def test_add_mechanic_to_ticket(self):
        # Create a mechanic (no auth required for POST /mechanics/)
        self.client.post("/mechanics/", json=self.mechanic_payload)

        # Create a ticket
        ticket_res = self.client.post(
            "/service-tickets/", json=self.ticket_payload, headers=self.auth_headers
        )
        ticket_id = ticket_res.get_json()["id"]

        # Assign mechanic to ticket
        res = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [1], "remove_ids": []},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()