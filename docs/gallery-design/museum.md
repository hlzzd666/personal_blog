# 船长的私人博物馆

## 范围与视觉依据

本说明只约束 `/gallery`。用户选定的船长舱概念图为视觉依据，生成图标识为 `exec-00fc56ea-a869-454d-b6c8-eed49013c8dc.png`（2026-09-22）。站点其他页面继续使用根目录 `DESIGN.md` 的航海日志规范。

序厅以独立舱室背景承载胡桃木、黄铜、宽舷窗和展柜氛围，标题、导航、搜索、全屏、人物展签、四章目录与罗盘均可独立交互。进入漫游后切换至 Three.js 实时封闭舱室；实时几何、光照和材质为功能重建，与概念图仍有差异，不属于逐像素或照片级复刻。

## 视觉与交互约束

- 深海底色 `#061017`、黄铜 `#c9a55c`、浅金 `#ead49a`、纸色 `#eee4ce` 和次要文字 `#bbb19c` 只作用于画廊。主按钮为方形黄铜铭牌，档案为浅纸面，避免把两者推广为全站组件。
- 大标题采用奶油色衬线字，正文和操作保持可读性。`Museum Serif` / `Museum Sans` 为本地 Noto Serif SC / Noto Sans SC 别名，位于 `web/src/gallery/fonts`，含两份 OFL 许可；400–700 可变字重和 Unicode 子集由 `fonts.css` 管理，无需 Google Fonts 网络请求。
- 顶栏在序厅和漫游中固定；四章为“序厅、东海群像、伟大航路、新世界”。章节关联只筛选已公开人物，未知姓名仍出现在全部馆藏。航海图志和经典瞬间共用同一份公开数据。
- 桌面支持鼠标视角、WASD/方向键、近距离 E/点击查看、Escape 暂停和返回序厅；详情使用原生 `dialog`。保留可见焦点、纸面深色焦点和减少动态偏好。
- 3D 需要至少 1024px、精细指针、WebGL2 和 Pointer Lock；小屏保留序厅，参观进入二维馆藏。650px 以下章节横向滚动、馆藏两列、详情单列。
- 保留 0～40 人容量、自动布展、碰撞、邻近最多 12 张海报纹理及资源释放。后端设置、排序、Session/CSRF、图片上传与权限契约不变，无新增 API 或数据库迁移。

## 素材与维护

| 本地素材 | 用途 | 来源记录 |
| --- | --- | --- |
| `web/public/gallery/museum/collection-interior.webp` | 当前实时场景的序厅背景截图 | 同名 `.webp.json` 与展品许可 |
| `web/public/gallery/museum/chapters.webp` | 四章场景图集 | 同名 `.webp.json` |
| `web/public/gallery/museum/portraits.webp` | 九位人物油画图集 | 同名 `.webp.json` |

章节与人物图集为 AI 生成的非官方同人插画；序厅背景为真实场景截图。各 JSON 记录来源、描述性 brief 与 WebP 处理方式，其中旧图集的 `prompt` 字段是来源摘要，不代表完整原始生成提示词。管理员海报优先，缺失或加载失败时才使用对应馆藏插画；未识别人物使用中性编目海报。图集裁切及姓名关联由 `web/src/gallery/curation.ts` 管理，替换图集时须同步裁切边界。

主要实现位于 `GalleryPage.vue`、`gallery-page.css`、`curation.ts`、`MuseumRoom.ts` 与 `GalleryScene.ts`；实时场景复用 `web/public/gallery/flagship/materials` 的材质。

## 主题道具与画像净空

前舱陈列六件《海贼王》主题物件，后舱为人物画像长廊。主题数据、展台位置与碰撞尺寸统一维护在 `web/src/gallery/artifacts.ts`；`ArtifactDisplays.ts` 提供展台和轻量备用造型，正式五件主题道具使用 `web/public/gallery/artifacts` 中的独立 GLB。目前草帽、果实、和道一文字使用用户下载的第三方模型，电话虫与记录指针为自建模型；梅利号沿用原有资产。参考来源支持设定说明，不表示模型是官方制作资产。

