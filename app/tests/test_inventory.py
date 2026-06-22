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


class InventoryTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create a customer so we can log in and get a token
            customer = Customer(
                name="Test User",
                email="test@inventory.com",
                password=generate_password_hash("123456"),
                make_model="Toyota Camry",
                date=date(2026, 6, 21),
            )
            db.session.add(customer)
            db.session.commit()

        login = self.client.post(
            "/customers/login",
            json={"email": "test@inventory.com", "password": "123456"},
        )
        self.token = login.get_json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

        # Only fields the Inventory model accepts: name, price
        self.item_payload = {
            "name": "Oil Filter",
            "price": 15.99,
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_inventory_item(self):
        res = self.client.post(
            "/inventory", json=self.item_payload, headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 201)

    def test_get_inventory(self):
        self.client.post(
            "/inventory", json=self.item_payload, headers=self.auth_headers
        )
        res = self.client.get("/inventory")
        self.assertEqual(res.status_code, 200)
        # GET /inventory returns a flat list, not a paginated wrapper
        body = res.get_json()
        self.assertIsInstance(body, list)
        self.assertTrue(len(body) >= 1)


if __name__ == "__main__":
    unittest.main()
