# -*- coding: utf-8 -*-
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
import requests
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from threading import Thread
from urllib.parse import urlparse
import sys
import zipfile
import platform
import tarfile
import sqlite3
from datetime import datetime
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import threading
import math

class SpiderGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小红书商品采集器")
        self.window.geometry("800x600")

        # 确保窗口在前台显示
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.after_idle(self.window.attributes, '-topmost', False)

        # 创建标签页控件
        self.tab_control = ttk.Notebook(self.window)

        # 采集标签页
        self.collect_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.collect_tab, text="商品采集")

        # 分析标签页
        self.analysis_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.analysis_tab, text="数据分析")

        # 将标签页控件放置到窗口
        self.tab_control.pack(fill=tk.BOTH, expand=True)

        # 设置采集标签页的内容
        self.setup_collect_tab()

        # 设置分析标签页的内容
        self.setup_analysis_tab()

        # 推迟创建爬虫实例，只在需要时创建
        self.spider = None
        self.log("程序启动成功！点击开始采集时将初始化浏览器。")

    def setup_collect_tab(self):
        """设置采集标签页的内容"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.collect_tab, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # URL输入区域
        url_frame = ttk.Frame(self.main_frame)
        url_frame.pack(fill=tk.BOTH, expand=True)

        # 创建标签变量
        self.url_label = ttk.Label(url_frame, text="请输入商品链接（每行一个）:")
        self.url_label.pack(anchor=tk.W)

        # 添加说明标签
        help_label = ttk.Label(url_frame, text="支持格式：\n1. 标准链接：https://www.xiaohongshu.com/goods-detail/xxx\n2. 分享链接：包含😆表情符号的完整分享文本\n3. 短链接：http://xhslink.com/xxx",
                              font=("Arial", 9), foreground="gray")
        help_label.pack(anchor=tk.W, pady=(0, 5))

        self.url_text = scrolledtext.ScrolledText(url_frame, height=10)
        self.url_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # 进度条区域
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)

        # 日志区域
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_label = ttk.Label(log_frame, text="操作日志:")
        log_label.pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # 控制按钮
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)

        # 复选框区域
        checkbox_frame = ttk.Frame(button_frame)
        checkbox_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.save_images_var = tk.BooleanVar()
        self.save_images_checkbox = ttk.Checkbutton(checkbox_frame, text="保存商品图片", variable=self.save_images_var)
        self.save_images_checkbox.pack(side=tk.LEFT)

        # 按钮区域
        buttons_frame = ttk.Frame(button_frame)
        buttons_frame.pack(side=tk.RIGHT)

        self.start_button = ttk.Button(buttons_frame, text="开始采集", command=self.start_collection)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.test_button = ttk.Button(buttons_frame, text="测试链接解析", command=self.test_url_parsing)
        self.test_button.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_button = ttk.Button(buttons_frame, text="清空日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT)

    def setup_analysis_tab(self):
        """设置分析标签页的内容"""
        # 创建主框架
        analysis_main_frame = ttk.Frame(self.analysis_tab, padding="10")
        analysis_main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建左右两个frame
        left_frame = ttk.Frame(analysis_main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_frame = ttk.Frame(analysis_main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 左侧 - 商品数据分析
        goods_frame = ttk.LabelFrame(left_frame, text="商品数据分析", padding="10")
        goods_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        goods_buttons_frame = ttk.Frame(goods_frame)
        goods_buttons_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(goods_buttons_frame, text="分析商品数据", command=self.analyze_goods_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(goods_buttons_frame, text="导出商品分析", command=self.export_goods_analysis).pack(side=tk.LEFT)

        # 商品分析结果表格
        self.goods_tree = ttk.Treeview(goods_frame, columns=('title', 'seller', 'count', 'avg_sales', 'total_sales'), show='headings', height=8)
        self.goods_tree.heading('#1', text='商品标题')
        self.goods_tree.heading('#2', text='店铺名称')
        self.goods_tree.heading('#3', text='采集次数')
        self.goods_tree.heading('#4', text='日均销量')
        self.goods_tree.heading('#5', text='总销量变化')

        # 设置列宽
        self.goods_tree.column('#1', width=200, minwidth=150)
        self.goods_tree.column('#2', width=150, minwidth=100)
        self.goods_tree.column('#3', width=80, minwidth=60)
        self.goods_tree.column('#4', width=80, minwidth=60)
        self.goods_tree.column('#5', width=100, minwidth=80)

        self.goods_tree.pack(fill=tk.BOTH, expand=True)

        # 右侧 - 店铺数据分析
        shop_frame = ttk.LabelFrame(right_frame, text="店铺数据分析", padding="10")
        shop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        shop_buttons_frame = ttk.Frame(shop_frame)
        shop_buttons_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(shop_buttons_frame, text="分析店铺数据", command=self.analyze_shop_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(shop_buttons_frame, text="导出店铺分析", command=self.export_shop_analysis).pack(side=tk.LEFT)

        # 店铺分析结果表格
        self.shop_tree = ttk.Treeview(shop_frame, columns=('seller', 'count', 'avg_daily', 'total_change'), show='headings', height=8)
        self.shop_tree.heading('#1', text='店铺名称')
        self.shop_tree.heading('#2', text='采集次数')
        self.shop_tree.heading('#3', text='日均出单')
        self.shop_tree.heading('#4', text='总销量变化')

        # 设置列宽
        self.shop_tree.column('#1', width=150, minwidth=100)
        self.shop_tree.column('#2', width=80, minwidth=60)
        self.shop_tree.column('#3', width=80, minwidth=60)
        self.shop_tree.column('#4', width=100, minwidth=80)

        self.shop_tree.pack(fill=tk.BOTH, expand=True)

        # 底部 - 数据管理
        management_frame = ttk.LabelFrame(analysis_main_frame, text="数据管理", padding="10")
        management_frame.pack(fill=tk.X, pady=(10, 0))

        management_buttons_frame = ttk.Frame(management_frame)
        management_buttons_frame.pack(fill=tk.X)

        ttk.Button(management_buttons_frame, text="导入数据(目录)", command=self.import_excel_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(management_buttons_frame, text="导入数据(文件)", command=self.import_single_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(management_buttons_frame, text="清空数据库", command=self.clear_database).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(management_buttons_frame, text="查看数据库", command=self.view_database).pack(side=tk.LEFT)

    def init_spider(self):
        """延迟初始化爬虫实例"""
        if self.spider is None:
            try:
                self.log("正在初始化浏览器，请稍候...")
                self.spider = XHSSpider(self)
                self.log("浏览器初始化成功！")
                return True
            except Exception as e:
                self.log(f"浏览器启动失败: {str(e)}")
                self.log("请确保Chrome浏览器已正确安装")
                return False
        return True

    def start_collection(self):
        """开始采集"""
        # 首先尝试初始化爬虫
        if not self.init_spider():
            return

        urls = self.url_text.get("1.0", tk.END).strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]

        if not urls:
            messagebox.showwarning("警告", "请输入商品链接")
            return

        # 禁用开始按钮
        self.start_button.config(state='disabled')
        self.clear_log()

        # 在新线程中运行采集
        thread = Thread(target=self.run_spider, args=(urls,))
        thread.daemon = True
        thread.start()

    def test_url_parsing(self):
        """测试链接解析功能"""
        self.clear_log()
        self.log("=== 开始测试链接解析功能 ===")

        # 测试用的各种链接格式
        test_urls = [
            "https://www.xiaohongshu.com/goods-detail/5fvEArEuMPs",
            "【小红书】冀教版8上英语讲义测试 😆 5fvEArEuMPs 😆 http://xhslink.com/m/8sRGr0QfpQO 点击链接或者复制本条信息打开【小红书app】查看 MF8056",
            "http://xhslink.com/m/8sRGr0QfpQO"
        ]

        for i, url in enumerate(test_urls, 1):
            self.log(f"\n测试 {i}: {url[:50]}{'...' if len(url) > 50 else ''}")

            # 这里只是测试URL清理，不需要初始化浏览器
            try:
                # 临时创建一个简单的URL清理器
                cleaned_url = self.clean_test_url(url)
                self.log(f"清理后: {cleaned_url}")
            except Exception as e:
                self.log(f"清理失败: {str(e)}")

        self.log("\n=== 链接解析测试完成 ===")

    def clean_test_url(self, url):
        """测试用的URL清理函数"""
        try:
            # 处理新的小红书分享链接格式
            if '😆' in url and 'xhslink.com' in url:
                # 提取短链接部分，直接使用短链接
                short_link_match = re.search(r'https?://xhslink\.com/[^\s]+', url)
                if short_link_match:
                    short_link = short_link_match.group(0)
                    return short_link

            # 处理标准的小红书商品链接
            match = re.search(r'goods-detail/([a-zA-Z0-9]+)', url)
            if match:
                product_id = match.group(1)
                return f'https://www.xiaohongshu.com/goods-detail/{product_id}'

            # 处理单独的短链接
            if 'xhslink.com' in url:
                short_link_match = re.search(r'https?://xhslink\.com/[^\s]+', url)
                if short_link_match:
                    return short_link_match.group(0)

            # 如果URL看起来是有效的HTTP/HTTPS链接，直接返回
            if url.startswith(('http://', 'https://')):
                return url

            return None

        except Exception as e:
            raise Exception(f"URL清理失败: {str(e)}")

    def run_spider(self, urls):
        """在新线程中运行爬虫"""
        try:
            self.spider.run(urls)
            self.log("采集完成！")
        finally:
            # 重新启用开始按钮
            self.start_button.config(state='normal')

    def log(self, message):
        """添加日志"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.window.update()

    def clear_log(self):
        """清空日志"""
        if hasattr(self, 'log_text'):
            self.log_text.delete("1.0", tk.END)

    def analyze_goods_data(self):
        """分析商品数据的占位方法"""
        self.log("商品数据分析功能待实现...")

    def export_goods_analysis(self):
        """导出商品分析的占位方法"""
        self.log("商品分析导出功能待实现...")

    def analyze_shop_data(self):
        """分析店铺数据的占位方法"""
        self.log("店铺数据分析功能待实现...")

    def export_shop_analysis(self):
        """导出店铺分析的占位方法"""
        self.log("店铺分析导出功能待实现...")

    def import_excel_data(self):
        """导入Excel数据的占位方法"""
        self.log("Excel数据导入功能待实现...")

    def import_single_file(self):
        """导入单个文件的占位方法"""
        self.log("单文件导入功能待实现...")

    def clear_database(self):
        """清空数据库的占位方法"""
        self.log("数据库清空功能待实现...")

    def view_database(self):
        """查看数据库的占位方法"""
        self.log("数据库查看功能待实现...")

    def run(self):
        """运行GUI"""
        self.window.mainloop()