| 展品 | 外观识别点 | 设定参考 |
| --- | --- | --- |
| 路飞的草帽 | 麦色宽檐、低圆顶、红帽带 | [路飞人物页](https://one-piece.com/character/monkey_d_luffy/index.html) |
| 电话虫 | 眼柄、螺旋壳、听筒与拨号盘 | [电话虫资料](https://one-piece.com/figure/o1351/index.html) |
| 记录指针 | 单针球罩、圆形底座、腕带 | [阿拉巴斯坦篇](https://one-piece.com/story/alabasta/index.html) |
| 橡胶果实 | 紫色球体、球面旋涡、卷曲果柄 | [果实造型资料](https://one-piece.com/news/70093/index.html) |
| 和道一文字 | 白鞘、白柄卷、圆形刀镡 | [动画第 19 话](https://one-piece.com/anime/19/index.html) |
| 黄金梅利号 | 羊首、草帽旗帜、帆装与甲板 | [梅利号资料](https://one-piece.com/character/going_merry/index.html) |

道具前使用 E 或点击打开纸面展签，展示介绍、外观识别点和设定参考。关闭展签后恢复先前漫游状态；暂停时不显示重复提示。小地图用方点标示道具、圆点标示人物展位。二维馆藏底部同样提供六件道具的阅读入口，触屏和不支持 WebGL 的设备也可访问。

人物展位从 `posterStartZ = 3.4` 开始；旧书柜、桌椅、望远镜和船模柜不再位于画像前方。道具留在前舱，和道一文字位于左舷 `x=-2.8,z=-1.25` 的纵向低台，刀身向入口轻微偏转约 20°，中央草帽保持独立迎宾位；两侧 x=±1.6 的通道贯通至长廊，壁灯置于画像之间。展台尺寸同时供碰撞与射线交互使用，准星对准展签也可打开详情。梅利号优先加载已有 GLB；等待或失败时显示独立的羊首帆船备用造型。

道具按材质合批，保留静态阴影、半分辨率环境遮蔽与最多 12 张附近海报纹理。新增内容不引入后端接口、数据迁移或外部运行时依赖。

## 本地运行与验收

在仓库根目录启动前端：

```powershell
node node_modules/vite/bin/vite.js web --host 127.0.0.1 --port 5175
```

另一个终端执行回归（需可解析的 Playwright 与 Chrome）：

```powershell
$env:GALLERY_URL = 'http://127.0.0.1:5175'
node scripts/gallery/check_browser.cjs
```

未设置 `GALLERY_URL` 时脚本默认连接 `http://127.0.0.1:5173`。脚本拦截公开接口提供确定性数据，不依赖开发数据库；截图和 `browser-report.json` 默认写到系统临时目录 `gallery-museum-qa`，可通过 `GALLERY_QA_OUTPUT` 指定输出路径。

本次实现通过前端 lint/build、5 项后端 pytest，以及容量 0/1/12/40、碰撞、纹理上限与驱逐、资源释放、搜索、详情、章节、移动端和六类失败情形的浏览器回归。另已在阻断 Google Fonts/gstatic 后确认两套字体本地加载，1280×720 无页面横向溢出。这些结果证明已测流程和环境，不构成所有硬件性能或实时画面完全还原的承诺。

## 2026-09-23：入口遮挡、场景与性能修正

序厅内容和章节目录改为正常文档流中的 flex 布局，以视口高度为最小高度，并按视口高度收敛标题尺寸。内容放不下时允许少量纵向滚动；1920×912 下页面约高 946px，主按钮不会被章节目录覆盖。1920×912、1672×941、1440×900、1280×720、1024×768 和 390×844 六个视口均通过按钮可见性、点击命中、间距和无页面横向溢出检查。

实时舱室增加弧形胡桃木与黄铜拱肋、桌面海图、绿色绗缝座椅和折叠织物，并调亮木材、柔化日光。场景仍为风格化实时重建，与概念图的几何、光照和材质质感存在差异。

性能调整包括按材质合并舱室与船模几何（合并前统一为非索引几何）、使用 Box3 解析遮挡检测、缓存静态 PCF 阴影、半分辨率 12 采样环境遮蔽、约 210 万像素预算、DPR 上限 1.25，以及暂停时停止渲染。

同一台 RX 6600、Chrome、1920×912、15 人物数据及固定 8 秒移动路径的前后实测如下：

| 指标 | 调整前 | 调整后 |
| --- | ---: | ---: |
| 平均 FPS | 96.2 | 144.1 |
| 帧耗时 P95 | 34.7ms | 7.0ms |
| 导航计算平均耗时 | 28.38ms | 0.02ms |
| 平均 draw calls | 3677.89 | 206.03 |
| 渲染 CPU 平均耗时 | 6.73ms | 2.12ms |

复测使用 `node scripts/gallery/profile_browser.cjs`，沿用 `GALLERY_URL`，可通过 `GALLERY_PROFILE_LABEL` 标记报告；默认输出到系统临时目录 `gallery-museum-qa`。本轮 `before.json` / `after.json` 为上述数据来源，最终报告 `errors` 为空。结果限于该硬件与固定场景，不代表所有设备的帧率。

本轮前端 lint/build 和完整浏览器回归通过，包含六视口、0/1/12/40 人物容量、海报缓存驱逐、资源销毁及六类失败恢复；浏览器回归报告 `errors` 为空。

主题道具回归增加：六个展位及碰撞、双侧通道、画像中心与边缘九点视线净空、六件展品的 E 交互、实际页面展签打开与关闭后恢复控制、二维和手机展签、船模请求失败时保留备用造型。截图和报告仍写入上述临时目录；旧性能表只代表前一阶段，不作为新增道具后的测量结果。

2026-09-23 主题道具版已通过 `npm run lint:web`、`npm run build:web` 和上述浏览器回归。最终 `browser-report.json` 无运行时或 WebGL 错误。新增道具后的 `artifacts-final.json` 在同一 RX 6600 / Chrome / 1920×912 / 15 人物 / 8 秒固定路线记录平均 143.9 FPS、P95 帧耗时 7.0ms、平均 158.19 次绘制调用；只代表当前测试环境。导航编号已放在画框上方，不覆盖海报主体。生产构建仍有既有的超过 500kB 分包体积提示，未阻断构建。

## Blender 自建展品替换（历史阶段）

这一历史阶段曾将五件展品改为自建 GLB，总计约 7MB、212,332 个三角面、34 个材质批次。当前仅电话虫与记录指针继续使用自建模型；已被替换的草帽、果实、和道一文字的旧生成器、源文件和预览已清理。当前模型来源与可编辑文件以 `web/public/gallery/artifacts/ASSET_SOURCES.md` 为准。

运行时并行读取五件道具，按展台尺寸等比摆放，并移除对应备用造型；玻璃使用透明混合，不启用 transmission 附加渲染。草帽展台单独抬高到 1.3m，改善入口处被刀架遮住的视线。离开页面后完成的请求也会释放纹理、材质和几何。

当前保留的自建展品重建与校验（草帽、和道一文字、果实已改用第三方模型，旧生成器已清理；导入方式见后文）：

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/gallery/build_snail_compass.py
python scripts/gallery/validate_artifact_models.py
```

浏览器回归另外校验五个模型全部载入、备用几何完整替换、缩放后位于展台边界内，以及单件模型加载失败时其他展品正常。上述旧性能结果属于替换前版本，新模型结果另以 `authored-models.json` 记录。

2026-09-23 自建模型版通过 `npm run lint:web`、`npm run build:web`、GLB 结构与预算校验，以及完整浏览器回归；五件模型加载与替换、展台边界、画像净空、单件模型失败恢复均通过，回归报告 `errors` 为空。构建仍有既有的超过 500kB 分包提示。

同一 RX 6600 / Chrome / 1920×912 / 15 人物 / 8 秒固定路线实测：平均 144.1 FPS、平均帧耗时 6.94ms、帧耗时 P95 7.0ms、渲染 CPU 平均 2.92ms、平均 206.15 次绘制调用、场景 584,503 个三角面。性能报告 `errors` 为空；此结果只代表上述本机环境。最终性能、回归报告和真实网页模型截图拼图保存在 `artifacts/gallery/qa/authored-models.json`、`artifacts/gallery/qa/authored-models-browser-report.json` 与 `artifacts/gallery/qa/authored-models.png`。

## 2026-09-23：下载素材与展陈重设计（当前版本）

根据用户提供的四个 GLB，替换草帽、橡胶果实和和道一文字，并将立体 One Piece Logo 放在双窗之间的中央实墙。作者、许可、修改说明和原始文件校验值见 `web/public/gallery/artifacts/ASSET_SOURCES.md`；展签和二维馆藏也提供可见署名。草帽采用 CC BY-NC 4.0，仅限非商业使用。原文件保留于 `artifacts/gallery/model/downloads/`，处理后的可编辑源文件为 `imported-{id}.blend`。

视觉方向见 `collection-concept.png`：海青色墙面、胡桃木结构与浅色石质展台共同承托模型。草帽使用 1.38m 高圆台；和道一文字使用 0.55m 左舷纵向低台，出鞘刀身与刀鞘分层陈列，并以约 110° 世界 Y 旋转让入口视角完整看到刀身；展签抬高到低台上沿，漫游状态读出移到左上留白区，避免覆盖刀架或展签。中央地毯只承担迎宾动线，不再承托刀台。窄高舷窗、中央实墙和六盏展品射灯取代原先拥挤的前景灯饰。地板弱化纹理反差，人物海报仍从 z=3.4 起保持净空。

入口相机位置为 `(-0.35, 1.7, 2.8)`；宽屏视场角为 58°，窗口变窄时平滑扩大到最多 78°，保证左舷和道、中央草帽与右舷船模不被视锥裁切。序厅背景 `collection-interior.webp` 取自当前真实 Three.js 场景，来源与相机信息保存在同名 JSON；页面标题、按钮和章节目录仍为可访问的 HTML。概念图仅作为设计方向，实时画面不宣称摄影级或严格 1:1 还原。

本次入口预览已在最终侧向展位完成后重新渲染为 1920×1080 WebP；预览中不包含导航、提示层或交互控件，避免序厅继续展示旧的中央刀台构图。窄桌面实时漫游会缩小右上航图并留出船模上方净空。

四个下载文件经过单位和朝向统一、底面与中心校正、同材质合批。和道一文字保留三张原始 2048 贴图，并增加木质支架和毡垫。五件道具与 Logo 合计约 15.51MB；全部资源内嵌，未增加运行时依赖。模型失败时保留各自备用造型，Logo 失败时保留文字标识。

重建当前第三方资产时使用下面的命令；历史自建草帽、果实、刀剑脚本会覆盖当前文件，不能作为当前版本的整批重建入口：

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/gallery/import_sketchfab_models.py
blender --background --factory-startup --python-exit-code 1 --python scripts/gallery/import_wado.py
python scripts/gallery/validate_artifact_models.py
```

完整浏览器回归通过六视口、0/1/12/40 人物容量、五件模型替换与展台边界、Logo 位置、双侧通道、画像九点净空、E 交互、手机展签及署名、纹理驱逐与资源释放、单件模型和 Logo 的失败恢复；报告 `errors` 为空。验收文件位于系统临时目录 `gallery-redesign-qa`。

最终 `npm run lint:web`、`npm run build:web`、GLB 结构与预算校验及 `git diff --check` 均通过。新序厅背景另在 1440×900 和 390×844 复核：图片完整加载、主按钮可点击、无横向溢出、无前端异常。构建仍保留既有超过 500kB 的分包提示。浏览器自动化连接曾返回 `unsupported Codex auth method: apikey`，本轮验收使用本地 Playwright 与 Chrome；机械样式扫描的颜色和字号提示属于展馆既有局部样式及本轮明确采用的 3D 材料色。

`imported-redesign.json` 记录当前版本在 RX 6600 / Chrome / 1920×912 / 15 人物 / 8 秒固定路线的实测：平均 **143.3 FPS**，平均帧耗时 **6.98ms**、P95 **7.0ms**，渲染 CPU 平均 **3.01ms**、P95 **4.3ms**，平均 **197.63** 次绘制调用，场景 **578,615** 个三角面，无运行时或 WebGL 错误。此数据仅代表上述本机环境，前面的性能表保留为各历史阶段记录。

## 序厅画面挤压修正

用户截图中的拥挤来自全页 `object-fit: cover` 裁切，加上文案、巨型章节计数、竖向人物签和高底栏叠压画面。当前 `entry-stage` 将导览与图像分成两列；图像独立使用 16:9 画框和 `object-fit: contain`，按视口高度分配空间。人物签与全屏操作移到图片下方，重复计数删除，底栏缩为紧凑章节导航。900px 以下改为上下排列，阅读和键盘顺序与 DOM 一致。序厅顶栏恢复正常文档流，漫游仍保留固定顶栏。

`check_browser.cjs` 增加图片比例、文案分离与底栏不遮图断言，覆盖 1920×912、1672×941、1440×900、1280×720、1024×768、768×1024、390×844 和 375×667；8 个尺寸均无横向溢出，主按钮可见，原有参观、章节、详情和失败恢复回归通过。末次高度调整另复核桌面无多余纵向滚动。结果与截图位于系统临时目录 `gallery-entry-layout-qa`；布局扫描无发现，lint/build 通过，生产构建仅有既有大分包提示。

## 果实与梅利号自动旋转

实时漫游中的橡胶果实与梅利号以各自展台中心为轴，每 48 秒匀速转一圈，展台与铭牌固定。加载时按真实顶点计算旋转半径并约束尺寸，避免船头、船尾扫入通道；正式模型与加载失败时的备用造型都使用相同展示逻辑。暂停、离开页面、展品离开视野或启用系统减少动态偏好时停止旋转。复用已有渲染循环，阴影最多每秒更新 15 次。

旋转回归校验运行帧确实改变角度、暂停/减少动态/背向展品时角度不变，并采样整圈 24 个朝向验证真实顶点仍在展台边界内。前端 lint/build 与完整浏览器回归通过，报告位于系统临时目录 `gallery-rotation-qa`。

开启旋转后的 `rotating-displays.json` 在相同 RX 6600 / Chrome / 1920×912 / 15 人物 / 8 秒路线下记录 143.3 FPS，帧耗时 P95 7.0ms、渲染 CPU 平均 2.55ms，平均 215.45 次绘制调用；报告无运行时或 WebGL 错误。结果仅代表该测试设备与路线。

人物海报的数据库字段为 `gallery_characters.poster_url`，保存 URL；上传服务支持 `MEDIA_STORAGE_DRIVER=local|oss`。生产环境设置为 `oss` 后，展馆海报和 Logo 会写入阿里云 OSS，访问地址使用 `OSS_PUBLIC_BASE_URL`（可填 CDN 域名），本地 `backend/uploads` 仍作为开发环境和未切换环境的回退。图片地址只保存到数据库，OSS 对象和数据库需要一起备份。现有九位示例海报可用 `scripts/gallery/migrate_portraits_to_oss.py --force` 从 `portraits.webp` 裁切、上传并回写；脚本不会把密钥写入仓库。
