"""Fixed worker compatible with Strapi 5 response format."""
import os
import random
import time
import requests

BASE_URL = os.getenv("WEBSPIDER_API", "http://localhost:1337/api")
WORKER_ID = os.getenv("WEBSPIDER_WORKER_ID", "fixed-worker")
CLAIM_LIMIT = int(os.getenv("WEBSPIDER_CLAIM_LIMIT", "3"))


def claim_tasks():
    """领取任务"""
    response = requests.post(
        f"{BASE_URL}/crawl-tasks/actions/claim",
        json={"workerId": WORKER_ID, "limit": CLAIM_LIMIT},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


def submit_result(task):
    """提交任务结果"""
    task_id = task["id"]

    # Strapi 5返回的数据可能直接在根级别,也可能在attributes下
    # 做兼容处理
    if "attributes" in task:
        task_data = task["attributes"]
    else:
        task_data = task

    url = task_data.get("url", f"demo-{task_id}")
    title = task_data.get("title", f"Demo product {task_id}")

    product_stub = {
        "externalId": url,
        "title": title,
        "price": round(random.uniform(10, 100), 2),
        "sales": random.randint(100, 1000),
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
            "result": {"raw": task_data.get("payload", {})},
        },
        timeout=10,
    )
    response.raise_for_status()
    print(f"[OK] Task #{task_id} completed successfully")


def run_once():
    """运行一次轮询"""
    tasks = claim_tasks()
    if not tasks:
        print("[WAIT] No tasks available, sleeping...")
        time.sleep(5)
        return

    print(f"[CLAIM] Claimed {len(tasks)} task(s)")
    for task in tasks:
        task_id = task["id"]
        # 兼容Strapi 5数据结构
        if "attributes" in task:
            task_title = task["attributes"].get("title", "Untitled")
        else:
            task_title = task.get("title", "Untitled")

        print(f"[PROCESS] Processing task #{task_id} - {task_title}")
        time.sleep(random.uniform(0.5, 1.5))  # 模拟采集延迟

        try:
            submit_result(task)
        except Exception as e:
            print(f"[ERROR] Failed to complete task #{task_id}: {e}")


if __name__ == "__main__":
    print(f"[START] Worker started: {WORKER_ID}")
    print(f"[CONFIG] API URL: {BASE_URL}")
    print(f"[CONFIG] Claim limit: {CLAIM_LIMIT}")
    print("-" * 50)

    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"[WARN] Worker error: {exc}")
            time.sleep(10)
