---
name: "个人航海日志"
description: "以航海器材清单组织个人写作与兴趣档案的前台视觉系统"
colors:
  deep-sea: "#07131f"
  deep-sea-system: "#071c29"
  night-panel: "#0e2938"
  chart-ground: "#dce8e9"
  canvas-panel: "#f8f0dc"
  ink: "#123247"
  muted-ink: "#536b72"
  canvas-ink: "#f6ebd4"
  muted-canvas: "#b8c9c7"
  brass-dark: "#754a08"
  brass-bright: "#f0c162"
  coral-dark: "#a92f2a"
  coral-bright: "#ff7868"
  focus-gold: "#ffd36f"
  sea-glass: "#87d2c7"
typography:
  display:
    fontFamily: "ZCOOL KuaiLe, Noto Sans SC, sans-serif"
    fontSize: "clamp(3.6rem, 7vw, 5.8rem)"
    fontWeight: 400
    lineHeight: 0.96
    letterSpacing: "0"
  headline:
    fontFamily: "ZCOOL KuaiLe, Noto Sans SC, sans-serif"
    fontSize: "clamp(2rem, 4vw, 3.5rem)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "0"
  body:
    fontFamily: "Noto Sans SC, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.85
    letterSpacing: "0"
  label:
    fontFamily: "Noto Sans SC, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 800
    lineHeight: 1.65
    letterSpacing: "0"
  technical:
    fontFamily: "IBM Plex Mono, monospace"
    fontSize: "0.72rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0"
rounded:
  control: "4px"
  panel: "6px"
  dialog: "8px"
  circular: "50%"
spacing:
  xs: "0.45rem"
  sm: "0.85rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  section: "4rem"
components:
  ocean-icon:
    size: "24px"
    width: "24px"
    height: "24px"
  navigation-icon:
    size: "20px"
    width: "20px"
    height: "20px"
  filter-control:
    backgroundColor: "transparent"
    textColor: "{colors.muted-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.85rem"
    height: "2.55rem"
  filter-control-selected-light:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.canvas-panel}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.85rem"
    height: "2.55rem"
  filter-control-selected-dark:
    backgroundColor: "{colors.brass-bright}"
    textColor: "{colors.deep-sea-system}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.85rem"
    height: "2.55rem"
  catalog-panel-light:
    backgroundColor: "{colors.canvas-panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "clamp(2rem, 5vw, 4.2rem)"
  catalog-panel-dark:
    backgroundColor: "{colors.night-panel}"
    textColor: "{colors.canvas-ink}"
    rounded: "{rounded.panel}"
    padding: "clamp(2rem, 5vw, 4.2rem)"
---

## Overview

**Creative North Star: "航海器材清单"**

前台把个人博客理解为一份持续编写的航海日志，而不是一组泛用内容卡片。深海蓝构成稳定、安静的工作环境，黄铜像刻度和仪器读数一样提供方向，珊瑚红只标记返回、风险与关键动作，帆布白和浅海图灰承载需要细读的记录面。航线、坐标、档案划分和器物轮廓负责叙事，内容仍然是视觉层级的中心。

新增的 24 枚多色图标是这套世界的功能语言。每一枚先传达导航、内容、操作或状态，再通过草帽、记录指针、电话虫、船锚和罗盘等器物留下记忆点。它们保留同一位插画者般的深海描边、帆布白分隔边和轻微不对称，带有手作感，但不表现为 emoji、亮面应用贴纸或角色肖像。

图标航海图是该系统的展示面：首屏左侧负责命名和规格说明，右侧让六枚核心航向沿虚线航路展开；其后的分类控制和三列器材账册用于检索。这个构图属于图标展示页，不应机械复制到所有页面；可复用的是材料、层级、图标组件、状态和响应式原则。

**Key Characteristics:**

- 深海工作台与帆布记录面并存，并跟随系统浅色/深色主题切换。
- 黄铜用于刻度与激活，珊瑚红用于航标、返回和警示，强调色保持稀缺。
- 标题有手写航海日志气质，正文保持清晰、克制和可长时间阅读。
- 细边框、方正小圆角、坐标网格与虚线航路代替通用浮层卡片装饰。
- 复杂图标轮廓坚持 raster-first，统一通过 `OceanIcon` 使用。

## Colors

颜色按“环境、记录面、读数、航标”分工；浅深主题改变明暗关系，但不改变语义。

### Primary

- **深海工作台（`deep-sea` / `deep-sea-system`）：** 全站默认环境与图标页深色背景。大面积使用时保持安静，避免再叠加大范围高饱和蓝。
- **夜间记录板（`night-panel`）：** 深色主题中的目录面板，与背景靠明度而非强描边分层。

### Secondary

- **黄铜刻度（`brass-dark` / `brass-bright`）：** 用于器物名、航线、激活控制和深色主题导航反馈。浅色主题使用较深版本确保文字对比，深色主题使用明亮版本。
- **聚焦金（`focus-gold`）：** 全局键盘焦点及深海导航的高可见反馈，不作为大面积背景。

