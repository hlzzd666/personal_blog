# Personal Blog 简明部署教程

本文只说明当前项目如何打包、上传和发布。服务器已经配置完成，不需要重新安装软件。

## 1. 发布时要上传什么

每次完整发布只上传三个压缩包：

| 压缩包 | 内容 | 服务器临时上传位置 | 正式发布位置 |
|---|---|---|---|
| `web.tar.gz` | 博客前台 | `/tmp/web.tar.gz` | `/var/www/personal_blog/releases/web-版本号` |
| `admin.tar.gz` | 管理后台 | `/tmp/admin.tar.gz` | `/var/www/personal_blog/releases/admin-版本号` |
| `backend.tar.gz` | Python 后端 | `/tmp/backend.tar.gz` | `/opt/personal_blog/releases/backend-版本号` |

不要上传下面这些内容：

- 不上传 `node_modules`。
- 不上传本地 `.env`。
- 不上传本地 `.venv`。
- 不上传 `backend/uploads`。

## 2. 本地打包

打开 Windows PowerShell，执行：

```powershell
Set-Location D:\codex-test\personal_blog
```

### 2.1 打包博客前台

```powershell
npm run build:web
tar -czf web.tar.gz -C web/dist .
```

前台生产构建固定使用 `/web/` 基路径，本地开发仍使用根路径。不要覆盖该构建配置，
否则线上静态资源或前端路由可能出现 404。

生成：

```text
D:\codex-test\personal_blog\web.tar.gz
```

### 2.2 打包管理后台

```powershell
npm run build:admin

tar -czf admin.tar.gz -C admin/dist .
```

生成：

```text
D:\codex-test\personal_blog\admin.tar.gz
```

后台 Vite 配置已固定生产基路径为 `/admin/`，开发环境仍为 `/`；普通构建命令即可生成可部署产物。

### 2.3 打包 Python 后端

```powershell
tar -czf backend.tar.gz `
  --exclude='backend/.env*' `
  --exclude='backend/data' `
  --exclude='backend/uploads' `
  --exclude='__pycache__' `
  --exclude='*.pyc' `
  backend
```

生成：

```text
D:\codex-test\personal_blog\backend.tar.gz
```

打包完成后，项目根目录应该有：

```text
web.tar.gz
admin.tar.gz
backend.tar.gz
```

## 3. 上传到服务器

### 使用 FinalShell

1. 使用 FinalShell 连接 `47.111.75.30`。
2. 在服务器文件窗口打开 `/tmp`。
3. 把 `web.tar.gz`、`admin.tar.gz`、`backend.tar.gz` 拖进 `/tmp`。
4. 等待三个文件上传完成。

也可以在本地 PowerShell 执行：

```powershell
scp web.tar.gz root@47.111.75.30:/tmp/
scp admin.tar.gz root@47.111.75.30:/tmp/
scp backend.tar.gz root@47.111.75.30:/tmp/
```

## 4. 在服务器发布

以下命令全部在 FinalShell 的服务器终端执行。

### 4.1 生成本次版本号

```bash
STAMP=$(date +%Y%m%d%H%M%S)
echo $STAMP
```

不要关闭这个终端，后面的命令会继续使用 `$STAMP`。

### 4.2 发布后端

创建目录并解压：

```bash
NEW_BACKEND="/opt/personal_blog/releases/backend-$STAMP"
mkdir -p "$NEW_BACKEND"
tar -xzf /tmp/backend.tar.gz -C "$NEW_BACKEND"
```

复制当前生产配置和站点设置：

```bash
cp /opt/personal_blog/backend/.env "$NEW_BACKEND/backend/.env"
mkdir -p "$NEW_BACKEND/backend/data"
cp -a /opt/personal_blog/backend/data/. "$NEW_BACKEND/backend/data/"
chown -R personal_blog:personal_blog "$NEW_BACKEND"
chmod 600 "$NEW_BACKEND/backend/.env"
```

这一步不能省略，否则可能丢失线上配置或覆盖站点设置。

安装依赖并更新数据库表：

```bash
/opt/personal_blog/.venv/bin/python -m pip install \
  -r "$NEW_BACKEND/backend/requirements.txt"

cd "$NEW_BACKEND"
/opt/personal_blog/.venv/bin/python -m alembic \
  -c backend/alembic.ini upgrade head
```

切换到新后端并重启：

