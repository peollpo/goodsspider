# -*- coding: utf-8 -*-
import sys
import traceback

try:
    print("Testing module imports...")

    # 测试基础模块导入
    import tkinter as tk
    print("OK tkinter imported")

    from selenium import webdriver
    print("OK selenium imported")

    from webdriver_manager.chrome import ChromeDriverManager
    print("OK webdriver_manager imported")

    import pandas as pd
    print("OK pandas imported")

    # 测试GUI创建
    print("\nTesting GUI creation...")
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("300x200")

    label = tk.Label(root, text="Program started successfully!\nThis is a test window")
    label.pack(pady=50)

    print("OK GUI created successfully")
    print("Window created, checking display...")

    # 显示窗口3秒后自动关闭
    root.after(3000, root.destroy)
    root.mainloop()

    print("Test completed")

except Exception as e:
    print(f"ERROR: {str(e)}")
    print("Detailed error information:")
    traceback.print_exc()