### Tertiary

- **珊瑚航标（`coral-dark` / `coral-bright`）：** 返回入口、警示、代码标识和少量关键动作。它是方向信号，不是页面主色。
- **海玻璃（`sea-glass`）：** 搜索和海洋仪表中的辅助分隔、输入边界与低优先级状态。

### Neutral

- **浅海图底（`chart-ground`）：** 浅色系统主题的页面底色，可叠加低对比度 32px 坐标网格。
- **帆布记录面（`canvas-panel`）：** 目录、日志和需要集中阅读的浅色面板。
- **墨水正文（`ink`）与旧墨水（`muted-ink`）：** 浅色主题的标题、正文和辅助说明。
- **帆布正文（`canvas-ink`）与雾面帆布（`muted-canvas`）：** 深色主题的主文字和次要文字。

**The Signal Scarcity Rule.** 黄铜和珊瑚只标记方向、状态或关键元数据；一个区域内不能让两者同时大面积竞争。

**The Paired Theme Rule.** 浅深主题必须成对检查，不可只反转背景；文字、边框、面板、激活态和图标阴影都要分别适配。

## Typography

**Display Font:** ZCOOL KuaiLe（后备为 Noto Sans SC 与系统无衬线）  
**Body Font:** Noto Sans SC（后备为系统无衬线）  
**Label/Mono Font:** IBM Plex Mono（后备为等宽字体，用于坐标、日期和技术标识）

**Character:** 展示字体提供航海日志的手写个性，正文与功能标签由 Noto Sans SC 保证中文可读性。等宽字体只承担读数和标识，不用于大段正文。

### Hierarchy

- **Display：** 仅用于页面主标题；尺寸使用 `typography.display`，短行、紧行高，图标航海图主标题限制在约 7 个汉字宽度。
- **Headline：** 用于主分区标题；尺寸使用 `typography.headline`，不与页面标题争夺第一层级。
- **Body：** 使用 `typography.body` 承担介绍和阅读内容，展示页说明行宽控制在约 34rem。
- **Label：** 使用 `typography.label` 承担筛选、图标用途和导航；依靠字重建立清晰度，不使用负字距。
- **Technical：** 使用 `typography.technical` 展示图标名称、坐标或文件规格；与自然语言标签并置时退居次层。

**The Two-Voice Rule.** 每个界面只保留“日志展示字 + 清晰功能字”两种主要声音；等宽字是仪表读数，不是第三套正文风格。

## Layout

全站以前台内容为中心，页面水平内边距使用 `clamp()` 在窄屏和宽屏间连续收敛。图标航海图最大内容宽度为 1260px，桌面首屏采用约 0.78:1.22 的左右两栏，文案与六枚核心航向相互平衡；目录面板内部使用三列账册，而不是等大贴纸卡片墙。

在 980px 以下，首屏改为单列，核心航向保持最多 38rem 的居中区域，账册降为两列；在 680px 以下，目录面板收紧为单列，工具栏改为纵向，筛选按钮共享可用宽度。固定格式元素必须锁定宽高或纵横比，图标、筛选控制和圆形底座不能因标签或加载状态发生布局位移。

主要节奏来自 `spacing.md`、`spacing.lg`、`spacing.xl` 与 `spacing.section`。页内大分区之间保留明确停顿，账册条目内部保持紧凑，以支持反复扫描。

**The Ledger Before Cards Rule.** 可比较的内容优先用分栏账册、细分隔线和连续记录面组织；只有真正独立的对象或工具才使用卡片。

**The Surface-Specific Hero Rule.** “左文右六枚核心航向”只属于图标系统展示页；后续页面沿用世界观时，应根据任务重组信息层级，而非复制首屏模板。

## Elevation & Depth

系统以色调分层和细边框为主，阴影只提供记录面离开工作台的轻微深度，以及图标在交互时的触感。浅色目录面使用 `0 1.3rem 3rem rgba(16, 43, 52, 0.12)`；深色目录面使用 `0 1.5rem 3.4rem rgba(0, 0, 0, 0.28)`。基础图标使用低幅 drop-shadow，悬停或聚焦时才增加阴影和饱和度。

半透明导航通过背景模糊与极淡底边在滚动时显现，不把每个导航项做成浮起的胶囊。坐标网格、黄铜虚线航路和圆形图标底座提供空间线索，但不得遮盖内容。

**The Flat-at-Rest Rule.** 列表条目和控制在静止状态保持平面；明显阴影只用于整块记录面、对话层或交互反馈。

## Shapes

形状语言由小圆角记录板、细线分隔、圆形仪表底座与不规则器物轮廓组成。控制使用 `rounded.control`，主要面板使用 `rounded.panel`，对话层可使用 `rounded.dialog`；圆形只用于图标底座、坐标点和仪表语义，不把普通文字按钮普遍胶囊化。