```bash
ln -sfn "$NEW_BACKEND/backend" /opt/personal_blog/backend.next
mv -Tf /opt/personal_blog/backend.next /opt/personal_blog/backend

systemctl restart personal-blog-backend
systemctl status personal-blog-backend --no-pager
```

看到 `active (running)` 表示后端正常。

### 4.3 发布两个前端

解压前台和后台：

```bash
NEW_WEB="/var/www/personal_blog/releases/web-$STAMP"
NEW_ADMIN="/var/www/personal_blog/releases/admin-$STAMP"

mkdir -p "$NEW_WEB" "$NEW_ADMIN"
tar -xzf /tmp/web.tar.gz -C "$NEW_WEB"
tar -xzf /tmp/admin.tar.gz -C "$NEW_ADMIN"

chown -R root:root "$NEW_WEB" "$NEW_ADMIN"
find "$NEW_WEB" "$NEW_ADMIN" -type d -exec chmod 755 {} \;
find "$NEW_WEB" "$NEW_ADMIN" -type f -exec chmod 644 {} \;
```

切换到新前端：

```bash
ln -sfn "$NEW_WEB" /var/www/personal_blog/web-current.next
mv -Tf /var/www/personal_blog/web-current.next \
  /var/www/personal_blog/web-current

ln -sfn "$NEW_ADMIN" /var/www/personal_blog/admin-current.next
mv -Tf /var/www/personal_blog/admin-current.next \
  /var/www/personal_blog/admin-current
```

前端是静态文件，不需要单独重启前端服务。检查并重新加载 Nginx：

```bash
nginx -t
systemctl reload nginx
```

### 4.4 检查是否发布成功

检查后端接口：

```bash
curl -i http://127.0.0.1:8000/api/v1/health
```

看到 `200 OK` 表示后端正常。

检查前台路径和重定向：

```bash
curl -I http://47.111.75.30/
curl -I http://47.111.75.30/web
curl -I http://47.111.75.30/web/
curl -I http://47.111.75.30/web/about
```

预期结果：

- `/` 返回 `301` 并跳转到 `/web/`。
- `/web` 返回 `301` 并跳转到 `/web/`。
- `/web/` 和 `/web/about` 返回 `200`。

浏览器打开：

```text
前台：https://www.ranjl.cn/web/
后台：https://www.ranjl.cn/admin/login
```

按 `Ctrl+F5` 强制刷新，避免浏览器继续使用旧文件。

确认网站正常后删除临时压缩包：

```bash
rm -f /tmp/web.tar.gz /tmp/admin.tar.gz /tmp/backend.tar.gz
```

然后回到本地 PowerShell，删除已经上传的发布包，避免下次误传旧版本：

```powershell
Remove-Item web.tar.gz, admin.tar.gz, backend.tar.gz -ErrorAction SilentlyContinue
```

这三个根目录发布包已配置在 `.gitignore` 中，不会进入 Git；即使如此，
每次完成线上验收后仍应执行本地清理，避免长期占用空间或混淆版本。

## 5. 只更新一个项目

不需要每次都发布全部项目。

| 修改内容 | 本地打包 | 上传 | 服务器操作 | 是否重启后端 |
|---|---|---|---|---|
| 只改博客前台 | 第 2.1 节 | `web.tar.gz` | 第 4.1 节和第 4.3 节中的前台命令 | 否 |
| 只改管理后台 | 第 2.2 节 | `admin.tar.gz` | 第 4.1 节和第 4.3 节中的后台命令 | 否 |
| 只改 Python 后端 | 第 2.3 节 | `backend.tar.gz` | 第 4.1 节和第 4.2 节 | 是 |

只更新一个前端时，不要执行另一个前端的 `tar -xzf` 命令，因为服务器上没有上传对应压缩包。

## 6. 配置文件在哪里

### 后端生产配置

文件：

```text
/opt/personal_blog/backend/.env
```

修改：

```bash
nano /opt/personal_blog/backend/.env
```

常见配置包括数据库连接、Redis、上传目录、管理员账号和 Cookie：

