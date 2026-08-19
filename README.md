# Personal Blog

一个以航海日志为视觉方向的个人博客 monorepo，包含：

- `backend/`: FastAPI 后端 API、SQLAlchemy 2 ORM、Alembic 数据库迁移
- `web/`: Vue 3 + Vite 个人博客前台
- `admin/`: Vue 3 + Vite 博客管理后台
- `docs/`: 项目设计、开发和 AI 协作规范
- `.venv/`: Python 虚拟环境（本地生成，不提交）

## 技术栈

- 后端：Python 3.13、FastAPI、Pydantic Settings、SQLAlchemy 2、Alembic、PyMySQL、MySQL 8+
- 前端：Vue 3、TypeScript、Vite、Vue Router、Pinia
- 工程化：npm workspaces、ESLint、Prettier、Git

## 快速开始

### 1. 创建数据库

确保本机 MySQL 服务已启动，然后执行 `backend/scripts/create_database.sql`。

默认连接信息：

```text
主机：127.0.0.1
端口：3306
用户：root
密码：见本地 `backend/.env`
数据库：personal_blog
```

### 2. 启动后端

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
alembic -c backend\alembic.ini upgrade head
npm run dev:backend
```

API 文档地址：`http://127.0.0.1:8000/docs`

开发模式下，后端默认开启 `--reload`，修改 `backend/` 下的 Python 代码后会自动重启服务。

### 3. 启动前台或后台

```powershell
npm install
npm run dev:web
npm run dev:admin
```

## 当前范围

本次只完成项目初始化、基础健康检查接口、数据库连接/迁移链路和前后台入口。首页、文章、关于自己、登录、文章编辑等具体业务模块，先按照 `docs/module-discussion.md` 逐项讨论后再实现。

## 协作规范

使用 Codex 继续开发前，请先阅读：

- `AGENTS.md`
- `docs/ai-development-guidelines.zh-CN.md`
- `docs/project-architecture.zh-CN.md`
- `docs/module-discussion.md`
