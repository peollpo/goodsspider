# -*- coding: utf-8 -*-
"""Simple test to check if the API is working."""
import sys
import requests

BASE_URL = "http://localhost:1337/api"

print("[TEST] Testing claim endpoint...")
sys.stdout.flush()

try:
    response = requests.post(
        f"{BASE_URL}/crawl-tasks/actions/claim",
        json={"workerId": "test-worker", "limit": 1},
        timeout=10,
    )
    print(f"[TEST] Response status: {response.status_code}")
    sys.stdout.flush()

    if response.status_code == 200:
        data = response.json()
        tasks = data.get("data", [])
        print(f"[TEST] Tasks claimed: {len(tasks)}")
        sys.stdout.flush()

        if tasks:
            task = tasks[0]
            print(f"[TEST] Task structure: {task.keys()}")
            sys.stdout.flush()
            print(f"[TEST] Task data: {task}")
            sys.stdout.flush()
        else:
            print("[TEST] No tasks available")
            sys.stdout.flush()
    else:
        print(f"[TEST] Error: {response.text}")
        sys.stdout.flush()

except Exception as e:
    print(f"[TEST] Exception: {e}")
    sys.stdout.flush()

print("[TEST] Test completed")
sys.stdout.flush()
