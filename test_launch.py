# -*- coding: utf-8 -*-
import sys
import traceback

# 设置控制台输出编码
import os
os.system('chcp 65001 >nul')

try:
    print("开始导入模块...")

    # 测试基础模块导入
    import tkinter as tk
    print("OK tkinter导入成功")

    from selenium import webdriver
    print("OK selenium导入成功")

    from webdriver_manager.chrome import ChromeDriverManager
    print("OK webdriver_manager导入成功")

    import pandas as pd
    print("OK pandas导入成功")

    # 测试GUI创建
    print("\n开始测试GUI创建...")
    root = tk.Tk()
    root.title("测试窗口")
    root.geometry("300x200")

    label = tk.Label(root, text="程序启动成功！\n这是测试窗口")
    label.pack(pady=50)

    print("✓ GUI创建成功")
    print("窗口已创建，请检查是否显示...")

    # 显示窗口3秒后自动关闭
    root.after(3000, root.destroy)
    root.mainloop()

    print("测试完成")

except Exception as e:
    print(f"❌ 错误: {str(e)}")
    print("详细错误信息:")
    traceback.print_exc()