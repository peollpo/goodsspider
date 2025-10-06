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

class Database:
    def __init__(self, db_path):
        """初始化数据库连接并创建必要的表结构"""
        try:
            # 添加 check_same_thread=False 参数以允许在不同线程中使用
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            # 添加锁来保护数据库操作
            self.lock = threading.Lock()
            self.cursor = self.conn.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            print(f"数据库错误: {e}")
            raise

    def create_tables(self):
        """创建数据库表"""
        with self.lock:
            # 商品表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goods (
                product_id TEXT PRIMARY KEY,
                title TEXT,
                seller_name TEXT,
                price TEXT,
                collect_time TEXT,
                count INTEGER DEFAULT 1
            )
            ''')

            # 检查goods表是否有count列，如果没有则添加
            try:
                self.cursor.execute("SELECT count FROM goods LIMIT 1")
            except sqlite3.OperationalError:
                # count列不存在，添加它
                self.cursor.execute('''
                ALTER TABLE goods ADD COLUMN count INTEGER DEFAULT 1
                ''')
                self.conn.commit()

            # 账号表 - 修改seller_name为主键
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS account (
                seller_name TEXT PRIMARY KEY,
                account_url TEXT,
                total_sales TEXT,
                collect_time TEXT
            )
            ''')

            # 采集数据表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS collect_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                sales TEXT,
                collect_time TEXT,
                FOREIGN KEY (product_id) REFERENCES goods (product_id)
            )
            ''')

            # 新增店铺采集数据表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS collect_account_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_name TEXT,
                total_sales TEXT,
                collect_time TEXT,
                FOREIGN KEY (seller_name) REFERENCES account (seller_name)
            )
            ''')

            self.conn.commit()

    def insert_goods(self, product_id, title, seller_name, price, collect_time):
        """插入商品信息，只在product_id不存在时才插入，同时更新count列"""
        try:
            with self.lock:
                # 首先检查product_id是否已存在
                self.cursor.execute('''
                SELECT COUNT(*), count FROM goods WHERE product_id = ?
                ''', (product_id,))

                result = self.cursor.fetchone()
                exists = result[0] > 0

                if not exists:
                    # 如果不存在，则插入新记录，count=1
                    self.cursor.execute('''
                    INSERT INTO goods (product_id, title, seller_name, price, collect_time, count)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ''', (product_id, title, seller_name, price, collect_time))
                    self.conn.commit()
                    return True, "inserted"
                else:
                    # 已存在，只更新count列 (+1)
                    current_count = result[1] if result[1] is not None else 0
                    new_count = current_count + 1

                    self.cursor.execute('''
                    UPDATE goods SET count = ? WHERE product_id = ?
                    ''', (new_count, product_id))
                    self.conn.commit()
                    return True, "count_updated"

        except sqlite3.Error as e:
            print(f"插入商品数据错误: {e}")
            return False, str(e)

    def insert_account(self, seller_name, account_url, total_sales, collect_time):
        """插入或更新账号信息"""
        try:
            with self.lock:
                self.cursor.execute('''
                INSERT OR REPLACE INTO account (seller_name, account_url, total_sales, collect_time)
                VALUES (?, ?, ?, ?)
                ''', (seller_name, account_url, total_sales, collect_time))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"插入账号数据错误: {e}")
            return False

    def insert_collect_account_data(self, seller_name, total_sales, collect_time):
        """插入店铺采集数据"""
        try:
            with self.lock:
                self.cursor.execute('''
                INSERT INTO collect_account_data (seller_name, total_sales, collect_time)
                VALUES (?, ?, ?)
                ''', (seller_name, total_sales, collect_time))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"插入店铺采集数据错误: {e}")
            return False

    def insert_collect_data(self, product_id, sales, collect_time):
        """插入采集数据"""
        try:
            with self.lock:
                self.cursor.execute('''
                INSERT INTO collect_data (product_id, sales, collect_time)
                VALUES (?, ?, ?)
                ''', (product_id, sales, collect_time))
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"插入采集数据错误: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            with self.lock:
                self.conn.close()

    def clear_all_data(self):
        """清空数据库中的所有表数据"""
        try:
            with self.lock:
                # 清空所有表
                self.cursor.execute("DELETE FROM collect_data")
                self.cursor.execute("DELETE FROM collect_account_data")
                self.cursor.execute("DELETE FROM goods")
                self.cursor.execute("DELETE FROM account")

                # 重置自增ID
                self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='collect_data'")
                self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='collect_account_data'")

                self.conn.commit()
                return True, "数据库已成功清空"
        except sqlite3.Error as e:
            print(f"清空数据库错误: {e}")
            return False, str(e)

    def get_all_data(self):
        """获取所有数据"""
        try:
            with self.lock:
                # 获取商品数据
                self.cursor.execute("SELECT COUNT(*) FROM goods")
                goods_count = self.cursor.fetchone()[0]

                # 获取采集数据
                self.cursor.execute("SELECT COUNT(*) FROM collect_data")
                collect_count = self.cursor.fetchone()[0]

                # 获取店铺数据
                self.cursor.execute("SELECT COUNT(*) FROM account")
                account_count = self.cursor.fetchone()[0]

                # 获取店铺采集数据
                self.cursor.execute("SELECT COUNT(*) FROM collect_account_data")
                account_collect_count = self.cursor.fetchone()[0]

                return {
                    'goods_count': goods_count,
                    'collect_count': collect_count,
                    'account_count': account_count,
                    'account_collect_count': account_collect_count
                }
        except sqlite3.Error as e:
            print(f"获取数据统计错误: {e}")
            return None

class SpiderGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小红书商品采集器")
        self.window.geometry("1000x700")

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
        # 初始化数据库
        self.init_database()
        self.log("程序启动成功！点击开始采集时将初始化浏览器。")

    def init_database(self):
        """初始化数据库"""
        try:
            # 获取当前脚本所在目录
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            # 创建数据保存目录
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # 初始化数据库
            db_path = os.path.join(data_dir, 'xiaohongshu.db')
            self.db = Database(db_path)
        except Exception as e:
            self.log(f"数据库初始化失败: {str(e)}")

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
        # 创建分析页面的主框架
        analysis_frame = ttk.Frame(self.analysis_tab, padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True)

        # 创建标签页控件用于商品分析和店铺分析
        self.analysis_notebook = ttk.Notebook(analysis_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True)

        # 商品分析标签页
        self.product_analysis_frame = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.product_analysis_frame, text="商品数据分析")

        # 店铺分析标签页
        self.shop_analysis_frame = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.shop_analysis_frame, text="店铺数据分析")

        # 数据管理标签页
        self.management_frame = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.management_frame, text="数据管理")

        # 设置各个页面
        self.setup_product_analysis()
        self.setup_shop_analysis()
        self.setup_data_management()

    def setup_product_analysis(self):
        """设置商品分析页面的内容"""
        # 控制区域
        control_frame = ttk.Frame(self.product_analysis_frame)
        control_frame.pack(fill=tk.X, pady=5)

        # 添加分析按钮
        self.analyze_button = ttk.Button(
            control_frame,
            text="分析商品数据",
            command=self.analyze_products
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        # 导出分析结果按钮
        self.export_button = ttk.Button(
            control_frame,
            text="导出分析结果",
            command=self.export_analysis
        )
        self.export_button.pack(side=tk.LEFT, padx=5)

        # 分析结果显示区域
        result_frame = ttk.Frame(self.product_analysis_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建带滚动条的Treeview
        tree_frame = ttk.Frame(result_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 创建垂直滚动条
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建水平滚动条
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )

        # 设置列
        self.tree["columns"] = (
            "product_id", "title", "seller_name", "price",
            "earliest_sales", "latest_sales", "earliest_time", "latest_time",
            "diff", "avg_daily", "count"
        )

        # 配置列宽和对齐方式
        self.tree.column("#0", width=0, stretch=tk.NO)  # 隐藏第一列
        self.tree.column("product_id", width=100, anchor=tk.W)
        self.tree.column("title", width=200, anchor=tk.W)
        self.tree.column("seller_name", width=120, anchor=tk.W)
        self.tree.column("price", width=80, anchor=tk.E)
        self.tree.column("earliest_sales", width=100, anchor=tk.E)
        self.tree.column("latest_sales", width=100, anchor=tk.E)
        self.tree.column("earliest_time", width=150, anchor=tk.W)
        self.tree.column("latest_time", width=150, anchor=tk.W)
        self.tree.column("diff", width=80, anchor=tk.E)
        self.tree.column("avg_daily", width=80, anchor=tk.E)
        self.tree.column("count", width=60, anchor=tk.E)

        # 设置列标题
        self.tree.heading("product_id", text="商品ID")
        self.tree.heading("title", text="标题")
        self.tree.heading("seller_name", text="店铺名称")
        self.tree.heading("price", text="价格")
        self.tree.heading("earliest_sales", text="第一次采集销量")
        self.tree.heading("latest_sales", text="最后采集销量")
        self.tree.heading("earliest_time", text="第一次采集时间")
        self.tree.heading("latest_time", text="最后采集时间")
        self.tree.heading("diff", text="销量差值")
        self.tree.heading("avg_daily", text="日均销量")
        self.tree.heading("count", text="采集次数")

        # 放置Treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 配置滚动条
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # 状态标签
        self.analysis_status = ttk.Label(self.product_analysis_frame, text="")
        self.analysis_status.pack(anchor=tk.W, pady=5)

    def setup_shop_analysis(self):
        """设置店铺分析页面的内容"""
        # 控制区域
        shop_control_frame = ttk.Frame(self.shop_analysis_frame)
        shop_control_frame.pack(fill=tk.X, pady=5)

        # 添加店铺分析按钮
        self.analyze_shop_button = ttk.Button(
            shop_control_frame,
            text="分析店铺数据",
            command=self.analyze_shops
        )
        self.analyze_shop_button.pack(side=tk.LEFT, padx=5)

        # 导出店铺分析结果按钮
        self.export_shop_button = ttk.Button(
            shop_control_frame,
            text="导出店铺分析结果",
            command=self.export_shop_analysis
        )
        self.export_shop_button.pack(side=tk.LEFT, padx=5)

        # 店铺分析结果显示区域
        shop_result_frame = ttk.Frame(self.shop_analysis_frame)
        shop_result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建带滚动条的Treeview
        shop_tree_frame = ttk.Frame(shop_result_frame)
        shop_tree_frame.pack(fill=tk.BOTH, expand=True)

        # 创建垂直滚动条
        shop_tree_scroll_y = ttk.Scrollbar(shop_tree_frame)
        shop_tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建水平滚动条
        shop_tree_scroll_x = ttk.Scrollbar(shop_tree_frame, orient=tk.HORIZONTAL)
        shop_tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建店铺分析Treeview
        self.shop_tree = ttk.Treeview(
            shop_tree_frame,
            yscrollcommand=shop_tree_scroll_y.set,
            xscrollcommand=shop_tree_scroll_x.set
        )

        # 设置店铺分析的列
        self.shop_tree["columns"] = (
            "seller_name", "old_collect_time", "new_collect_time",
            "earliest_sales", "latest_sales", "sales_diff", "avg_daily"
        )

        # 配置列宽和对齐方式
        self.shop_tree.column("#0", width=0, stretch=tk.NO)  # 隐藏第一列
        self.shop_tree.column("seller_name", width=150, anchor=tk.W)
        self.shop_tree.column("old_collect_time", width=150, anchor=tk.W)
        self.shop_tree.column("new_collect_time", width=150, anchor=tk.W)
        self.shop_tree.column("earliest_sales", width=100, anchor=tk.E)
        self.shop_tree.column("latest_sales", width=100, anchor=tk.E)
        self.shop_tree.column("sales_diff", width=100, anchor=tk.E)
        self.shop_tree.column("avg_daily", width=100, anchor=tk.E)

        # 设置店铺分析的列标题
        self.shop_tree.heading("seller_name", text="店铺名称")
        self.shop_tree.heading("old_collect_time", text="最早采集时间")
        self.shop_tree.heading("new_collect_time", text="最晚采集时间")
        self.shop_tree.heading("earliest_sales", text="最早总销量")
        self.shop_tree.heading("latest_sales", text="最晚总销量")
        self.shop_tree.heading("sales_diff", text="销量差值")
        self.shop_tree.heading("avg_daily", text="日均出单量")

        # 放置店铺Treeview
        self.shop_tree.pack(fill=tk.BOTH, expand=True)

        # 配置滚动条
        shop_tree_scroll_y.config(command=self.shop_tree.yview)
        shop_tree_scroll_x.config(command=self.shop_tree.xview)

        # 店铺分析状态标签
        self.shop_analysis_status = ttk.Label(self.shop_analysis_frame, text="")
        self.shop_analysis_status.pack(anchor=tk.W, pady=5)

    def setup_data_management(self):
        """设置数据管理页面的内容"""
        # 数据导入区域
        import_frame = ttk.LabelFrame(self.management_frame, text="数据导入", padding="10")
        import_frame.pack(fill=tk.X, pady=(10, 5))

        import_buttons_frame = ttk.Frame(import_frame)
        import_buttons_frame.pack(fill=tk.X)

        self.import_button = ttk.Button(import_buttons_frame, text="导入数据(目录)", command=self.import_excel_data)
        self.import_button.pack(side=tk.LEFT, padx=(0, 5))

        self.import_file_button = ttk.Button(import_buttons_frame, text="导入数据(文件)", command=self.import_single_file)
        self.import_file_button.pack(side=tk.LEFT, padx=(0, 5))

        # 数据库管理区域
        db_frame = ttk.LabelFrame(self.management_frame, text="数据库管理", padding="10")
        db_frame.pack(fill=tk.X, pady=5)

        db_buttons_frame = ttk.Frame(db_frame)
        db_buttons_frame.pack(fill=tk.X)

        self.view_db_button = ttk.Button(db_buttons_frame, text="查看数据库", command=self.view_database)
        self.view_db_button.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_db_button = ttk.Button(db_buttons_frame, text="清空数据库", command=self.clear_database)
        self.clear_db_button.pack(side=tk.LEFT, padx=(0, 5))

        # 数据库状态显示
        self.db_status_frame = ttk.Frame(self.management_frame)
        self.db_status_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.db_status_text = scrolledtext.ScrolledText(self.db_status_frame, height=15)
        self.db_status_text.pack(fill=tk.BOTH, expand=True)

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

    def analyze_products(self):
        """分析商品数据"""
        try:
            # 禁用按钮避免重复操作
            self.analyze_button.config(state='disabled')

            # 清空现有数据
            for i in self.tree.get_children():
                self.tree.delete(i)

            self.analysis_status.config(text="正在分析商品数据...")

            # 在新线程中进行分析，避免阻塞UI
            Thread(target=self.run_analysis, daemon=True).start()

        except Exception as e:
            self.analysis_status.config(text=f"分析出错: {str(e)}")
            self.analyze_button.config(state='normal')

    def run_analysis(self):
        """在后台线程中运行分析"""
        try:
            # 从数据库获取分析所需的数据
            with self.db.lock:
                # 获取所有商品信息
                self.db.cursor.execute('''
                SELECT product_id, title, seller_name, price, count FROM goods
                ''')
                products = self.db.cursor.fetchall()

                if not products:
                    self.analysis_status.config(text="没有找到商品数据")
                    self.analyze_button.config(state='normal')
                    return

                total_products = len(products)
                self.analysis_status.config(text=f"找到 {total_products} 个商品，正在分析...")

                # 用于存储分析结果
                results = []

                # 遍历每个商品
                for idx, (product_id, title, seller_name, price, count) in enumerate(products):
                    # 获取该商品最早和最晚的销量记录
                    self.db.cursor.execute('''
                    SELECT sales, collect_time FROM collect_data
                    WHERE product_id = ?
                    ORDER BY collect_time ASC
                    ''', (product_id,))
                    sales_records = self.db.cursor.fetchall()

                    if len(sales_records) < 1:
                        # 至少需要一条记录
                        continue

                    # 获取最早和最晚的记录
                    earliest_sales, earliest_time = sales_records[0]
                    if len(sales_records) > 1:
                        latest_sales, latest_time = sales_records[-1]
                    else:
                        latest_sales, latest_time = earliest_sales, earliest_time

                    # 计算差值
                    try:
                        sales_diff = int(latest_sales) - int(earliest_sales)
                    except:
                        sales_diff = 0

                    # 计算天数差和日均销量
                    try:
                        earliest_datetime = datetime.strptime(earliest_time, '%Y-%m-%d %H:%M:%S')
                        latest_datetime = datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                        days_diff = (latest_datetime - earliest_datetime).total_seconds() / (24 * 3600)

                        if days_diff > 0:
                            avg_daily = round(sales_diff / days_diff, 2)
                        else:
                            avg_daily = 0
                    except:
                        avg_daily = 0

                    # 添加到结果中
                    results.append({
                        'product_id': product_id,
                        'title': title,
                        'seller_name': seller_name,
                        'price': price,
                        'earliest_sales': earliest_sales,
                        'latest_sales': latest_sales,
                        'earliest_time': earliest_time,
                        'latest_time': latest_time,
                        'diff': sales_diff,
                        'avg_daily': avg_daily,
                        'count': count
                    })

                # 更新UI
                self.window.after(0, self.update_analysis_results, results)

        except Exception as e:
            self.analysis_status.config(text=f"分析出错: {str(e)}")
            self.analyze_button.config(state='normal')

    def update_analysis_results(self, results):
        """更新分析结果到UI"""
        try:
            # 清空现有数据
            for i in self.tree.get_children():
                self.tree.delete(i)

            if not results:
                self.analysis_status.config(text="没有足够的销量数据用于分析")
                self.analyze_button.config(state='normal')
                return

            # 添加数据到treeview
            for idx, item in enumerate(results):
                self.tree.insert(
                    parent="",
                    index="end",
                    iid=idx,
                    text="",
                    values=(
                        item['product_id'],
                        item['title'],
                        item['seller_name'],
                        item['price'],
                        item['earliest_sales'],
                        item['latest_sales'],
                        item['earliest_time'],
                        item['latest_time'],
                        item['diff'],
                        item['avg_daily'],
                        item['count']
                    )
                )

            self.analysis_status.config(text=f"分析完成，共 {len(results)} 个商品有效")

        except Exception as e:
            self.analysis_status.config(text=f"更新分析结果出错: {str(e)}")
        finally:
            self.analyze_button.config(state='normal')

    def export_analysis(self):
        """导出分析结果到Excel"""
        if not self.tree.get_children():
            messagebox.showwarning("警告", "没有可导出的分析结果")
            return

        # 从treeview中获取数据
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            data.append({
                'product_id': values[0],
                'title': values[1],
                'seller_name': values[2],
                'price': values[3],
                'earliest_sales': values[4],
                'latest_sales': values[5],
                'earliest_time': values[6],
                'latest_time': values[7],
                'diff': values[8],
                'avg_daily': values[9],
                'count': values[10]
            })

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 添加商品链接列
        df['商品链接'] = df['product_id'].apply(lambda x: f"https://www.xiaohongshu.com/goods-detail/{x}")

        # 重命名列
        df = df.rename(columns={
            'product_id': '商品ID',
            'title': '标题',
            'seller_name': '店铺名称',
            'price': '价格',
            'earliest_sales': '第一次采集销量',
            'latest_sales': '最后采集销量',
            'earliest_time': '第一次采集时间',
            'latest_time': '最后采集时间',
            'diff': '销量差值',
            'avg_daily': '日均销量',
            'count': '采集次数'
        })

        # 选择要导出的列
        columns = [
            '商品ID', '标题', '店铺名称', '价格', '商品链接',
            '第一次采集销量', '最后采集销量', '第一次采集时间', '最后采集时间',
            '销量差值', '日均销量', '采集次数'
        ]
        df = df[columns]

        # 保存到Excel
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            title="保存分析结果"
        )

        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", f"分析结果已导出到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def analyze_shops(self):
        """分析店铺数据"""
        try:
            # 禁用按钮避免重复操作
            self.analyze_shop_button.config(state='disabled')

            # 清空现有数据
            for i in self.shop_tree.get_children():
                self.shop_tree.delete(i)

            self.shop_analysis_status.config(text="正在分析店铺数据...")

            # 在新线程中进行分析，避免阻塞UI
            Thread(target=self.run_shop_analysis, daemon=True).start()

        except Exception as e:
            self.shop_analysis_status.config(text=f"分析出错: {str(e)}")
            self.analyze_shop_button.config(state='normal')

    def run_shop_analysis(self):
        """在后台线程中运行店铺分析"""
        try:
            # 从数据库获取分析所需的数据
            with self.db.lock:
                # 获取所有店铺信息
                self.db.cursor.execute('''
                SELECT seller_name FROM account
                ''')
                shops = self.db.cursor.fetchall()

                if not shops:
                    self.shop_analysis_status.config(text="没有找到店铺数据")
                    self.analyze_shop_button.config(state='normal')
                    return

                total_shops = len(shops)
                self.shop_analysis_status.config(text=f"找到 {total_shops} 个店铺，正在分析...")

                # 用于存储分析结果
                results = []

                # 遍历每个店铺
                for idx, (seller_name,) in enumerate(shops):
                    # 获取该店铺最早和最晚的销量记录
                    self.db.cursor.execute('''
                    SELECT total_sales, collect_time FROM collect_account_data
                    WHERE seller_name = ?
                    ORDER BY collect_time ASC
                    ''', (seller_name,))
                    sales_records = self.db.cursor.fetchall()

                    if len(sales_records) < 1:
                        continue

                    # 获取最早和最晚的记录
                    earliest_sales, earliest_time = sales_records[0]
                    if len(sales_records) > 1:
                        latest_sales, latest_time = sales_records[-1]
                    else:
                        latest_sales, latest_time = earliest_sales, earliest_time

                    # 计算差值
                    try:
                        sales_diff = int(latest_sales) - int(earliest_sales)
                    except:
                        sales_diff = 0

                    # 计算天数差和日均出单量
                    try:
                        earliest_datetime = datetime.strptime(earliest_time, '%Y-%m-%d %H:%M:%S')
                        latest_datetime = datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                        days_diff = (latest_datetime - earliest_datetime).total_seconds() / (24 * 3600)

                        if days_diff > 0:
                            avg_daily = round(sales_diff / days_diff, 2)
                        else:
                            avg_daily = 0
                    except:
                        avg_daily = 0

                    # 添加到结果中
                    results.append({
                        'seller_name': seller_name,
                        'old_collect_time': earliest_time,
                        'new_collect_time': latest_time,
                        'earliest_sales': earliest_sales,
                        'latest_sales': latest_sales,
                        'sales_diff': sales_diff,
                        'avg_daily': avg_daily
                    })

                # 更新UI
                self.window.after(0, self.update_shop_analysis_results, results)

        except Exception as e:
            self.shop_analysis_status.config(text=f"分析出错: {str(e)}")
            self.analyze_shop_button.config(state='normal')

    def update_shop_analysis_results(self, results):
        """更新店铺分析结果到UI"""
        try:
            # 清空现有数据
            for i in self.shop_tree.get_children():
                self.shop_tree.delete(i)

            if not results:
                self.shop_analysis_status.config(text="没有足够的店铺数据用于分析")
                self.analyze_shop_button.config(state='normal')
                return

            # 添加数据到treeview
            for idx, item in enumerate(results):
                self.shop_tree.insert(
                    parent="",
                    index="end",
                    iid=idx,
                    text="",
                    values=(
                        item['seller_name'],
                        item['old_collect_time'],
                        item['new_collect_time'],
                        item['earliest_sales'],
                        item['latest_sales'],
                        item['sales_diff'],
                        item['avg_daily']
                    )
                )

            self.shop_analysis_status.config(text=f"分析完成，共 {len(results)} 个店铺有效")

        except Exception as e:
            self.shop_analysis_status.config(text=f"更新分析结果出错: {str(e)}")
        finally:
            self.analyze_shop_button.config(state='normal')

    def export_shop_analysis(self):
        """导出店铺分析结果"""
        if not self.shop_tree.get_children():
            messagebox.showwarning("警告", "没有可导出的店铺分析结果")
            return

        # 从treeview中获取数据
        data = []
        for item in self.shop_tree.get_children():
            values = self.shop_tree.item(item)["values"]
            data.append({
                'seller_name': values[0],
                'old_collect_time': values[1],
                'new_collect_time': values[2],
                'earliest_sales': values[3],
                'latest_sales': values[4],
                'sales_diff': values[5],
                'avg_daily': values[6]
            })

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 重命名列
        df = df.rename(columns={
            'seller_name': '店铺名称',
            'old_collect_time': '最早采集时间',
            'new_collect_time': '最晚采集时间',
            'earliest_sales': '最早总销量',
            'latest_sales': '最晚总销量',
            'sales_diff': '销量差值',
            'avg_daily': '日均出单量'
        })

        # 保存到Excel
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            title="保存店铺分析结果"
        )

        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", f"店铺分析结果已导出到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def import_excel_data(self):
        """导入Excel数据"""
        folder_path = filedialog.askdirectory(title="选择包含Excel文件的文件夹")
        if folder_path:
            Thread(target=self.run_import, args=(folder_path,), daemon=True).start()

    def import_single_file(self):
        """导入单个Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("Excel文件", "*.xls")]
        )
        if file_path:
            Thread(target=self.run_import_single_file, args=(file_path,), daemon=True).start()

    def run_import(self, folder_path):
        """在后台线程中运行导入操作"""
        try:
            # 禁用按钮
            self.import_button.config(state='disabled')
            self.import_file_button.config(state='disabled')

            # 更新状态
            self.update_db_status("开始导入Excel文件...")

            # 查找所有Excel文件
            excel_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        excel_files.append(os.path.join(root, file))

            if not excel_files:
                self.update_db_status("未找到Excel文件")
                return

            self.update_db_status(f"找到 {len(excel_files)} 个Excel文件，开始导入...")

            # 处理每个文件
            for idx, file_path in enumerate(excel_files):
                self.update_db_status(f"正在处理 {idx+1}/{len(excel_files)}: {os.path.basename(file_path)}")
                self.import_excel_file(file_path)

            self.update_db_status("所有Excel文件导入完成!")

        except Exception as e:
            self.update_db_status(f"导入出错: {str(e)}")
        finally:
            # 重新启用按钮
            self.import_button.config(state='normal')
            self.import_file_button.config(state='normal')

    def run_import_single_file(self, file_path):
        """在后台线程中运行导入单个文件的操作"""
        try:
            # 禁用按钮
            self.import_button.config(state='disabled')
            self.import_file_button.config(state='disabled')

            self.update_db_status(f"开始导入文件: {os.path.basename(file_path)}")
            self.import_excel_file(file_path)
            self.update_db_status("文件导入完成!")

        except Exception as e:
            self.update_db_status(f"导入出错: {str(e)}")
        finally:
            # 重新启用按钮
            self.import_button.config(state='normal')
            self.import_file_button.config(state='normal')

    def import_excel_file(self, file_path):
        """导入单个Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)

            # 检查必要的列是否存在
            required_columns = ['商品ID', '标题', '店铺名称', '价格', '销量', '采集时间']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.update_db_status(f"文件 {os.path.basename(file_path)} 缺少必要列: {missing_columns}")
                return

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    product_id = str(row['商品ID'])
                    title = str(row['标题'])
                    seller_name = str(row['店铺名称'])
                    price = str(row['价格'])
                    sales = str(row['销量'])
                    collect_time = str(row['采集时间'])

                    # 插入或更新商品数据
                    self.db.insert_goods(product_id, title, seller_name, price, collect_time)

                    # 插入采集数据
                    self.db.insert_collect_data(product_id, sales, collect_time)

                except Exception as e:
                    self.update_db_status(f"处理第 {index+1} 行时出错: {str(e)}")
                    continue

            self.update_db_status(f"文件 {os.path.basename(file_path)} 导入完成")

        except Exception as e:
            self.update_db_status(f"读取文件 {os.path.basename(file_path)} 出错: {str(e)}")

    def clear_database(self):
        """清空数据库"""
        result = messagebox.askyesno("确认", "确定要清空数据库吗？此操作不可恢复！")
        if result:
            try:
                success, message = self.db.clear_all_data()
                if success:
                    self.update_db_status("数据库已清空")
                    messagebox.showinfo("成功", message)
                else:
                    self.update_db_status(f"清空数据库失败: {message}")
                    messagebox.showerror("错误", f"清空失败: {message}")
            except Exception as e:
                error_msg = f"清空数据库出错: {str(e)}"
                self.update_db_status(error_msg)
                messagebox.showerror("错误", error_msg)

    def view_database(self):
        """查看数据库统计信息"""
        try:
            data = self.db.get_all_data()
            if data:
                status_text = f"""数据库统计信息：
商品数量: {data['goods_count']} 条
商品采集记录: {data['collect_count']} 条
店铺数量: {data['account_count']} 条
店铺采集记录: {data['account_collect_count']} 条

更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                self.update_db_status(status_text)
            else:
                self.update_db_status("获取数据库信息失败")
        except Exception as e:
            self.update_db_status(f"查看数据库出错: {str(e)}")

    def update_db_status(self, message):
        """更新数据库状态显示"""
        if hasattr(self, 'db_status_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.db_status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.db_status_text.see(tk.END)
            self.window.update()

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

        # 使用GUI的数据库实例
        self.db = gui.db

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

                # 模拟处理时间和数据插入
                time.sleep(1)

                # 模拟数据采集并存储到数据库
                try:
                    product_id = f"test_{i}"
                    title = f"测试商品_{i}"
                    seller_name = f"测试店铺_{i}"
                    price = f"{i * 10}.00"
                    sales = str(i * 100)
                    collect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # 插入商品信息
                    self.db.insert_goods(product_id, title, seller_name, price, collect_time)
                    # 插入采集数据
                    self.db.insert_collect_data(product_id, sales, collect_time)

                    self.gui.log(f"已保存: {title}")

                except Exception as e:
                    self.gui.log(f"保存数据失败: {str(e)}")

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