```env
DATABASE_URL=数据库连接地址
PUBLIC_BASE_URL=http://47.111.75.30
SITE_URL=http://47.111.75.30
WEB_BASE_PATH=/web
WEB_DIST_DIR=/var/www/personal_blog/web-current
UPLOAD_DIR=/data/personal_blog/uploads
MEDIA_STORAGE_DRIVER=oss
OSS_ENDPOINT=https://oss-cn-your-region.aliyuncs.com
OSS_BUCKET=your-bucket
OSS_ACCESS_KEY_ID=服务器专用访问密钥
OSS_ACCESS_KEY_SECRET=服务器专用访问密钥
OSS_PUBLIC_BASE_URL=https://cdn.example.com
OSS_OBJECT_PREFIX=personal-blog/prod
REDIS_URL=redis://127.0.0.1:6379/0
ADMIN_USERNAME=管理员用户名
ADMIN_PASSWORD_HASH=管理员密码哈希
COOKIE_SECURE=false
```

修改后执行：

```bash
systemctl restart personal-blog-backend
```

`personal-blog-daily-learning.service` 里的 `TimeoutStartSec=12min` 只影响定时执行器，不影响前台按钮的 `test` 请求。它比每日问答 AI 请求的 600 秒稍长，给启动、解析和落库留出余量。

### 展馆 OSS 配置与迁移记录

- 展馆海报和 Logo 上传使用 `MEDIA_STORAGE_DRIVER=oss`；其他业务的上传仍遵循各自现有实现。
- 当前展馆 Bucket 为 `ranjl-gallery-prod-1`，地域为北京，Endpoint 为 `https://oss-cn-beijing.aliyuncs.com`；公开图片基地址为 `https://ranjl-gallery-prod-1.oss-cn-beijing.aliyuncs.com`。
- OSS 跨域来源已验证 `https://ranjl.cn`、`https://www.ranjl.cn` 和 `http://127.0.0.1:5175`，读取方法为 GET/HEAD。密钥仅保存在本地与生产 `backend/.env`，生产文件权限为 600。
- 同一 Bucket 按环境分目录：本地 `OSS_OBJECT_PREFIX=personal-blog/dev`，生产 `OSS_OBJECT_PREFIX=personal-blog/prod`。海报分别存入对应前缀下的 `gallery/poster/`，Logo 存入 `gallery/logo/`；修改配置后重启后端。此配置仅决定新上传路径，历史图片需要复制并更新数据库中的完整 URL。
- 两地人物按姓名匹配图片，保留各自人物档案；本地测试人物不能同步覆盖线上正式人物。删除旧对象前，必须确认数据库和业务 JSON 数据已无引用；删除需单独授予限定旧目录的 `oss:DeleteObject` 权限，上传权限不包含删除权限。
- 2026-09-23：已完成环境目录分离并更新两地数据库。本地 9 张油画海报使用 `dev` 目录；线上使用同款 9 张油画及新增的布鲁克油画，共 10 张，使用 `prod` 目录。布鲁克人物档案保留，新图源文件为 `web/public/gallery/museum/brook.webp`；`dev` 中也保存了该素材，但未新增或覆盖本地人物档案。两地数据库保持独立。
- 原共享目录 `personal-blog/gallery/poster/` 中本次替换的 19 个旧对象已删除：删除前检查两地数据库和业务 JSON 均无引用，删除后逐个确认返回 `404 NoSuchKey`，并核对当前 19 条海报引用的图片内容哈希均正确。此次分目录替换按用户要求未新增备份。
- 生产后端当前版本：`/opt/personal_blog/releases/backend-20260923234026/backend`。之前 OSS 迁移留下的环境配置及海报新旧地址映射备份位于 `/opt/personal_blog/backups/gallery-oss-20260923222455/`，该目录含敏感配置，只限服务器管理员访问；本次发布未新增备份。
- `scripts/gallery/migrate_portraits_to_oss.py --force` 会覆盖匹配人物的现有海报；线上已有正式海报时，不应重复执行该命令。当前线上迁移已完成，后续直接在后台上传图片即可。


### Nginx 配置

文件：

```text
/etc/nginx/sites-available/personal-blog-backend
```

当前前台路径规则如下。若 IP 和域名同时使用，`47.111.75.30` 必须独立作为
`listen 80 default_server` 的 `server_name`，不能和域名一起放进跳转到 HTTPS 域名的
server 块；`/api/`、`/uploads/` 和 `/admin/` 的原有规则必须保留：

