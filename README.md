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
python backend\scripts\generate_password_hash.py
alembic -c backend\alembic.ini upgrade head
npm run dev:backend
```

API 文档地址：`http://127.0.0.1:8000/docs`

开发模式下，后端默认开启 `--reload`，修改 `backend/` 下的 Python 代码后会自动重启服务。

后台管理接口需要服务端登录态。复制 `.env.example` 后，把脚本生成的哈希写入
`backend/.env` 的 `ADMIN_PASSWORD_HASH`，并按需调整 `ADMIN_USERNAME`。

### 3. 启动前台或后台

```powershell
npm install
npm run dev:web
npm run dev:admin
```

后台 API 地址通过 `admin` 应用的 `VITE_API_BASE_URL` 配置，生产默认可使用同源
`/api/v1`，本地前后端分端口运行时可设置为 `http://127.0.0.1:8000/api/v1`。

“关于我”页面的高德地图使用前台环境变量加载。需要真实地图时先复制 `web/.env.example` 为
`web/.env.local`，再填写高德开放平台的 Web 端 JS API Key 与安全密钥；城市名称和坐标仍在
管理后台的“关于我”模块维护。

## 当前范围

本次只完成项目初始化、基础健康检查接口、数据库连接/迁移链路和前后台入口。首页、文章、关于自己、登录、文章编辑等具体业务模块，先按照 `docs/module-discussion.md` 逐项讨论后再实现。

## 部署备注

需要将当前项目打包、上传并更新到服务器时，请阅读简明教程：
[`docs/deployment-guide.zh-CN.md`](docs/deployment-guide.zh-CN.md)。

### 上传目录持久化

生产环境不要把上传文件长期放在代码发布目录里。后端已支持通过 `UPLOAD_DIR` 指定真实上传目录，本地默认值仍是 `backend/uploads`。

服务器部署时建议创建代码目录外的持久化目录：

```bash
sudo mkdir -p /data/personal_blog/uploads/resumes
sudo chown -R <运行后端的用户>:<运行后端的用户> /data/personal_blog/uploads
```

然后在服务器 `backend/.env` 中配置：

```env
UPLOAD_DIR=/data/personal_blog/uploads
PUBLIC_BASE_URL=https://你的域名
```

如果部署前本地或旧服务器已有上传文件，需要先迁移：

```bash
cp -a backend/uploads/. /data/personal_blog/uploads/
```

`/data/personal_blog/uploads` 需要纳入服务器备份；后续发布代码、重新解压或拉取仓库时，不要删除这个目录。

## 协作规范

使用 Codex 继续开发前，请先阅读：

- `AGENTS.md`
- `docs/ai-development-guidelines.zh-CN.md`
- `docs/project-architecture.zh-CN.md`
- `docs/module-discussion.md`
