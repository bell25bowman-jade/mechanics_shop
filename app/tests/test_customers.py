import sys
import unittest
from pathlib import Path


# Support running this file directly via "Run Python File".
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import db

class CustomerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

        self.customer_payload = {
            "name": "John Doe",
            "email": "john@test.com",
            "password": "123456",
            "make_model": "Honda Civic",
            "date": "2026-06-21"
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_customer(self):
        res = self.client.post("/customers", json=self.customer_payload)
        self.assertEqual(res.status_code, 201)

    def test_get_customers(self):
        self.client.post("/customers", json=self.customer_payload)

        res = self.client.get("/customers")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertIn("items", body)
        self.assertTrue(len(body["items"]) >= 1)


if __name__ == "__main__":
    unittest.main()