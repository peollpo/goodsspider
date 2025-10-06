# Backend (Strapi) – Minimal Demo

## 运行环境
- Node.js 18 - 22
- MySQL 8（或兼容版本）
- npm 8+

## 配置
复制 `.env.example` 为 `.env`，并根据实际 MySQL 连接信息调整：

```bash
cp .env.example .env
# 修改数据库主机、账号、密码等
```

默认字段：

```
DATABASE_CLIENT=mysql
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=webspider
DATABASE_USERNAME=root
DATABASE_PASSWORD=example
```

## 安装与启动

```bash
npm install
npm run develop
```

启动后访问 http://localhost:1337/admin 首次创建管理员账号。

## 主要内容模型
- **Store**：小红书店铺（externalId, name, followers, metadata, products）
- **Product**：商品（externalId, title, price, sales, coverUrl, metadata, lastCrawledAt, store, tasks）
- **Crawl Task**：采集任务（title, url, state, priority, payload, result, workerId, attempts, scheduledAt, completedAt, product）
- **Collector Log**：采集端日志（workerId, level, message, details, task）

## 自定义接口
- `POST /api/crawl-tasks/claim`
  - 请求：`{"workerId": "worker-1", "limit": 5}`
  - 响应：任务数组，并将状态置为 `processing`

- `POST /api/crawl-tasks/:id/complete`
  - 请求：
    ```json
    {
      "state": "done",
      "product": {
        "externalId": "xxx",
        "title": "Demo",
        "price": 19.9,
        "sales": 120,
        "store": { "externalId": "store-1", "name": "旗舰店" }
      },
      "result": { "raw": {} }
    }
    ```
  - 作用：更新任务状态，自动 upsert 店铺/商品数据，并清空锁信息。

## 后续扩展建议
- 接入 JWT/API Token + IP 白名单
- 引入消息队列/多 Worker 并发
- 结合对象存储上传图片
- 增加图表/报表前端


