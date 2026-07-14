import unittest

from app import app, db, User, Order
from werkzeug.security import generate_password_hash


class AdminOrdersTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SECRET_KEY="test-secret")
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                phone="+995555000000",
                address="თბილისი",
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    def test_admin_page_shows_order_number_for_each_order(self):
        with app.app_context():
            order = Order(
                username="client",
                phone="+995555111111",
                address="თბილისი",
                payment_method="Cash on Delivery",
                total_price=25.0,
                items="Arduino Uno R3 x1",
            )
            db.session.add(order)
            db.session.commit()

        self.client.post(
            "/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )

        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("შეკვეთის ნომერი", body)
        self.assertIn(f"#{order.id}", body)


if __name__ == "__main__":
    unittest.main()