图标外轮廓来自透明 PNG，不以 CSS、图标字体或临时 SVG 重画复杂形状。每枚图标保持深海色 keyline、帆布白分隔边、清晰透明边缘和一致留白，确保在浅色与深色表面都可辨认。

**The Instrument Geometry Rule.** 几何形状必须解释功能：圆形表示仪表或定位，小圆角表示记录面和控制，虚线表示航路；不添加无语义的装饰圆角容器。

## Components

### OceanIcon

- **资产：** 24 枚 256 × 256 RGBA 透明 PNG，分为导航、内容、操作、状态四组；复杂轮廓采用 raster-first。
- **接口：** 只通过 `OceanIcon` 的受控 `name`、`size`、`decorative` 和 `label` 属性使用，不直接拼接文件路径，也不复制目录元数据。
- **尺寸：** 常规界面显示范围为 20–64px；导航使用 `navigation-icon`。72px 与 88px 仅用于图标目录的样本和核心航向展示，不是常规控件尺寸。
- **布局：** 图片固定为 1:1，显式设置宽高并禁止 flex 收缩；使用 `object-fit: contain` 保留完整轮廓和安全留白。
- **语义：** 图标与可见文字并用时保持装饰性；图标单独承担功能时设置 `decorative=false` 并提供准确 `label`。未知或不在目录中的名称不得绕过类型约束。
- **状态：** 默认只有轻微投影；可交互容器悬停或键盘聚焦时可增加投影、轻微上移和极小旋转，但不能改变盒子尺寸。

### Navigation

导航是透明或半透明的固定顶栏，品牌在左，主要入口在右；窄屏允许换行并转为上下排列。图标与文字始终并列，悬停、当前页与键盘聚焦由文字颜色和 2px 底部航线共同表达。图标航海图使用 system-surface 变体，使导航背景、文字和激活色跟随系统主题。

### Filter Controls

分类筛选是一组紧凑的分段控制，而不是一排独立胶囊。默认态透明、使用次要文字色，选中态分别使用 `filter-control-selected-light` 或 `filter-control-selected-dark`；`aria-pressed` 是视觉与语义状态的共同来源。键盘焦点使用 3px 珊瑚色内描边，不能只依赖颜色变化。

### Catalog Panel and Ledger

目录面板在浅深主题中分别使用 `catalog-panel-light` 与 `catalog-panel-dark`。内部条目共享连续的顶部、底部和列分隔线；每项由圆形图标底座、中文名称、器物母题、用途与技术名称组成。圆形底座只托住图标，不成为嵌套卡片。

### Footer

页脚延续深海背景与帆布文字，浅色/system-surface 场景切换为相应记录面。链接保持纯文本或“图标 + 文字”，悬停和聚焦只改变为当前主题的黄铜或珊瑚信号色；移动端改为纵向排列。

### Motion and Theme Behavior

目录筛选使用短促的透明度与纵向位移过渡；图标以 180–240ms 的滤镜和位移变化回应交互，导航显隐属于较慢的环境动作。系统启用 `prefers-reduced-motion: reduce` 时，必须关闭列表过渡、图标位移、导航动画与平滑滚动；颜色和描边反馈仍需保留。主题使用 `prefers-color-scheme`，不设置与系统偏好冲突的局部假主题。

## Do's and Don'ts

### Do:

- **Do** 从 `iconCatalog` 选择图标，并通过 `OceanIcon` 渲染；常规界面尺寸保持在 20–64px。
- **Do** 在按钮和导航中优先使用“图标 + 可见中文文字”，仅在语义已被广泛理解且有可访问名称时单独使用图标。
- **Do** 同时验证浅色和深色主题中的文字对比、透明边缘、描边、投影、焦点和选中态。
- **Do** 用海图网格、细边框、黄铜刻度和少量珊瑚航标建立世界感，让内容和操作保持清晰。
- **Do** 为所有固定格式图标和控件定义稳定尺寸，并让 980px、680px 两级布局自然降列。
- **Do** 在 reduced-motion 模式下保留状态颜色与焦点轮廓，同时移除位移、旋转、列表过渡和页面平滑滚动。

### Don't:

- **Don't** 用 CSS、emoji、图标字体或临时 SVG 仿制这套复杂器物轮廓；新增同类图标必须延续 raster-first 与透明 PNG 资产流程。
- **Don't** 把 72px/88px 的展示尺寸带入导航、按钮或正文元数据，也不要让图标因 flex 或文字长度被压缩变形。
- **Don't** 把目录做成等大贴纸卡片墙、在卡片内继续嵌套卡片，或给每个平面条目添加悬浮阴影。
- **Don't** 大面积混用黄铜与珊瑚，或引入主导性的紫色、米色、单一蓝色渐变来稀释深海、帆布、黄铜、珊瑚的材料关系。
- **Don't** 让图标替代标签、错误文案或状态说明；功能理解始终优先于母题彩蛋。
- **Don't** 在 reduced-motion 模式中保留悬停位移、旋转、平滑滚动或自动显隐动画。
