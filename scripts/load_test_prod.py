# type: ignore
"""
locust -f load_test_prod.py --headless -u 1000 -r 10 -t 5m
"""

from locust import HttpUser, constant, task


class QuickstartUser(HttpUser):
    wait_time = constant(0)
    host = "https://whatbikeswin.com"

    @task
    def test_get_method(self):
        self.client.get("/")

    @task
    def test_get_method(self):
        self.client.get("/api/racing/insight/popular-pairs")

    @task
    def test_get_method(self):
        self.client.get("/api/racing/insight/recent-races")

    def on_start(self):
        ...
