# -*- coding: utf-8 -*-
"""升级版小红书商品采集Worker - 支持批量链接、短链接、历史记录"""
import os
import re
import time
import requests
import json
from datetime import datetime

BASE_URL = os.getenv("WEBSPIDER_API", "http://localhost:1337/api")
WORKER_ID = os.getenv("WEBSPIDER_WORKER_ID", "batch-crawler-worker")
CLAIM_LIMIT = int(os.getenv("WEBSPIDER_CLAIM_LIMIT", "1"))


def extract_urls_from_text(text):
    """从多行文本中提取所有链接

    支持格式:
    1. 完整链接: https://www.xiaohongshu.com/goods-detail/677deacf627fd90001933466?xsec_token=...
    2. 短链接: https://xhslink.com/m/4ZhKf0O6l4h
    3. 文本分享: 【小红书】标题 😆 短码 😆 https://xhslink.com/m/xxx ...
    """
    urls = []

    # 按行分割
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 提取所有URL
        # 匹配 https://www.xiaohongshu.com/goods-detail/... 或 https://xhslink.com/m/...
        url_patterns = [
            r'https://www\.xiaohongshu\.com/goods-detail/[a-zA-Z0-9\?&=\-_%]+',
            r'https://xhslink\.com/m/[a-zA-Z0-9]+'
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, line)
            urls.extend(matches)

    # 去重
    return list(set(urls))


def resolve_short_url(short_url):
    """重定向短链接获取真实item_id

    短链接如: https://xhslink.com/m/4ZhKf0O6l4h
    会重定向到: https://www.xiaohongshu.com/goods-detail/673071e618193500011e6dd0?...
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        response = requests.get(short_url, headers=headers, timeout=10, allow_redirects=True)

        # 从最终URL中提取item_id
        final_url = response.url
        print(f"[REDIRECT] {short_url} -> {final_url}")

        match = re.search(r'goods-detail/([a-zA-Z0-9]+)', final_url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"[ERROR] Failed to resolve short URL: {e}")
        return None


def extract_item_id(url):
    """从商品URL中提取item_id"""
    # 如果是短链接,先重定向
    if 'xhslink.com' in url:
        return resolve_short_url(url)

    # 完整链接直接提取
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


def save_product_history(product_data, product_url, task_id):
    """保存商品历史记录"""
    history_data = {
        "data": {
            "productId": product_data.get('item_id'),
            "title": product_data.get('title'),
            "sellerName": product_data.get('seller_name'),
            "totalSales": product_data.get('sales') or 0,
            "price": product_data.get('price') or 0,
            "sales": product_data.get('sales') or 0,
            "collectTime": datetime.now().isoformat(),
            "productUrl": product_url,
            "accountUrl": f"https://www.xiaohongshu.com/user/profile/{product_data.get('seller_id')}" if product_data.get('seller_id') else None,
            "crawlTask": task_id
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/product-histories",
            json=history_data,
            timeout=10
        )
        response.raise_for_status()
        print(f"[HISTORY] Saved product history for {product_data.get('item_id')}")
    except Exception as e:
        print(f"[WARN] Failed to save product history: {e}")


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


def submit_result(task, product_data, product_url):
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

    # 保存历史记录
    save_product_history(product_data, product_url, task_id)

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


def process_single_url(url, task):
    """处理单个URL"""
    print(f"\n[URL] Processing: {url}")

    # 提取item_id
    item_id = extract_item_id(url)
    if not item_id:
        print(f"[ERROR] Cannot extract item_id from URL: {url}")
        return False

    print(f"[CRAWL] Fetching product data for item_id: {item_id}")

    # 获取真实商品数据
    api_data = fetch_product_data(item_id)
    if not api_data:
        print(f"[ERROR] Failed to fetch product data")
        return False

    # 解析商品数据
    product_data = parse_product_data(api_data)
    if not product_data:
        print(f"[ERROR] Failed to parse product data")
        return False

    print(f"[PARSED] Title: {product_data.get('title')}")
    print(f"[PARSED] Price: {product_data.get('price')} yuan")
    print(f"[PARSED] Sales: {product_data.get('sales')}")
    print(f"[PARSED] Seller: {product_data.get('seller_name')}")

    # 提交结果
    try:
        submit_result(task, product_data, url)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to submit result: {e}")
        return False


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

        # 提取所有URL
        urls = extract_urls_from_text(task_url)
        if not urls:
            print(f"[ERROR] No valid URLs found in task")
            continue

        print(f"[BATCH] Found {len(urls)} URL(s) to process")

        # 处理每个URL
        success_count = 0
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] Processing URL...")
            if process_single_url(url, task):
                success_count += 1
            # 延迟避免API限制
            if idx < len(urls):
                time.sleep(2)

        print(f"\n[SUMMARY] Task #{task_id}: {success_count}/{len(urls)} URLs processed successfully")


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Batch XHS Product Crawler Worker")
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
