from locust import HttpUser, task, between
from typing import List, Optional
import random
from queue import Queue

user_queue = Queue()

with open("../scripts/locust_users.txt") as f:
    for line in f:
        username = line.strip()
        if not username:
            continue
        user_queue.put(username)


class TodoUser(HttpUser):
    wait_time = between(0.01, 0.05)

    host = "http://80.93.52.25"

    token: Optional[str] = None
    task_ids: Optional[List[int]]
    category_ids: Optional[List[int]] = None

    username = "lola"
    password = "12345678"

    def on_start(self) -> None:
        self.task_ids = []
        self.category_ids = []

        if user_queue.empty():
            raise RuntimeError("No more users available")

        self.username = user_queue.get()
        self.password = "12345678"
        self.logged_in = False
        self.login()

    def on_stop(self):
        if getattr(self, "username", None) and getattr(self, "logged_in", False):
            user_queue.put(self.username)

    def login(self):
        payload = {"username": self.username, "password": self.password}
        with self.client.post(
                "/auth/login", data=payload, name="POST /auth/login", catch_response=True) as resp:

            if resp.status_code != 200:
                resp.failure(f"Login failed: {resp.status_code} {resp.text}")
                return

            data = resp.json()
            token = data.get("access_token")

            if not token:
                resp.failure(f"No access_token in response: {data}")
                return

            self.token = token
            self.logged_in = True
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(5)
    def list_tasks(self):
        with self.client.get("/tasks", name="GET /tasks", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"List tasks failed: {r.status_code} {r.text}")

    @task(2)
    def me(self):
        with self.client.get("/users/me", name="GET /users/me", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"me: {r.status_code} {r.text}")

    @task(2)
    def create_task(self):
        payload = {"title": f"locust-{random.randint(1, 10_000_000_000)}"}
        with self.client.post("/tasks", json=payload, name="POST /tasks", catch_response=True) as r:
            if r.status_code not in (200, 201):
                r.failure(f"create_task: {r.status_code} {r.text}")
                return

            data = r.json()
            task_id = data.get("id") or data.get("task_id")
            if task_id:
                self.task_ids.append(task_id)

    @task(1)
    def patch_task(self):
        if not self.task_ids:
            return
        task_id = random.choice(self.task_ids)
        payload = {"title": f"updated-{random.randint(1, 10_000_000)}"}
        with self.client.patch(
                f"/tasks/{task_id}", json=payload, name="PATCH /tasks/:id", catch_response=True
        ) as r:
            if r.status_code != 200:
                r.failure(f"patch_task: {r.status_code} {r.text}")

    @task(1)
    def delete_task(self):
        if not self.task_ids:
            return
        task_id = self.task_ids.pop()
        with self.client.delete(
                f"/tasks/{task_id}", name="DELETE /tasks/:id", catch_response=True) as r:
            if r.status_code not in (200, 204):
                r.failure(f"delete_task: {r.status_code} {r.text}")
