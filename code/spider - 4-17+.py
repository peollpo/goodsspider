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
        
        # 创建爬虫实例（在初始化时就创建）
        try:
            self.spider = XHSSpider(self)
        except Exception as e:
            self.log(f"浏览器启动失败: {str(e)}")
    
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
        
        ttk.Label(log_frame, text="运行日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 控制区域
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 添加保存图片复选框
        self.save_images_var = tk.BooleanVar(value=False)  # 默认不勾选
        self.save_images_check = ttk.Checkbutton(
            control_frame, 
            text="保存商品图片", 
            variable=self.save_images_var
        )
        self.save_images_check.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(control_frame, text="开始采集", command=self.start_spider)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 添加导入目录按钮
        self.import_button = ttk.Button(control_frame, text="导入数据", command=self.import_excel_data)
        self.import_button.pack(side=tk.LEFT, padx=5)
        
        # 添加清空数据库按钮
        self.clear_db_button = ttk.Button(control_frame, text="清空数据库", command=self.clear_database)
        self.clear_db_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 在选项区域添加自动关机复选框
        self.shutdown_var = tk.BooleanVar()
        self.shutdown_checkbox = ttk.Checkbutton(
            control_frame, 
            text="任务完成后自动关机", 
            variable=self.shutdown_var
        )
        self.shutdown_checkbox.pack(side=tk.LEFT, padx=5)
        
    def setup_analysis_tab(self):
        """设置分析标签页的内容"""
        # 创建分析页面的主框架
        analysis_frame = ttk.Frame(self.analysis_tab, padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制区域
        control_frame = ttk.Frame(analysis_frame)
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
        result_frame = ttk.Frame(analysis_frame)
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
        self.tree.heading("product_id", text="商品ID", command=lambda: self.sort_treeview("product_id", False))
        self.tree.heading("title", text="标题", command=lambda: self.sort_treeview("title", False))
        self.tree.heading("seller_name", text="店铺名称", command=lambda: self.sort_treeview("seller_name", False))
        self.tree.heading("price", text="价格", command=lambda: self.sort_treeview("price", True))
        self.tree.heading("earliest_sales", text="第一次采集销量", command=lambda: self.sort_treeview("earliest_sales", True))
        self.tree.heading("latest_sales", text="最后采集销量", command=lambda: self.sort_treeview("latest_sales", True))
        self.tree.heading("earliest_time", text="第一次采集时间", command=lambda: self.sort_treeview("earliest_time", False))
        self.tree.heading("latest_time", text="最后采集时间", command=lambda: self.sort_treeview("latest_time", False))
        self.tree.heading("diff", text="销量差值", command=lambda: self.sort_treeview("diff", True))
        self.tree.heading("avg_daily", text="日均销量", command=lambda: self.sort_treeview("avg_daily", True))
        self.tree.heading("count", text="采集次数", command=lambda: self.sort_treeview("count", True))
        
        # 用于记录排序状态
        self.sort_info = {
            "column": None,  # 当前排序的列
            "reverse": False  # 是否倒序
        }
        
        # 存储每行对应的URL，用于点击打开
        self.tree_item_urls = {}
        
        # 绑定行点击事件
        self.tree.bind("<Double-1>", self.on_tree_item_double_click)
        # 添加右键菜单
        self.tree.bind("<Button-3>", self.show_tree_item_context_menu)
        
        # 放置Treeview
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # 状态标签
        self.analysis_status = ttk.Label(analysis_frame, text="")
        self.analysis_status.pack(anchor=tk.W, pady=5)
        
    def sort_treeview(self, column, is_numeric=False):
        """排序Treeview的数据"""
        # 获取所有数据项
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # 判断是否需要切换排序方向
        reverse = False
        if self.sort_info["column"] == column:
            reverse = not self.sort_info["reverse"]
        
        # 更新排序状态
        self.sort_info["column"] = column
        self.sort_info["reverse"] = reverse
        
        # 排序
        if is_numeric:
            # 数值排序，考虑空值
            def convert_to_number(x):
                try:
                    return float(x[0]) if x[0] else 0
                except (ValueError, TypeError):
                    return 0
            items.sort(key=convert_to_number, reverse=reverse)
        else:
            # 字符串排序
            items.sort(reverse=reverse)
        
        # 更新排序箭头
        for col in self.tree["columns"]:
            if col == column:
                arrow = "▼" if reverse else "▲"
                text = self.tree.heading(col)["text"]
                # 移除可能已有的箭头
                if text.endswith(" ▲") or text.endswith(" ▼"):
                    text = text[:-2]
                self.tree.heading(col, text=f"{text} {arrow}")
            else:
                text = self.tree.heading(col)["text"]
                if text.endswith(" ▲") or text.endswith(" ▼"):
                    self.tree.heading(col, text=text[:-2])
        
        # 重新插入排序后的数据
        for index, (val, iid) in enumerate(items):
            self.tree.move(iid, '', index)
    
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
            with self.spider.db.lock:
                # 获取所有商品信息
                self.spider.db.cursor.execute('''
                SELECT product_id, title, seller_name, price, count FROM goods
                ''')
                products = self.spider.db.cursor.fetchall()
                
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
                    # 更新进度信息
                    progress = f"正在分析 {idx+1}/{total_products}: {title[:20]}..."
                    self.analysis_status.config(text=progress)
                    
                    # 获取该商品最早和最晚的销量记录
                    self.spider.db.cursor.execute('''
                    SELECT sales, collect_time FROM collect_data 
                    WHERE product_id = ? 
                    ORDER BY collect_time ASC
                    ''', (product_id,))
                    sales_records = self.spider.db.cursor.fetchall()
                    
                    if len(sales_records) < 2:
                        # 至少需要两条记录才能计算差值
                        continue
                    
                    # 获取最早和最晚的记录
                    earliest_sales, earliest_time = sales_records[0]
                    latest_sales, latest_time = sales_records[-1]
                    
                    # 解析时间
                    earliest_datetime = datetime.strptime(earliest_time, '%Y-%m-%d %H:%M:%S')
                    latest_datetime = datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                    
                    # 计算差值
                    sales_diff = int(latest_sales) - int(earliest_sales)
                    
                    # 计算天数差
                    days_diff = (latest_datetime - earliest_datetime).total_seconds() / (24 * 3600)
                    
                    # 避免除以零
                    if days_diff > 0:
                        avg_daily = round(sales_diff / days_diff)
                    else:
                        avg_daily = 0
                    
                    # 格式化时间为月-日格式
                    # 兼容Windows系统的日期格式化
                    if platform.system() == 'Windows':
                        earliest_formatted = earliest_datetime.strftime('%m-%d').lstrip('0').replace('-0', '-') + '-销量'
                        latest_formatted = latest_datetime.strftime('%m-%d').lstrip('0').replace('-0', '-') + '-销量'
                    else:
                        earliest_formatted = earliest_datetime.strftime('%-m-%-d-销量')
                        latest_formatted = latest_datetime.strftime('%-m-%-d-销量')
                    
                    # 获取product_url
                    product_url = ""
                    try:
                        # 尝试从数据库中获取URL
                        self.spider.db.cursor.execute('''
                        SELECT product_url FROM collect_data 
                        WHERE product_id = ? 
                        LIMIT 1
                        ''', (product_id,))
                        url_result = self.spider.db.cursor.fetchone()
                        
                        if url_result and url_result[0]:
                            product_url = url_result[0]
                        else:
                            # 如果在collect_data中没有找到，构造一个标准URL
                            product_url = f"https://www.xiaohongshu.com/goods-detail/{product_id}"
                    except:
                        # 失败时也构造一个标准URL
                        product_url = f"https://www.xiaohongshu.com/goods-detail/{product_id}"
                    
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
                        'earliest_formatted': earliest_formatted,
                        'latest_formatted': latest_formatted,
                        'product_url': product_url,
                        'count': count if count is not None else 1
                    })
                
                # 更新UI (在主线程中)
                self.window.after(0, self.update_analysis_results, results)
                
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)
            self.window.after(0, lambda: self.analysis_status.config(text=f"分析过程出错: {str(e)}"))
            self.window.after(0, lambda: self.analyze_button.config(state='normal'))
    
    def update_analysis_results(self, results):
        """更新分析结果到UI"""
        try:
            # 清空现有数据
            for i in self.tree.get_children():
                self.tree.delete(i)
                
            # 清空URL映射
            self.tree_item_urls = {}
                
            if not results:
                self.analysis_status.config(text="没有足够的销量数据用于分析")
                self.analyze_button.config(state='normal')
                return
            
            # 更新列标题为实际日期，同时保留排序功能
            earliest_date = results[0]['earliest_formatted']
            latest_date = results[0]['latest_formatted']
            
            self.tree.heading("earliest_sales", text=earliest_date, command=lambda: self.sort_treeview("earliest_sales", True))
            self.tree.heading("latest_sales", text=latest_date, command=lambda: self.sort_treeview("latest_sales", True))
            
            # 添加数据到treeview
            for idx, item in enumerate(results):
                tree_item = self.tree.insert(
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
                
                # 存储商品URL，用于点击行时打开
                if 'product_url' in item and item['product_url']:
                    self.tree_item_urls[tree_item] = item['product_url']
            
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
        df['商品链接'] = df['product_id'].apply(lambda x: f"https://item.taobao.com/item.htm?id={x}")
        
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
        
    def log(self, message):
        """添加日志到日志区域"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        
    def update_progress(self, current, total):
        """更新进度条"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.status_label.config(text=f"进度: {current}/{total}")
        
    def clean_url(self, url):
        """清理URL，提取商品ID并重构标准URL"""
        try:
            # 查找goods-detail/后面的ID
            match = re.search(r'goods-detail/([a-zA-Z0-9]+)', url)
            if match:
                product_id = match.group(1)
                # 返回标准格式URL
                return f'https://www.xiaohongshu.com/goods-detail/{product_id}'
            return url
        except:
            return url
        
    def start_spider(self):
        """开始爬虫"""
        urls = []
        for line in self.url_text.get('1.0', tk.END).splitlines():
            line = re.sub(r'^[^h]+', '', line.strip())
            if line and 'xiaohongshu.com' in line:
                clean_url = self.clean_url(line)
                if clean_url:
                    urls.append(clean_url)
        
        if not urls:
            self.log("请输入至少一个链接")
            return
        
        # 禁用开始按钮
        self.start_button.config(state='disabled')
        self.log(f"开始处理 {len(urls)} 个链接...")
        
        # 在新线程中运行爬虫
        Thread(target=self.run_spider, args=(urls,), daemon=True).start()
        
    def run_spider(self, urls):
        """在新线程中运行爬虫"""
        try:
            self.spider.run(urls)
            self.log("采集完成！")
            
            # 任务完成后检查是否需要关机
            if self.shutdown_var.get():
                self.log("任务完成，系统将在1分钟后关机...")
                # 使用系统命令执行关机，给用户1分钟的缓冲时间
                os.system("shutdown /s /t 60")
                
                # 添加取消关机的按钮
                cancel_btn = ttk.Button(
                    self.window,
                    text="取消关机",
                    command=lambda: os.system("shutdown /a")
                )
                cancel_btn.pack(pady=5)
            
        except Exception as e:
            self.log(f"发生错误: {str(e)}")
            # 如果发生错误，确保取消关机计划
            if self.shutdown_var.get():
                os.system("shutdown /a")
        finally:
            self.start_button.config(state='normal')
            
    def run(self):
        """运行GUI"""
        self.window.mainloop()
        
    def import_excel_data(self):
        """导入Excel表格数据到数据库"""
        try:
            import tkinter.filedialog as filedialog
            
            # 选择文件夹
            folder_path = filedialog.askdirectory(title="选择包含Excel表格的文件夹")
            if not folder_path:
                self.log("未选择文件夹，操作取消")
                return
                
            self.log(f"选择的文件夹: {folder_path}")
            
            # 确保爬虫实例已创建
            if not hasattr(self, 'spider') or self.spider is None:
                self.log("创建爬虫实例...")
                try:
                    self.spider = XHSSpider(self)
                except Exception as e:
                    self.log(f"爬虫实例创建失败: {str(e)}")
                    return
            
            # 在新线程中运行导入操作，避免阻塞UI
            Thread(target=self.run_import, args=(folder_path,), daemon=True).start()
            
        except Exception as e:
            self.log(f"导入数据操作失败: {str(e)}")
            
    def run_import(self, folder_path):
        """在后台线程中运行导入操作"""
        try:
            # 禁用按钮
            self.import_button.config(state='disabled')
            self.start_button.config(state='disabled')
            
            self.log("开始搜索Excel文件...")
            excel_files = []
            
            # 遍历文件夹及子文件夹查找Excel文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        excel_files.append(os.path.join(root, file))
            
            if not excel_files:
                self.log("未找到Excel文件")
                messagebox.showinfo("导入结果", f"在选定文件夹中未找到Excel文件。")
                return
                
            self.log(f"找到 {len(excel_files)} 个Excel文件")
            
            # 处理每个Excel文件
            total_imported = 0
            
            for i, file_path in enumerate(excel_files):
                self.log(f"正在处理文件 {i+1}/{len(excel_files)}: {os.path.basename(file_path)}")
                
                # 更新进度条
                self.update_progress(i+1, len(excel_files))
                
                # 导入单个文件
                imported_count = self.import_single_excel(file_path)
                total_imported += imported_count
                
                # 强制释放文件句柄
                try:
                    import gc
                    gc.collect()
                    # 在Windows系统上运行时，等待一小段时间让系统完全释放文件句柄
                    if platform.system() == 'Windows':
                        time.sleep(0.5)
                except:
                    pass
            
            self.log(f"导入完成！共导入 {total_imported} 条记录")
            
            # 导入完成后显示确认对话框
            if total_imported > 0:
                messagebox.showinfo("导入成功", f"成功导入 {total_imported} 条数据到数据库！")
            else:
                messagebox.showwarning("导入警告", "未能成功导入任何数据。请检查文件格式是否正确。")
            
        except Exception as e:
            self.log(f"导入过程出错: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("导入错误", f"导入过程中发生错误: {str(e)}")
        finally:
            # 启用按钮
            self.import_button.config(state='normal')
            self.start_button.config(state='normal')
            
    def import_single_excel(self, file_path):
        """导入单个Excel文件的数据"""
        excel_file = None
        try:
            # 读取Excel文件
            self.log(f"读取文件: {file_path}")
            
            # 获取Excel文件的所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            self.log(f"文件包含 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")
            
            # 尝试所有工作表
            total_imported = 0
            for sheet_name in sheet_names:
                self.log(f"正在处理工作表: {sheet_name}")
                
                # 读取当前工作表
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 打印工作表形状(行数和列数)
                self.log(f"工作表形状: {df.shape[0]} 行 x {df.shape[1]} 列")
                
                # 检查是否为空
                if df.empty:
                    self.log(f"工作表 '{sheet_name}' 为空，跳过")
                    continue
                
                # 检查并处理列名，确保列名格式正确
                columns = df.columns.tolist()
                self.log(f"列名: {', '.join([str(col) for col in columns])}")
                
                # 检查是否有unnamed列，这通常是Excel文件的空列
                unnamed_cols = [col for col in columns if 'Unnamed' in str(col)]
                if unnamed_cols:
                    self.log(f"检测到 {len(unnamed_cols)} 个未命名列，尝试清理...")
                    df = df.drop(columns=unnamed_cols)
                    columns = df.columns.tolist()
                    self.log(f"清理后的列: {', '.join([str(col) for col in columns])}")
                
                # 显示前几行数据作为样本
                self.log("数据样本:")
                sample_rows = min(3, df.shape[0])  # 最多显示3行
                for i in range(sample_rows):
                    self.log(f"行 {i+1}: {dict(df.iloc[i])}")
                
                # 预处理：移除列名中可能的空格、处理可能连在一起的列名
                if len(columns) == 1 and isinstance(columns[0], str) and 'title' in columns[0].lower():
                    # 处理可能连在一起的列名情况
                    self.log("检测到列名可能连在一起，尝试分割...")
                    
                    # 尝试使用预定义的列名进行拆分
                    expected_columns = ['title', 'seller_name', 'total_sales', 'price', 
                                       'sales', 'collect_time', 'product_url']
                    
                    # 读取数据为文本格式，避免类型转换问题
                    raw_data = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
                    
                    if not raw_data.empty:
                        # 检查是否有样本行
                        sample_row = raw_data.iloc[0, 0] if not raw_data.empty else ""
                        self.log(f"样本数据: {sample_row[:100]}...")
                        
                        # 根据样本数据和用户提供的例子，创建新的DataFrame
                        try:
                            # 尝试使用分隔符来分割，比如检查是否有明显的分隔符
                            new_rows = []
                            for idx, row in raw_data.iterrows():
                                data = row.iloc[0]
                                if isinstance(data, str):
                                    # 用于存储提取的数据
                                    extracted_data = {}
                                    
                                    # 查找并提取每个列的数据
                                    # 2025普通话水平测试冲刺礼包：考前冲刺视频课+电子版资料+范读 · 通用范文+资料题库（特别推荐！） 网盘发货非纸质(宝子们要注意呀)炫酷小煜的店250009.9210002025-03-25 14:17:08https://www.xiaohongshu.com/goods-detail/67bd5ced7198db0001313f06
                                    
                                    # 提取URL (最容易识别的部分)
                                    url_match = re.search(r'(https?://\S+)', data)
                                    if url_match:
                                        extracted_data['product_url'] = url_match.group(1)
                                        # 移除URL部分，便于处理其他字段
                                        data = data.replace(url_match.group(1), '')
                                    
                                    # 提取采集时间 (格式较为固定)
                                    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', data)
                                    if time_match:
                                        extracted_data['collect_time'] = time_match.group(1)
                                        # 移除时间部分
                                        data = data.replace(time_match.group(1), '')
                                    
                                    # 提取销量和价格 (通常是连续的数字)
                                    # 假设销量通常较大，价格通常较小且可能有小数点
                                    numbers = re.findall(r'\d+\.?\d*', data)
                                    if len(numbers) >= 2:
                                        # 提取价格和销量 (根据数值大小的模式来区分)
                                        numbers = [float(n) for n in numbers]
                                        numbers.sort()  # 从小到大排序
                                        
                                        # 假设较小的数通常是价格
                                        for n in numbers:
                                            if n < 1000:  # 通常价格小于1000
                                                extracted_data['price'] = str(n)
                                                break
                                        
                                        # 假设较大的数通常是销量
                                        for n in reversed(numbers):
                                            if n > 1000:  # 通常销量大于1000
                                                extracted_data['sales'] = str(int(n))
                                                break
                                        
                                        # 尝试识别total_sales (总销量)
                                        for n in reversed(numbers):
                                            if n > 1000 and 'sales' in extracted_data and n != float(extracted_data['sales']):
                                                extracted_data['total_sales'] = str(int(n))
                                                break
                                    
                                    # 提取卖家名称 (通常包含"店"字)
                                    seller_match = re.search(r'[^0-9a-zA-Z\s:/_\-.]+店', data)
                                    if seller_match:
                                        extracted_data['seller_name'] = seller_match.group(0)
                                        # 移除卖家名称部分
                                        data = data.replace(seller_match.group(0), '')
                                    
                                    # 剩余部分假设为标题
                                    # 清理标题前后的空格和特殊字符
                                    title = data.strip()
                                    if 'seller_name' in extracted_data:
                                        # 进一步清理可能的残留
                                        title = title.replace(extracted_data['seller_name'], '')
                                    extracted_data['title'] = title.strip()
                                    
                                    new_rows.append(extracted_data)
                            
                            # 创建新的DataFrame
                            if new_rows:
                                df = pd.DataFrame(new_rows)
                                self.log(f"成功分割数据，获取列: {', '.join(df.columns)}")
                            else:
                                self.log("无法自动分割列，请确保Excel文件格式正确")
                                continue
                                
                        except Exception as e:
                            self.log(f"尝试分割数据时出错: {str(e)}")
                            continue
                
                # 检查必需的列是否存在
                required_columns = ['title', 'seller_name', 'product_url']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    self.log(f"缺少必需的列: {', '.join(missing_columns)}，跳过工作表 {sheet_name}")
                    continue
                
                # 处理前先检查并提取商品ID
                self.log("提取商品ID并检查是否有重复...")
                product_ids = []
                for idx, row in df.iterrows():
                    product_url = row.get('product_url', '')
                    if not product_url or not isinstance(product_url, str) or 'xiaohongshu.com' not in product_url:
                        continue
                        
                    product_id = self.spider.extract_product_id(product_url)
                    if product_id:
                        # 添加product_id到DataFrame
                        df.at[idx, 'extracted_product_id'] = product_id
                        product_ids.append(product_id)
                
                # 检查是否有重复的product_id
                unique_ids = set(product_ids)
                if len(unique_ids) < len(product_ids):
                    duplicates = len(product_ids) - len(unique_ids)
                    self.log(f"检测到 {duplicates} 个重复的商品ID，进行数据过滤...")
                    
                    # 按product_id分组，保留每组中最新的记录
                    # 首先将collect_time转换为datetime类型以便排序
                    df['collect_time_dt'] = pd.to_datetime(df['collect_time'], errors='coerce')
                    
                    # 找出每个product_id的最新记录的索引
                    latest_indices = df.groupby('extracted_product_id')['collect_time_dt'].idxmax().tolist()
                    
                    # 仅保留这些索引的行
                    df = df.loc[latest_indices]
                    
                    self.log(f"过滤后保留 {len(df)} 行唯一商品数据")
                
                # 导入数据到数据库
                imported_count = 0
                for index, row in df.iterrows():
                    try:
                        # 获取已提取的商品ID
                        product_id = row.get('extracted_product_id')
                        if not product_id:
                            # 如果没有预先提取的ID，尝试从URL中提取
                            product_url = row.get('product_url', '')
                            if not product_url or not isinstance(product_url, str) or 'xiaohongshu.com' not in product_url:
                                self.log(f"第 {index+1} 行: 无效的商品URL: {product_url}，跳过")
                                continue
                                
                            product_id = self.spider.extract_product_id(product_url)
                        
                        if not product_id:
                            self.log(f"第 {index+1} 行: 无法提取商品ID，URL: {row.get('product_url', '')}，跳过")
                            continue
                        
                        # 获取当前时间作为导入时间
                        import_time = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 准备数据
                        title = str(row.get('title', '')) if not pd.isna(row.get('title', '')) else ''
                        seller_name = str(row.get('seller_name', '')) if not pd.isna(row.get('seller_name', '')) else ''
                        price = str(row.get('price', '')) if not pd.isna(row.get('price', '')) else ''
                        
                        # 处理销量数据，确保是字符串格式
                        sales = str(int(float(row.get('sales', 0)))) if not pd.isna(row.get('sales', '')) else '0'
                        total_sales = str(int(float(row.get('total_sales', 0)))) if not pd.isna(row.get('total_sales', '')) else '0'
                        
                        # 处理采集时间
                        collect_time = row.get('collect_time', '')
                        if pd.isna(collect_time) or not collect_time:
                            collect_time = import_time
                        elif isinstance(collect_time, (pd.Timestamp, datetime)):
                            collect_time = collect_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 1. 插入商品信息到goods表
                        success, status = self.spider.db.insert_goods(product_id, title, seller_name, price, collect_time)
                        if success:
                            if status == "inserted":
                                self.log(f"商品信息已保存到数据库: {product_id}")
                            else:
                                self.log(f"商品已存在，更新采集计数: {product_id}")
                        
                        # 2. 插入账号信息到account表
                        account_url = row.get('account_url', '')
                        if isinstance(account_url, float) and math.isnan(account_url):
                            account_url = ''
                        self.spider.db.insert_account(seller_name, account_url, total_sales, collect_time)
                        
                        # 3. 插入采集数据到collect_data表
                        self.spider.db.insert_collect_data(product_id, sales, collect_time)
                        
                        # 4. 插入店铺采集数据到collect_account_data表
                        if seller_name and total_sales:
                            self.spider.db.insert_collect_account_data(seller_name, total_sales, collect_time)
                        
                        imported_count += 1
                        
                        # 每导入10条记录输出一次日志
                        if imported_count % 10 == 0:
                            self.log(f"已从工作表 '{sheet_name}' 导入 {imported_count} 条记录")
                        
                    except Exception as e:
                        self.log(f"导入第 {index+1} 行数据时出错: {str(e)}")
                        import traceback
                        self.log(traceback.format_exc())
                        continue
                
                self.log(f"工作表 '{sheet_name}' 导入完成，成功导入 {imported_count} 条记录")
                total_imported += imported_count
            
            if total_imported == 0:
                self.log(f"警告: 未能从文件 {os.path.basename(file_path)} 导入任何数据")
                self.log("请确保Excel文件格式正确，并包含必要的列: 'title', 'seller_name', 'product_url'")
            else:
                self.log(f"文件 {os.path.basename(file_path)} 导入完成，成功导入 {total_imported} 条记录")
            
            return total_imported
            
        except Exception as e:
            self.log(f"处理文件 {file_path} 时出错: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return 0
        finally:
            # 确保Excel文件关闭，释放资源
            if excel_file is not None:
                try:
                    excel_file.close()
                    self.log(f"已关闭文件: {file_path}")
                except:
                    pass

    def clear_database(self):
        """清空数据库"""
        try:
            # 确认对话框
            confirm = messagebox.askyesno(
                "确认清空数据库", 
                "确定要清空数据库中的所有数据吗？\n此操作不可恢复！",
                icon='warning'
            )
            
            if not confirm:
                self.log("取消清空数据库操作")
                return
                
            # 确保爬虫实例已创建
            if not hasattr(self, 'spider') or self.spider is None:
                self.log("创建爬虫实例...")
                try:
                    self.spider = XHSSpider(self)
                except Exception as e:
                    self.log(f"爬虫实例创建失败: {str(e)}")
                    return
            
            # 调用数据库清空方法
            success, message = self.spider.db.clear_all_data()
            
            if success:
                self.log(message)
                messagebox.showinfo("操作成功", "数据库已成功清空")
            else:
                self.log(f"清空数据库失败: {message}")
                messagebox.showerror("操作失败", f"清空数据库时出错: {message}")
                
        except Exception as e:
            self.log(f"清空数据库操作出错: {str(e)}")
            messagebox.showerror("操作错误", f"清空数据库操作出错: {str(e)}")

    def on_tree_item_double_click(self, event):
        """处理列表行双击事件"""
        # 获取点击的项目
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        # 获取该项对应的URL
        if item in self.tree_item_urls:
            url = self.tree_item_urls[item]
            self.open_url_in_browser(url)
    
    def show_tree_item_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击的项目
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
            
        # 选中被点击的项目
        self.tree.selection_set(item)
        
        # 创建右键菜单
        context_menu = tk.Menu(self.window, tearoff=0)
        context_menu.add_command(label="打开商品链接", command=lambda: self.open_item_url(item))
        context_menu.add_command(label="复制商品链接", command=lambda: self.copy_item_url(item))
        
        # 显示菜单
        context_menu.tk_popup(event.x_root, event.y_root)
    
    def open_item_url(self, item):
        """打开选中项的URL"""
        if item in self.tree_item_urls:
            url = self.tree_item_urls[item]
            self.open_url_in_browser(url)
    
    def copy_item_url(self, item):
        """复制选中项的URL到剪贴板"""
        if item in self.tree_item_urls:
            url = self.tree_item_urls[item]
            self.window.clipboard_clear()
            self.window.clipboard_append(url)
            messagebox.showinfo("复制成功", "商品链接已复制到剪贴板")
    
    def open_url_in_browser(self, url):
        """在默认浏览器中打开URL"""
        try:
            import webbrowser
            if url and isinstance(url, str) and url.startswith('http'):
                self.log(f"正在浏览器中打开: {url}")
                webbrowser.open(url)
            else:
                self.log(f"无效的URL: {url}")
                messagebox.showwarning("打开链接", "无效的商品链接")
        except Exception as e:
            self.log(f"打开浏览器失败: {str(e)}")
            messagebox.showerror("打开链接", f"无法打开浏览器: {str(e)}")

# 添加资源路径检测函数
def resource_path(relative_path):
    """获取资源的绝对路径，兼容PyInstaller打包后的路径"""
    try:
        # PyInstaller创建临时文件夹存放资源文件
        base_path = sys._MEIPASS
    except Exception:
        # 不是通过PyInstaller运行，使用当前文件路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

class XHSSpider:
    def __init__(self, gui):
        self.gui = gui
        # 获取当前脚本所在目录（兼容打包后路径）
        try:
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                self.base_dir = os.path.dirname(sys.executable)
            else:
                # 未打包的脚本
                self.base_dir = os.path.dirname(os.path.abspath(__file__))
        except:
            self.base_dir = os.getcwd()
            
        # 创建数据保存目录
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.images_dir = os.path.join(self.data_dir, 'images')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 初始化数据库
        db_path = os.path.join(self.data_dir, 'xiaohongshu.db')
        self.db = Database(db_path)
        self.log(f"数据库已初始化: {db_path}")
        
        try:
            # 使用Chrome浏览器
            self.gui.log("正在配置Chrome浏览器...")
            
            # 设置Chrome选项
            options = Options()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")  # 静默日志
            
            # 自动下载Chrome驱动 - 修复路径问题
            self.gui.log("正在下载Chrome驱动...")
            driver_path = ChromeDriverManager().install()
            # 修复路径中的斜杠
            driver_path = driver_path.replace('/', '\\')
            self.gui.log(f"使用驱动: {driver_path}")
            
            # 初始化浏览器
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 设置等待和数据
            self.wait = WebDriverWait(self.driver, 20)
            self.data = []
            
            # 打开小红书主页
            self.driver.get('https://www.xiaohongshu.com')
            time.sleep(5)
        except Exception as e:
            self.gui.log("Chrome浏览器启动失败！请检查：")
            self.gui.log("1. 是否已安装Chrome浏览器")
            self.gui.log(f"错误信息: {str(e)}")
            raise Exception("浏览器启动失败，请确保已安装Chrome浏览器")
        
    def log(self, message):
        """输出日志到GUI"""
        self.gui.log(message)
        
    def extract_number(self, text):
        """提取字符串中的数字，支持万级单位，并转换为整数格式"""
        if not text:
            return ''
        
        # 处理万级数字
        if '万' in text:
            number = re.findall(r'([\d.]+)万', text)
            if number:
                # 转换为整数格式
                return str(int(float(number[0]) * 10000))
        
        # 处理普通数字
        numbers = re.findall(r'\d+', text)
        return numbers[0] if numbers else ''
        
    def extract_product_id(self, url):
        """从URL中提取商品ID"""
        match = re.search(r'goods-detail/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        return None
        
    def get_product_info(self, url):
        try:
            self.log(f"正在处理URL: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            self.log("页面标题: " + self.driver.title)
            
            # 提取商品ID
            product_id = self.extract_product_id(url)
            if not product_id:
                self.log("无法提取商品ID，跳过")
                return None
                
            self.log(f"商品ID: {product_id}")
            
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'graphic-detail-container')))
            except Exception as e:
                self.log(f"等待页面加载失败: {str(e)}")
                return None
            
            self.scroll_page()
            
            try:
                # 获取商品标题
                title = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'goods-name'))).text
                self.log(f"找到标题: {title}")
                
                # 获取店铺信息
                seller_name = self.driver.find_element(By.CLASS_NAME, 'seller-name').text
                self.log(f"找到店铺名: {seller_name}")
                
                # 获取店铺链接
                account_url = ""
                try:
                    seller_link = self.driver.find_element(By.CSS_SELECTOR, '.seller-name')
                    parent_link = seller_link.find_element(By.XPATH, '..')
                    account_url = parent_link.get_attribute('href')
                    self.log(f"找到店铺链接: {account_url}")
                except Exception as e:
                    self.log(f"无法获取店铺链接: {str(e)}")
                
                # 获取商品销量 - 转换为整数格式
                sales_element = self.driver.find_element(By.CLASS_NAME, 'spu-text')
                sales_text = sales_element.text
                sales = ''
                if '万' in sales_text:
                    number = re.findall(r'([\d.]+)万', sales_text)
                    if number:
                        # 直接转换为整数格式，乘以10000
                        sales = str(int(float(number[0]) * 10000))
                else:
                    sales = self.extract_number(sales_text)
                self.log(f"找到销量: {sales}")
                
                # 获取店铺粉丝数和总销量
                sub_titles = self.driver.find_elements(By.CLASS_NAME, 'sub-title')
                followers = ''
                total_sales = ''
                
                for sub_title in sub_titles:
                    text = sub_title.text
                    if '粉丝数' in text:
                        followers = self.extract_number(text)
                    elif '已售' in text:
                        total_sales = self.extract_number(text)
                        # 确保total_sales是整数
                        if total_sales and total_sales.isdigit():
                            total_sales = str(int(total_sales))
                
                self.log(f"店铺粉丝数: {followers}")
                self.log(f"店铺总销量: {total_sales}")
                
                # 获取商品主图
                main_img_urls = []
                swiper = self.driver.find_element(By.CLASS_NAME, 'swiper-wrapper')
                img_elements = swiper.find_elements(By.TAG_NAME, 'img')
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src:
                        main_img_urls.append(src)
                self.log(f"找到 {len(main_img_urls)} 张主图")
                
                # 获取商品详情图片
                detail_container = self.driver.find_element(By.CLASS_NAME, 'graphic-detail-container')
                detail_imgs = detail_container.find_elements(By.TAG_NAME, 'img')
                detail_urls = [img.get_attribute('src') for img in detail_imgs if img.get_attribute('src')]
                self.log(f"找到 {len(detail_urls)} 张详情图")
                
                # 下载图片到商品专属文件夹
                folder_name = self.sanitize_filename(title)
                self.save_images(main_img_urls, folder_name, 'main')
                self.save_images(detail_urls, folder_name, 'detail')
                
                # 添加获取价格的代码
                try:
                    # 尝试多种可能的CSS选择器
                    selectors = [
                        "div.price", 
                        "div.price p span", 
                        "div[class*='price']", 
                        "div[data-v-8686a314].price"
                    ]
                    
                    price = "N/A"
                    for selector in selectors:
                        try:
                            price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_element.text.replace("¥", "").strip()
                            # 提取数字部分
                            price = re.search(r'\d+(\.\d+)?', price_text).group()
                            if price:
                                break
                        except:
                            continue
                    
                    if price == "N/A":
                        # 尝试使用XPath
                        try:
                            price_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'price')]//span[contains(text(), '¥')]/following-sibling::p/span")
                            price = price_element.text.strip()
                        except:
                            self.log("无法获取商品价格")
                except:
                    price = "N/A"
                    self.log("无法获取商品价格")
                
                # 获取当前时间作为采集时间
                collect_time = time.strftime('%Y-%m-%d %H:%M:%S')
                
                # 保存数据到数据库
                success, status = self.db.insert_goods(product_id, title, seller_name, price, collect_time)
                if success:
                    if status == "inserted":
                        self.log(f"商品信息已保存到数据库: {product_id}")
                    else:
                        self.log(f"商品已存在，更新采集计数: {product_id}")
                
                # 直接保存账号信息，不获取链接
                self.db.insert_account(seller_name, "", total_sales, collect_time)
                self.log(f"账号信息已保存到数据库: {seller_name}")
                
                # 保存店铺采集数据，记录不同采集时间的店铺销量
                if seller_name and total_sales:
                    self.db.insert_collect_account_data(seller_name, total_sales, collect_time)
                    self.log(f"店铺采集数据已保存到数据库: {seller_name} - 总销量 {total_sales}")
                
                # 保存采集数据
                if product_id and sales:
                    self.db.insert_collect_data(product_id, sales, collect_time)
                    self.log(f"采集数据已保存到数据库: {product_id} - 销量 {sales}")
                
                return {
                    'product_id': product_id,
                    'title': title,
                    'seller_name': seller_name,
                    'price': price,
                    'sales': sales,  # 现在是整数格式
                    'total_sales': total_sales,  # 确保是整数
                    'collect_time': collect_time,
                    'product_url': url,
                    'account_url': account_url
                }
                
            except Exception as e:
                self.log(f"提取商品信息失败: {str(e)}")
                import traceback
                self.log(traceback.format_exc())
                return None
            
        except Exception as e:
            self.log(f"处理URL失败: {str(e)}")
            return None
            
    def scroll_page(self):
        """滚动页面直到底部"""
        self.log("开始滚动页面...")
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        no_change_count = 0
        max_no_change = 5  # 连续5次高度不变才认为到底
        
        while no_change_count < max_no_change:
            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # 等待加载
            
            # 获取新的页面高度
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            
            # 检查是否有新内容加载
            if new_height == last_height:
                no_change_count += 1
                self.log(f"页面高度未变化，等待次数: {no_change_count}")
            else:
                no_change_count = 0
                self.log(f"页面高度更新: {new_height}")
                
            last_height = new_height
        
        self.log("已到达页面底部")
            
    def sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        # 移除特殊字符，保留中文、字母、数字
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', filename)
        return cleaned.strip()
            
    def save_images(self, img_urls, product_folder, img_type):
        """保存图片到商品专属文件夹"""
        # 检查是否需要保存图片
        if not self.gui.save_images_var.get():
            self.log(f"跳过保存{img_type}图片（未勾选保存图片选项）")
            return
            
        # 在 images 目录下创建商品文件夹
        folder_path = os.path.join(self.images_dir, product_folder)
        os.makedirs(folder_path, exist_ok=True)
        
        self.log(f"开始下载 {len(img_urls)} 张{img_type}图片到 {folder_path}")
        for i, url in enumerate(img_urls):
            try:
                if not url or not url.startswith('http'):
                    continue
                    
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    ext = os.path.splitext(urlparse(url).path)[1]
                    if not ext:
                        ext = '.jpg'
                        
                    # 文件名格式: 类型_序号.扩展名
                    filename = f'{img_type}_{i+1}{ext}'
                    path = os.path.join(folder_path, filename)
                    
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    self.log(f"成功保存图片: {path}")
            except Exception as e:
                self.log(f"保存图片失败 {url}: {str(e)}")
                continue
    
    def save_to_file(self, data, filename, file_type="xlsx"):
        """保存数据到文件"""
        if not data:
            self.log("没有数据可以保存")
            return False
        
        try:
            df = pd.DataFrame(data)
            
            # 过滤掉不需要的列
            columns_to_keep = ['product_id', 'title', 'seller_name', 'price', 'sales', 'total_sales', 
                              'collect_time', 'product_url', 'account_url']
            
            # 仅保留需要的列（如果它们存在于DataFrame中）
            available_columns = [col for col in columns_to_keep if col in df.columns]
            df = df[available_columns]
            
            # 确保列的顺序，将price放在sales前面
            if "price" in df.columns and "sales" in df.columns:
                # 获取所有列
                all_columns = list(df.columns)
                # 移除price和sales
                all_columns.remove("price")
                all_columns.remove("sales")
                # 获取sales的原始位置
                sales_idx = list(df.columns).index("sales")
                # 在sales位置插入price和sales
                all_columns.insert(sales_idx, "sales")
                all_columns.insert(sales_idx, "price")
                # 重新排序列
                df = df[all_columns]
            
            if file_type == "xlsx":
                df.to_excel(filename, index=False)
            else:
                df.to_csv(filename, index=False, encoding="utf_8_sig")
            
            self.log(f"数据已保存到: {filename}")
            return True
        except Exception as e:
            self.log(f"保存数据时出错: {str(e)}")
            return False
            
    def run(self, urls):
        try:
            total = len(urls)
            
            for i, url in enumerate(urls, 1):
                info = self.get_product_info(url)
                if info:
                    self.data.append(info)
                    self.log(f"成功提取商品信息: {info['title']}")
                        
                self.gui.update_progress(i, total)
                time.sleep(3)
            
            if self.data:
                self.save_to_file(self.data, os.path.join(self.data_dir, f'products_{time.strftime("%Y%m%d_%H%M%S")}.xlsx'))
            else:
                self.log("没有成功提取到任何商品信息")
                    
        except Exception as e:
            self.log(f"运行出错: {str(e)}")
        finally:
            # 关闭数据库连接
            self.db.close()
            # 不关闭浏览器，让用户可以继续使用
            # self.driver.quit()

# 在程序入口处调用
if __name__ == '__main__':
    try:
        # 创建并运行GUI
        gui = SpiderGUI()
        gui.run()
    except Exception as e:
        print(f"程序启动错误: {str(e)}") 