```nginx
location = / {
    return 301 /web/;
}

location = /web {
    return 301 /web/;
}

# 文章、专题和短动态详情由后端返回带 metadata 的 Vue HTML 外壳。
# API 服务地址按实际 systemd 监听地址调整。
location ~ ^/web/(articles|series|notes)/[^/]+/?$ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location = /robots.txt {
    proxy_pass http://127.0.0.1:8000;
}

location = /sitemap.xml {
    proxy_pass http://127.0.0.1:8000;
}

location = /feed.xml {
    proxy_pass http://127.0.0.1:8000;
}

location /web/ {
    alias /var/www/personal_blog/web-current/;
    try_files $uri /web/index.html;
}

location / {
    return 404;
}
```

如果服务器上已经有单独的 `/api/` 反向代理段，通用接口保持 120 秒。只有
`/api/v1/daily-learning/test` 和 `/api/v1/daily-learning/run-now` 会同步等待上游 AI
生成结果，需要单独放宽到 600 秒，避免一次性生成大量问答时先被 nginx 返回
`504 Gateway Time-out`。生产服务器已经按这个要求调整过时，请保持一致。

参考写法如下，放在通用 `location ^~ /api/` 前面：

```nginx
location = /api/v1/daily-learning/test {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 10s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout 600s;
}

location = /api/v1/daily-learning/run-now {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 10s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout 600s;
}
```


前台正式入口固定为 `http://47.111.75.30/web/`。Vue Router 子路由也位于该前缀下，
例如文章列表为 `/web/articles`、关于页面为 `/web/about`。根路径只负责跳转，
不再直接提供前台文件。详情页的 HTML 外壳由后端读取 `WEB_DIST_DIR/index.html` 后注入
canonical、Open Graph 和 JSON-LD；静态资源仍由 Nginx 提供。RSS 位于 `/feed.xml`
（页脚兼容入口为 `/api/feed.xml`），站点地图位于 `/sitemap.xml`。

修改后执行：

```bash
nginx -t
systemctl reload nginx
```

### 后端 systemd 服务配置

文件：

```text
/etc/systemd/system/personal-blog-backend.service
```

修改后执行：

```bash
systemctl daemon-reload
systemctl restart personal-blog-backend
```

### 前台地图配置

这是本地构建配置，文件位置：

```text
web/.env.production.local
```

修改后重新打包并上传 `web.tar.gz`。只重启服务器不会让前端构建配置生效。

### 前后台 API 地址

当前前后台默认使用 `/api/v1`，不需要额外修改。生产环境不要配置成 `127.0.0.1:8000`。

## 7. 重启和日志命令

### 每日问答定时器

首次部署每日问答功能时，先生成加密主密钥：

```bash
/opt/personal_blog/.venv/bin/python -c \
  "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

把输出写入 `/opt/personal_blog/backend/.env`：

```env
DAILY_LEARNING_ENCRYPTION_KEY=<刚生成的完整密钥>
```

然后安装并启动定时器：

```bash
cp /opt/personal_blog/backend/deploy/systemd/personal-blog-daily-learning.service \
  /etc/systemd/system/
cp /opt/personal_blog/backend/deploy/systemd/personal-blog-daily-learning.timer \
  /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now personal-blog-daily-learning.timer
