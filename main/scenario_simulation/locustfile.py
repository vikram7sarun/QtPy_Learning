
from locust import HttpUser, task, between
import random

class ECommerceUser(HttpUser):
    wait_time = between(1, 5)  # Simulate realistic delays between actions

    @task(3)
    def browse_products(self):
        self.client.get("/products")
        self.client.get(f"/products/{random.randint(1, 100)}")

    @task(1)
    def view_cart(self):
        self.client.get("/cart")

    @task(2)
    def add_to_cart(self):
        product_id = random.randint(1, 100)
        self.client.post("/cart", json={"product_id": product_id, "quantity": random.randint(1, 3)})

    @task(1)
    def checkout(self):
        self.client.post("/checkout", json={"payment_method": "credit_card"})
