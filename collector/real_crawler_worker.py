# -*- coding: utf-8 -*-
"""真实的小红书商品采集Worker - 调用实际API获取商品数据"""
import os
import re
import time
import requests
import json

BASE_URL = os.getenv("WEBSPIDER_API", "http://localhost:1337/api")
WORKER_ID = os.getenv("WEBSPIDER_WORKER_ID", "real-crawler-worker")
CLAIM_LIMIT = int(os.getenv("WEBSPIDER_CLAIM_LIMIT", "3"))


def extract_item_id(url):
    """从商品URL中提取item_id"""
    # 支持多种URL格式
    # https://www.xiaohongshu.com/goods-detail/684ebfff57fa160001d48e6f
    # https://mall.xiaohongshu.com/goods-detail/684ebfff57fa160001d48e6f
    match = re.search(r'goods-detail/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None


def fetch_product_data(item_id):
    """调用小红书API获取真实商品数据"""
    api_url = f"https://mall.xiaohongshu.com/api/store/jpd/edith/detail/h5/toc"
    params = {
        'version': '0.0.5',
        'item_id': item_id
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.xiaohongshu.com/',
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            print(f"[ERROR] API returned error: {data.get('msg')}")
            return None

        return data.get('data')
    except Exception as e:
        print(f"[ERROR] Failed to fetch product data: {e}")
        return None


def parse_product_data(data):
    """解析API返回的商品数据"""
    if not data or 'template_data' not in data:
        return None

    template_data = data['template_data']
    if not template_data or len(template_data) == 0:
        return None

    info = template_data[0]

    # 提取商品信息
    result = {
        'title': None,
        'price': None,
        'sales': None,
        'seller_name': None,
        'seller_id': None,
        'cover_url': None,
        'description': None,
        'images': []
    }

    # 标题和基本信息
    if 'descriptionH5' in info:
        desc = info['descriptionH5']
        result['title'] = desc.get('name')
        result['item_id'] = desc.get('skuId')

    # 价格信息 (单位是分,需要除以100)
    if 'priceH5' in info:
        price_info = info['priceH5']
        highlight_price = price_info.get('highlightPrice')
        if highlight_price:
            result['price'] = float(highlight_price)

        # 销量信息
        sales_text = price_info.get('itemAnalysisDataText', '')
        sales_match = re.search(r'已售(\d+)', sales_text)
        if sales_match:
            result['sales'] = int(sales_match.group(1))

    # 价格信息(从bottomBarMainH5获取,单位也是分)
    if 'bottomBarMainH5' in info:
        bottom_bar = info['bottomBarMainH5']
        price = bottom_bar.get('price')
        if price:
            result['price'] = float(price) / 100

    # 卖家信息
    if 'sellerH5' in info:
        seller = info['sellerH5']
        result['seller_name'] = seller.get('name')
        result['seller_id'] = seller.get('id')
        result['seller_logo'] = seller.get('logo')
        result['seller_fans'] = seller.get('fansAmount')
        result['seller_sales'] = seller.get('salesVolume')

    # 商品图片
    if 'carouselH5' in info:
        carousel = info['carouselH5']
        images = carousel.get('images', [])
        result['images'] = [img.get('url') for img in images if img.get('url')]
        if result['images']:
            result['cover_url'] = 'https:' + result['images'][0] if result['images'][0].startswith('//') else result['images'][0]

    # 商品描述
    if 'graphicDetailsV4' in info:
        graphic = info['graphicDetailsV4']
        result['description'] = graphic.get('description')

    # 物流信息
    if 'goodsDistributeV4' in info:
        distribute = info['goodsDistributeV4']
        result['location'] = distribute.get('location')
        result['shipping_fee'] = distribute.get('fee')

    return result


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


def submit_result(task, product_data):
    """提交真实的商品数据"""
    task_id = task["id"]

    # 提取任务数据(兼容Strapi 5)
    if "attributes" in task:
        task_data = task["attributes"]
    else:
        task_data = task

    # 构建商品数据
    product_payload = {
        "externalId": product_data.get('item_id') or task_data.get('url'),
        "title": product_data.get('title') or 'Unknown Product',
        "price": product_data.get('price') or 0,
        "sales": product_data.get('sales') or 0,
        "coverUrl": product_data.get('cover_url'),
        "metadata": {
            "description": product_data.get('description'),
            "images": product_data.get('images', []),
            "location": product_data.get('location'),
            "shipping_fee": product_data.get('shipping_fee'),
            "crawled_at": time.time(),
        }
    }

    # 店铺数据
    if product_data.get('seller_id'):
        product_payload["store"] = {
            "externalId": product_data['seller_id'],
            "name": product_data.get('seller_name') or 'Unknown Store',
            "logoUrl": product_data.get('seller_logo'),
            "metadata": {
                "fans": product_data.get('seller_fans'),
                "sales_volume": product_data.get('seller_sales'),
            }
        }

    # 提交完成状态
    response = requests.post(
        f"{BASE_URL}/crawl-tasks/{task_id}/actions/complete",
        json={
            "state": "done",
            "product": product_payload,
            "result": {"raw": product_data},
        },
        timeout=10,
    )
    response.raise_for_status()
    print(f"[OK] Task #{task_id} completed - {product_data.get('title')}")
    print(f"     Price: {product_data.get('price')} | Sales: {product_data.get('sales')}")


def run_once():
    """运行一次采集轮询"""
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
            task_url = task["attributes"].get("url")
            task_title = task["attributes"].get("title", "Untitled")
        else:
            task_url = task.get("url")
            task_title = task.get("title", "Untitled")

        print(f"\n[PROCESS] Task #{task_id} - {task_title}")
        print(f"[URL] {task_url}")

        # 提取item_id
        item_id = extract_item_id(task_url)
        if not item_id:
            print(f"[ERROR] Cannot extract item_id from URL: {task_url}")
            continue

        print(f"[CRAWL] Fetching product data for item_id: {item_id}")

        # 获取真实商品数据
        api_data = fetch_product_data(item_id)
        if not api_data:
            print(f"[ERROR] Failed to fetch product data")
            # 可以选择标记任务为failed
            continue

        # 解析商品数据
        product_data = parse_product_data(api_data)
        if not product_data:
            print(f"[ERROR] Failed to parse product data")
            continue

        print(f"[PARSED] Title: {product_data.get('title')}")
        print(f"[PARSED] Price: {product_data.get('price')} yuan")
        print(f"[PARSED] Sales: {product_data.get('sales')}")
        print(f"[PARSED] Seller: {product_data.get('seller_name')}")

        # 提交结果
        try:
            submit_result(task, product_data)
        except Exception as e:
            print(f"[ERROR] Failed to submit result: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Real XHS Product Crawler Worker")
    print(f"[CONFIG] Worker ID: {WORKER_ID}")
    print(f"[CONFIG] API URL: {BASE_URL}")
    print(f"[CONFIG] Claim limit: {CLAIM_LIMIT}")
    print("=" * 60)

    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"[WARN] Worker error: {exc}")
            import traceback
            traceback.print_exc()
            time.sleep(10)
