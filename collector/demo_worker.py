"""Minimal demo collector that works with the Strapi backend claim/complete endpoints."""
from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, List

import requests

BASE_URL = os.getenv("WEBSPIDER_API", "http://localhost:1337/api")
WORKER_ID = os.getenv("WEBSPIDER_WORKER_ID", "demo-worker")
CLAIM_LIMIT = int(os.getenv("WEBSPIDER_CLAIM_LIMIT", "3"))


def claim_tasks() -> List[Dict[str, Any]]:
    response = requests.post(
        f"{BASE_URL}/crawl-tasks/actions/claim",
        json={"workerId": WORKER_ID, "limit": CLAIM_LIMIT},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


def submit_result(task: Dict[str, Any]) -> None:
    task_id = task["id"]
    product_stub = {
        "externalId": task["attributes"].get("url", f"demo-{task_id}"),
        "title": task["attributes"].get("title", f"Demo product {task_id}"),
        "price": round(random.uniform(10, 100), 2),
        "sales": random.randint(0, 1000),
        "store": {
            "externalId": "demo-store",
            "name": "Demo Store",
        },
        "metadata": {
            "source": "demo",
            "claimedAt": time.time(),
        },
    }

    response = requests.post(
        f"{BASE_URL}/crawl-tasks/{task_id}/actions/complete",
        json={
            "state": "done",
            "product": product_stub,
            "result": {"raw": task["attributes"].get("payload", {})},
        },
        timeout=10,
    )
    response.raise_for_status()


def run_once() -> None:
    tasks = claim_tasks()
    if not tasks:
        print("No tasks available, sleeping...")
        time.sleep(5)
        return

    for task in tasks:
        print(f"Processing task #{task['id']} - {task['attributes'].get('title')}")
        time.sleep(random.uniform(0.5, 1.5))
        submit_result(task)


if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception as exc:  # noqa: BLE001
            print(f"Worker error: {exc}")
            time.sleep(10)


