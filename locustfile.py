from locust import HttpUser, task, between

class UserBehavior(HttpUser):
    wait_time = between(1, 3)
    @task
    def create_link(self):
        self.client.post("/links/shorten", json={
            "original_url": "https://google.com"
        })
    @task
    def redirect(self):
        res = self.client.post("/links/shorten", json={
            "original_url": "https://google.com"
        })
        code = res.json().get("short_code")
        if code:
            self.client.get(f"/{code}", allow_redirects=False)