import sqlite3
import pandas as pd

# 查看数据库表结构
conn = sqlite3.connect('data/xiaohongshu.db')
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("数据库表:", [t[0] for t in tables])

# 查看每个表的结构
for table in tables:
    table_name = table[0]
    print(f"\n=== {table_name} 表结构 ===")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'主键' if col[5] else '普通列'}")
    
    # 查看表的数据量
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  数据量: {count} 条")

conn.close()