systemctl restart personal-blog-backend
```

检查状态：

```bash
systemctl status personal-blog-daily-learning.timer --no-pager
systemctl list-timers personal-blog-daily-learning.timer --no-pager
journalctl -u personal-blog-daily-learning.service -n 100 --no-pager
```

部署后功能默认关闭。登录管理后台“每日问答”页面，保存 AI 配置并测试成功后再启用。

### 重启后端

```bash
systemctl restart personal-blog-backend
```

### 查看后端状态

```bash
systemctl status personal-blog-backend --no-pager
```

### 查看后端错误日志

```bash
journalctl -u personal-blog-backend -n 100 --no-pager
```

### 查看 Nginx 错误日志

```bash
tail -n 100 /var/log/nginx/error.log
```

### 检查所有服务

```bash
systemctl is-active personal-blog-backend
systemctl is-active nginx
systemctl is-active mysql
systemctl is-active redis-server
```

四行都显示 `active` 表示正常。

## 8. 绝对不要删除的生产数据

```text
/opt/personal_blog/backend/.env
/opt/personal_blog/backend/data/site_settings.json
/data/personal_blog/uploads
MySQL 中的 personal_blog 数据库
```

发布时只切换版本目录，不要删除这些生产数据。

## 9. 一句话记忆

```text
本地构建三个项目
-> 生成三个 tar.gz
-> 上传到服务器 /tmp
-> 解压到 releases 新目录
-> 后端复制旧 .env 和 data
-> 执行数据库迁移
-> 切换 current 软链接
-> 确认前台从 /web/ 访问
-> 重启后端并刷新浏览器
```

## 10. 2026-09-23 完整发布与清理记录

- 前台、管理后台和后端统一发布为 `20260923234026`，当前目录由原有三个稳定软链接指向；包含展馆更新、OSS 环境分离和本地代码清理。
- 修正后台生产构建的 `/admin/` 基路径、前台默认头像与氛围背景的 `/web/` 路径，后台空表单不再请求不存在的默认头像。
- 上传前记录发布包及每个文件的 SHA-256；解压后及旧版本删除后逐项校验。生产 `.env`、业务 JSON 和展馆人物/海报引用与发布前一致，数据库迁移版本为 `20260913_01`，本次未产生新的数据库迁移。
- 本地前后台 lint/build 通过；后端沿用本轮清理已通过的 51 项测试。线上检查覆盖首页、文章、专题、短动态、关于、留言板、大屏、后台登录、公共 API、RSS 和站点地图。展馆 10 张 OSS 海报解码成功，7 个 GLB 载入成功，桌面漫游、暂停退出及手机人物档案检查通过。
- 已删除 85 个旧发布目录、6 个已完成的迁移临时文件、3 个本次部署临时目录，总计约 828.38 MiB。两个 releases 根目录只保留当前后端、前台、后台各一版。
- 删除前检查旧目录未被运行进程引用；删除后校验当前文件哈希、生产配置、业务 JSON、海报引用和服务状态。数据库、上传目录、OSS 正式素材、运行环境和已有备份保留。
- 本地发布清单与浏览器验收报告分别位于系统临时目录 `personal-blog-deploy-20260923234026` 和 `blog-deploy-qa`。旧发布目录已清理，不能再通过切回旧软链接回滚；后续发布应先验收再清理。

## 11. 人物分类配置的升级要求

迁移 `20260924_01` 新增 `gallery_chapters` 表及人物 `chapter_id`。发布此功能时须同步更新后端、前台和管理后台，并在新后端启动前使用其运行环境执行 `alembic -c backend/alembic.ini upgrade head`（仓库根目录执行，数据库连接使用目标环境配置）。迁移只初始化一次默认分类和已有角色归属，保留原人物资料、海报及展位顺序；之后由后台“3D 展厅 → 人物分类标签”维护。

此功能已于 2026-09-24 随三个项目同步发布，线上迁移版本为 `20260924_01`；第 10 节保留为历史记录。

## 12. 2026-09-24 完整发布记录

- 前台、管理后台、后端统一发布为 `20260924154109`，包括夜航关于页和展馆人物分类；三个稳定软链接已切换到各自对应的新版本目录。
- 前后台完整 lint/build 通过，展馆后端 9 项测试通过。生产构建分别使用 `/web/`、`/admin/`，未上传本地 `.env`、业务 data、上传文件或虚拟环境。
- 发布包及解压文件 SHA-256 全量校验通过；生产 `.env`、业务 JSON、展馆人物姓名和海报引用在切换前后哈希一致。迁移从 `20260913_01` 升级至 `20260924_01`，线上保留 10 位人物并初始化 3 个分类。
- 后端、Nginx、MySQL、Redis 均 active，Nginx 配置检查及依赖检查通过。公开前台、关于页、展馆、后台登录、健康接口、个人资料、展馆接口、RSS 和 sitemap 均返回 200；入口 JS/CSS 可访问，新关于页背景哈希与本地产物一致。
- 浏览器确认线上关于页读取正式资料及 7 个项目，背景正常、无横向溢出且未捕获 error/warn；后台登录表单正常显示。未通过后台修改任何正式内容。
- 展馆浏览器首次命中历史 HTML 缓存并加载旧入口脚本；使用本次 release 查询参数重新读取后，确认入口脚本与当前构建一致，序厅、3 个接口分类及章节切换正常。服务器前后台首页正文与本地构建逐字节一致；曾访问旧版本的浏览器需 Ctrl+F5 强制刷新。
- 保留上一版 `20260923234026` 的三个发布目录，未执行旧版本清理。新迁移为新增表和可空列，紧急切回旧代码时保留新增数据库结构，不自动执行 downgrade。
- 本次清单、哈希及版本切换状态保存在本机系统临时目录 `personal-blog-deploy-20260924154109`。验收后清理本次传输压缩包，生产数据及旧版本目录保留。
