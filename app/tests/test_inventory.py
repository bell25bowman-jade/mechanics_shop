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
        self.item_payload: dict[str, object] = {
            "name": "Oil Filter",
            "price": 15.99,
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_item(self, name: str = "Oil Filter", price: float = 15.99):
        return self.client.post(
            "/inventory/",
            json={"name": name, "price": price},
            headers=self.auth_headers,
        )

    def test_create_inventory_item(self):
        res = self._create_item()
        self.assertEqual(res.status_code, 201)

    def test_create_inventory_item_unauthorized(self):
        res = self.client.post("/inventory/", json=self.item_payload)
        self.assertEqual(res.status_code, 401)

    def test_get_inventory(self):
        self._create_item()
        res = self.client.get("/inventory/")
        self.assertEqual(res.status_code, 200)
        # GET /inventory returns a flat list, not a paginated wrapper
        body = res.get_json()
        self.assertIsInstance(body, list)
        self.assertTrue(len(body) >= 1)

    def test_get_inventory_item(self):
        created = self._create_item().get_json()
        res = self.client.get(f"/inventory/{created['id']}")
        self.assertEqual(res.status_code, 200)

    def test_get_inventory_item_not_found(self):
        res = self.client.get("/inventory/9999")
        self.assertEqual(res.status_code, 404)

    def test_update_inventory_item(self):
        created = self._create_item().get_json()
        res = self.client.put(
            f"/inventory/{created['id']}",
            json={"price": 19.99},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_inventory_item(self):
        created = self._create_item().get_json()
        res = self.client.delete(
            f"/inventory/{created['id']}", headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_inventory_items_bulk(self):
        first = self._create_item(name="Brake Pad", price=79.99).get_json()
        second = self._create_item(name="Air Filter", price=29.99).get_json()
        res = self.client.delete(
            "/inventory/delete",
            json={"ids": [first["id"], second["id"]]},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_inventory_items_bulk_invalid(self):
        res = self.client.delete(
            "/inventory/delete",
            json={"ids": ["bad-id"]},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
