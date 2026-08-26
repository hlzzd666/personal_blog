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
Push-Location admin
npx vue-tsc -b
npx vite build --base=/admin/
Pop-Location

tar -czf admin.tar.gz -C admin/dist .
```

生成：

```text
D:\codex-test\personal_blog\admin.tar.gz
```

后台必须使用 `--base=/admin/`，否则线上后台可能白屏。

### 2.3 打包 Python 后端

```powershell
tar -czf backend.tar.gz `
  --exclude='backend/.env' `
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
前台：http://47.111.75.30/web/
后台：http://47.111.75.30/admin/login
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
REDIS_URL=redis://127.0.0.1:6379/0
ADMIN_USERNAME=管理员用户名
ADMIN_PASSWORD_HASH=管理员密码哈希
COOKIE_SECURE=false
```

修改后执行：

```bash
systemctl restart personal-blog-backend
```

### Nginx 配置

文件：

```text
/etc/nginx/sites-available/personal-blog-backend
```

当前前台路径规则如下。`/api/`、`/uploads/` 和 `/admin/` 的原有规则必须保留：

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
    try_files $uri $uri/ /web/index.html;
}

location / {
    return 404;
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
