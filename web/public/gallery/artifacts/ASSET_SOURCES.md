# 主题展品模型与素材来源

2026-09-23 核对。第三方模型的作者、原模型页和许可直接来自用户提供的 GLB 文件 `asset.extras`，不是根据文件名推测。文件来源为用户下载的四个 GLB；原始下载文件保留不变。展馆中的模型均不标称为《海贼王》官方制作资产。

## 本次导入的第三方模型

| 展品 / 发布文件 | 原始下载文件 | 原模型与作者 | 作者账号 | 许可 |
| --- | --- | --- | --- | --- |
| 路飞的草帽 / `straw-hat.glb` | `luffys_straw_hat.glb` | [Luffy's Straw hat](https://sketchfab.com/3d-models/luffys-straw-hat-ca7a5a97ec934b2984bd0ce28a392cae)，[Rayn_Snow](https://sketchfab.com/Rayn_Snow) | `Rayn_Snow` | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)；须署名、链接许可并注明修改；仅限非商业使用 |
| 橡胶果实 / `gum-gum.glb` | `gomu_gomu_no_mi.glb` | [Gomu Gomu No Mi](https://sketchfab.com/3d-models/gomu-gomu-no-mi-2d08af4cad6b4748b48de2fcb1aa0200)，[Kris](https://sketchfab.com/popit228fm) | `popit228fm` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)；须署名、链接许可并注明修改 |
| 和道一文字 / `wado.glb` | `katana_-_wado_ichimonji.glb` | [Katana - Wado Ichimonji](https://sketchfab.com/3d-models/katana-wado-ichimonji-6199b50ce733431fbedb7a5bf2fa9c1b)，[NRiza](https://sketchfab.com/NRiza21) | `NRiza21` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)；须署名、链接许可并注明修改 |
| 展馆标识 / `one-piece-logo.glb` | `one_piece_logo.glb` | [One Piece logo](https://sketchfab.com/3d-models/one-piece-logo-dd8815b7dba6496daac409b036c9e980)，[eriklys](https://sketchfab.com/eriklys) | `eriklys` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)；须署名、链接许可并注明修改 |

原模型 ID 分别为 `ca7a5a97ec934b2984bd0ce28a392cae`、`2d08af4cad6b4748b48de2fcb1aa0200`、`6199b50ce733431fbedb7a5bf2fa9c1b`、`dd8815b7dba6496daac409b036c9e980`。作者账号为原 GLB 提供的 Sketchfab 主页账号，显示名称可能与账号不同。

### 陈列与处理

- 草帽：采用下载模型的无系绳造型；统一单位、居中并对齐底面，保留原始网格与 512 像素贴图。
- 橡胶果实：统一单位、居中并对齐底面；按唯一材质将 17 个网格合为 1 个，保留原始贴图。
- 和道一文字：保留原始刀、鞘网格、法线和三张 2048 × 2048 PBR 贴图；刀在上、鞘在下，刀柄朝左，正面朝 GLB +Z。新增深色木质双层支架与四处毡垫；删除两个未使用的 UV 通道，按材质合并为 3 个绘制批次；底面对齐 GLB Y=0，X/Z 居中，贴图内嵌。
- 展馆标识：统一单位与中心；将 83 个网格按 6 种材质合并，保留外形和色彩，陈列在前舱两扇窄高舷窗之间的海青色实墙上。

草帽、果实与标识的导入脚本为 `scripts/gallery/import_sketchfab_models.py`，和道一文字为 `scripts/gallery/import_wado.py`；处理后的 Blender 工作文件及报告位于 `artifacts/gallery/model/imported-{id}.blend` 与同目录的 `imported-{id}-report.json`。

以上资源在对应道具展签中提供可见署名与许可；展馆标识的署名位于二维馆藏页底部“展馆素材来源”区域。本文件记录更完整的原文件与处理来源。

序厅背景 `../museum/collection-interior.webp` 是包含上述模型的本地场景截图，沿用此处列明的作者和许可；画面含 CC BY-NC 4.0 草帽模型，仅限非商业使用。截图未替代交互式场景或文字控件。

### 原始下载文件校验值

| 原始文件 | SHA-256 |
| --- | --- |
| `luffys_straw_hat.glb` | `35faf7c8394d5b75593e54ed466e3f6308508cb7fa9fcf815db272a627aa6cac` |
| `gomu_gomu_no_mi.glb` | `8c139be953680015d03082732d6dfc21aab4087161bd2c8b5c500d687dc7b6e2` |
| `katana_-_wado_ichimonji.glb` | `4d093eecb8b6512d9828f644de136a024d8a41fe10d01091ca1dbfbfe3a360e8` |
| `one_piece_logo.glb` | `059142bd7d99ba7a529892cc393429ba41d55233cdbdf218400575f4c11bde01` |

## 继续使用的本项目自建模型

2026-09-23 用 Blender 4.2.23 LTS 制作的非官方同人复原，未使用第三方网格或纹理。

| 文件 | 造型与材质 | 生成器 |
| --- | --- | --- |
| `den-den-mushi.glb` | 蜗牛软体、眼睑、壳体、听筒、嵌壳拨号盘与卷线 | `scripts/gallery/build_snail_compass.py` |
| `log-pose.glb` | 单针玻璃球、木质底座、闭合腕带、扣针与缝线 | 同上 |

此前自建的草帽、和道一文字与橡胶果实已由上表的第三方模型替换，旧生成脚本、源文件及预览已清理。当前第三方原始下载、导入脚本、处理后的 Blender 源文件和许可记录继续保留。

黄金梅利号继续使用 `web/public/models/ASSET_SOURCES.md` 已记录的用户提供模型。
设定参考链接见 `web/src/gallery/artifacts.ts`。自建源文件、离线预览和纹理源图位于 `artifacts/gallery/model/`。
