# 展馆资源来源

## 当前实时船长舱

建筑由 `web/src/gallery/MuseumRoom.ts` 创建，不再加载旧版整船 GLB。地板纹理由 Canvas 生成，运行时只加载以下三张建筑贴图：

| 资源 | 用途 | 来源 |
| --- | --- | --- |
| `flagship/materials/walnut-color.jpg` | 胡桃木颜色 | Image2 API 从批准的主视角图提取 |
| `flagship/materials/walnut-normal.png` | 胡桃木微表面 | 由颜色图估算法线，非实物扫描 |
| `flagship/materials/brass-color.jpg` | 黄铜颜色 | 程序纹理，随机种子 61 |

重建脚本为 `scripts/gallery/prepare_materials.py`，只输出上述三张图片及来源记录。主视角与胡桃木参考、提示词、生成记录保留在 `artifacts/gallery/reference/perspective/` 和 `walnut/`。

## 展品与人物

独立展品模型见 [展品来源](artifacts/ASSET_SOURCES.md)，梅利号来源见 [模型来源](../models/ASSET_SOURCES.md)。第三方原始下载、导入后的 Blender 文件与许可均保留。

`museum/` 中的章节与人物油画为非官方同人插画；`collection-interior.webp` 是当前实时场景截图，其第三方模型许可见展品来源。各图片的同名 JSON 记录素材来源。

## 已退役资源

已移除旧整船 GLB、旧海面图片、帆布/柚木贴图、未使用的粗糙度和黄铜法线、旧序厅背景，以及被第三方展品替代的自建草帽、果实、和道制作链。现有动态路径图标、字体子集、模型加载失败时的备用几何继续保留。
