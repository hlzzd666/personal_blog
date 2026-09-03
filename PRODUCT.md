# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

面向浏览个人博客、文章与兴趣内容的公开访客，以及负责维护站点内容的单一管理员。

## Product Purpose

这是一个将个人写作、技术实践和兴趣展示整合在一起的个人博客。公开访客可以阅读文章、专题、短动态与个人资料，并通过 3D 人物展厅沉浸式浏览《海贼王》人物档案；管理员通过独立后台维护内容。

## Positioning

站点以抽象航海日志为统一语言，把长期写作记录与可漫游的兴趣档案空间组织为同一段航程。

## Operating Context

- 前台以 PC 与移动 Web 阅读为主；3D 展厅首版只提供 PC 第一人称漫游，其他设备使用二维降级列表。
- 后台由单一管理员通过 Session 登录维护内容，图片沿用站点媒体上传与清理能力。

## Capabilities and Constraints

- 前端使用 Vue 3、TypeScript 与 Vite，后端使用 FastAPI、SQLAlchemy、Alembic 与 MySQL。
- 3D 展厅使用 Three.js WebGLRenderer，最多维护 40 位人物，公开页面只展示已启用人物。
- 展厅首版不包含人物模型、音频、移动端漫游、WebGPU、小地图、瞬移或后台 3D 预览。
- 《海贼王》人物资料、Logo 与正式海报由管理员后续维护；仓库只提供无版权图片依赖的程序化占位海报。

## Brand Commitments

- 前台采用抽象航海日志风格，核心色彩与材质来自深海蓝、黄铜金、珊瑚红、航线和档案标记。
- 用户文案使用中文，功能名称清晰直接。

## Evidence on Hand

- 现有前台已实现航海日志视觉、文章、专题、短动态与关于我页面。
- 现有后台已具备 Session/CSRF 鉴权、图片上传和媒体引用清理能力。

## Product Principles

- 沉浸效果服务于内容浏览，不以特效牺牲可用性。
- 公开阅读保持匿名，内容写入只向管理员开放。
- 复用现有站点能力，首版不提前建设未验证的复杂系统。
- 明确提供加载、空内容、错误与不支持设备状态。

## Accessibility & Inclusion

保留清晰键盘焦点、减少动态偏好支持和二维降级内容；不支持 3D 的设备仍可读取人物资料。