# 简化版的XHSSpider类，用于测试
class XHSSpider:
    def __init__(self, gui):
        self.gui = gui
        self.driver = None

        # 获取当前脚本所在目录
        try:
            if getattr(sys, 'frozen', False):
                self.base_dir = os.path.dirname(sys.executable)
            else:
                self.base_dir = os.path.dirname(os.path.abspath(__file__))
        except:
            self.base_dir = os.getcwd()

        # 创建数据保存目录
        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)

        self.gui.log("正在配置Chrome浏览器...")
        self.init_browser()

    def init_browser(self):
        """初始化浏览器"""
        try:
            # 设置Chrome选项
            options = Options()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")

            self.gui.log("正在下载Chrome驱动...")
            driver_path = ChromeDriverManager().install()
            driver_path = driver_path.replace('/', '\\')
            self.gui.log(f"使用驱动: {driver_path}")

            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)

            self.gui.log("Chrome浏览器配置完成！")

        except Exception as e:
            self.gui.log(f"浏览器初始化失败: {str(e)}")
            raise

    def run(self, urls):
        """运行采集"""
        try:
            self.gui.log(f"开始采集 {len(urls)} 个链接...")

            for i, url in enumerate(urls, 1):
                self.gui.log(f"[{i}/{len(urls)}] 处理: {url[:50]}...")

                # 更新进度条
                progress = (i / len(urls)) * 100
                self.gui.progress_var.set(progress)
                self.gui.window.update()

                # 模拟处理时间
                time.sleep(1)

            self.gui.log("所有链接处理完成！")

        except Exception as e:
            self.gui.log(f"采集过程中出错: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                self.gui.log("浏览器已关闭")

if __name__ == '__main__':
    try:
        gui = SpiderGUI()
        gui.run()
    except Exception as e:
        print(f"程序启动错误: {str(e)}")
        import traceback
        traceback.print_exc()