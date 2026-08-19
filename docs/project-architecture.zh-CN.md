# 项目架构说明

## 目录约定

```text
personal_blog/
├── admin/                  # 博客管理后台 Vue 应用
├── backend/                # FastAPI 应用
│   ├── app/
│   │   ├── api/            # API 路由和版本
│   │   ├── core/           # 配置、数据库、基础设施
│   │   ├── models/         # SQLAlchemy ORM 模型
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── services/       # 业务服务
│   │   └── main.py
│   ├── migrations/         # Alembic 迁移
│   └── scripts/            # 本地初始化脚本
├── docs/                   # 人和 AI 共用的项目文档
├── web/                    # 个人博客前台 Vue 应用
└── package.json            # npm workspace 编排
```

## 依赖方向

路由 `api` -> 服务 `services` -> 数据访问/模型 `models`。Schema 不依赖路由，前端页面通过 API client 访问后端。跨应用共享的契约未来优先通过 OpenAPI 生成或明确复制，禁止隐式耦合源码。

## 环境

- 后端开发：根目录 `.venv`
- 数据库：本地 MySQL，连接串由 `backend/.env` 提供
- 前台默认端口：`5173`
- 后台默认端口：`5174`
- 后端默认端口：`8000`
