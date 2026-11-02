# 普通图片 OSS 存储与迁移

- `POST /api/v1/media/images` 与展厅共用 `MEDIA_STORAGE_DRIVER` 配置。
- OSS 模式写入 `OSS_OBJECT_PREFIX/uploads/<随机文件名>`，失败返回 502，不回退到服务器磁盘。
- 本地模式仍写入 `UPLOAD_DIR`。PDF 简历接口不受本次图片迁移影响。
- 媒体资源页同时展示本地和本站 OSS 目录，可按来源与引用状态筛选、预览和复制链接。OSS 列举失败时降级显示已引用对象，未知大小/时间显示“未知”，禁用 OSS 清理。

## 迁移步骤

在项目根目录执行 `python -m backend.scripts.migrate_images_to_oss <阶段> --manifest <清单绝对路径>`：

1. `prepare`：上传图片并逐张通过公开 URL 下载，校验 SHA-256；生成清单，保留本地文件。
2. `apply`：短暂停止 API 写入，备份待修改字段和站点设置，更新图片引用；完成后恢复设置文件属主并启动 API。
3. 配置旧 `/uploads/<文件名>` 地址到清单中 OSS 地址的精确重定向，并通过 `nginx -t` 校验；不重定向简历目录。
4. 验证网站图片、新上传、旧链接都正常。
5. `delete`：检查引用已更新，重新验证全部本地/OSS 哈希后，仅删除清单内图片。

清单和引用备份含实际数据，只能保存在服务器受限备份目录，不提交 Git。恢复时可依清单从 OSS 下载文件，并按引用备份恢复字段；不要回退到仍只支持本地上传的旧代码。

## 2026-11-02 执行记录

普通图片接口已发布为 OSS 模式；49 张图片共 2,853,051 字节迁移到 `personal-blog/prod/uploads/`。引用备份、清单及部署前配置位于 `/opt/personal_blog/backups/`，文件名包含 `images-oss-20261102`。Nginx 精确重定向配置为 `/etc/nginx/snippets/personal-blog-images-oss.conf`。

## OSS 媒体管理权限

RAM 用户：`personal-blog-oss-uploader`。将 `docs/oss-media-management-policy.json` 作为附加自定义策略绑定到该用户，保留已有上传/读取权限。列举只允许 `personal-blog/prod/` 前缀；删除只允许本应用图片目录。无需授予 `AliyunOSSFullAccess`。

`GET /api/v1/media/files` 返回来源、清单完整性、警告及引用位置。`DELETE /api/v1/media/files/unreferenced?storage=local|oss` 默认仍为本地；OSS 清理要求完整清单，服务端重新检查引用，只允许清理本应用上传格式的图片。未知用途的其他对象不参与清理。清理错误后页面刷新，避免展示已部分清理的旧列表。
