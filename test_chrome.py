# -*- coding: utf-8 -*-
import sys
import traceback

try:
    print("Testing Chrome WebDriver...")

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options

    print("Setting up Chrome options...")
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--headless")  # 添加无头模式测试

    print("Downloading Chrome driver...")
    driver_path = ChromeDriverManager().install()
    print(f"Driver path: {driver_path}")

    print("Starting Chrome browser...")
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    print("Testing basic navigation...")
    driver.get("https://www.baidu.com")
    print(f"Page title: {driver.title}")

    print("Closing browser...")
    driver.quit()

    print("Chrome WebDriver test completed successfully!")

except Exception as e:
    print(f"ERROR: {str(e)}")
    print("Detailed error information:")
    traceback.print_exc()