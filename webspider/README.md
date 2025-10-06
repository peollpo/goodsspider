# WebSpider Minimal Demo

This directory hosts the minimal Strapi-based demo for the 小红书商品采集 Web 系统。
The demo exposes任务认领与回传接口，并在 MySQL 中存储店铺、商品与采集任务信息。

## 内容列表

- `backend/` – Strapi 应用（MySQL 驱动、基础内容模型、自定义任务 API）。
- `collector/demo_worker.py` – 简易采集端示例脚本，演示如何调用任务领取/回传接口。

## 快速开始

1. 准备 MySQL（默认使用 `webspider` 数据库，账号 `root` / `example`）。
2. 在 `backend` 目录安装依赖并启动 Strapi：

   ```bash
   cd backend
   npm install
   npm run develop
   ```

3. （可选）运行示例采集端脚本：

   ```bash
   cd collector
   pip install requests
   python demo_worker.py
   ```

   采集端会轮询 `/api/crawl-tasks/claim`，并随机生成商品数据回传。

4. 通过 http://localhost:1337/admin 创建管理员账号，管理内容模型和数据。

详细接口说明、模型字段及扩展计划见仓库根目录提供的系统设计文档。
