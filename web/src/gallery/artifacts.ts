/** 前台策展记录；第三方模型署名与设定参考分开记录，不标称官方模型。 */
type ModelCredit = {
  title: string; author: string; authorUrl: string; modelUrl: string;
  license: string; licenseUrl: string; changes: string;
};
export type MuseumArtifact = {
  id: string; title: string; subtitle: string; description: string;
  features: string[]; source: string; x: number; z: number; width: number; depth: number; height: number; plinthHeight?: number;
  modelCredit?: ModelCredit;
  /** 长形刀类沿舱室深度陈列，展签仍朝向入口。 */
  sideDisplay?: boolean;
  /** 侧向长形展品的水平朝向；用于让入口视线看到完整刀身。 */
  displayYaw?: number;
};
export const logoCredit: ModelCredit = {
  title: 'One Piece logo', author: 'eriklys', authorUrl: 'https://sketchfab.com/eriklys',
  modelUrl: 'https://sketchfab.com/3d-models/one-piece-logo-dd8815b7dba6496daac409b036c9e980',
  license: 'CC BY 4.0', licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
  changes: '已调整尺寸与位置，并合并同材质网格。',
};
export const artifacts: MuseumArtifact[] = [
  { id: 'straw-hat', title: '路飞的草帽', subtitle: '一顶草帽，一个约定', x: 0, z: -5.55, width: 1.8, depth: 1.6, height: 2.05, plinthHeight: 1.38,
    description: '香克斯交给路飞的草帽，承载着再次相见的约定。展品保留宽帽檐、圆顶与红色帽带，让这件旅途中的信物成为前舱的中心。',
    features: ['浅麦色宽圆帽檐', '低圆顶，环绕一周的红色帽带', '简洁的无系绳造型，保留草帽的经典轮廓'], source: 'https://one-piece.com/character/monkey_d_luffy/index.html',
    modelCredit: { title: "Luffy's Straw hat", author: 'Rayn_Snow', authorUrl: 'https://sketchfab.com/Rayn_Snow',
      modelUrl: 'https://sketchfab.com/3d-models/luffys-straw-hat-ca7a5a97ec934b2984bd0ce28a392cae',
      license: 'CC BY-NC 4.0 · 仅限非商业使用', licenseUrl: 'https://creativecommons.org/licenses/by-nc/4.0/',
      changes: '已调整尺寸与位置，保留原始造型和贴图。' } },
  { id: 'den-den-mushi', title: '电话虫', subtitle: '来自大海另一端的声音', x: -3.15, z: -6.0, width: 1.65, depth: 1.45, height: 2.5,
    description: '《海贼王》世界中的通讯生物。这里采用普通电话虫的形态：软体身体、长眼柄、螺旋壳，以及装在壳上的听筒与拨号盘。',
    features: ['浅绿色身体，独立伸出的眼柄', '螺旋壳与黑色电话听筒', '正面拨号盘；不是屠魔令使用的金色电话虫'], source: 'https://one-piece.com/figure/o1351/index.html' },
  { id: 'log-pose', title: '记录指针', subtitle: '在伟大航路辨认方向', x: 3.15, z: -5.45, width: 1.65, depth: 1.45, height: 2.35,
    description: '普通指南针无法指引伟大航路的航程，记录指针通过记录岛屿的磁气带领航海者前进。本展品展示单针腕式结构。',
    features: ['透明球罩中悬置方向针', '圆形底座与棕色腕带', '单针版本，与新世界使用的三针版本区分'], source: 'https://one-piece.com/story/alabasta/index.html' },
  { id: 'gum-gum', title: '橡胶果实', subtitle: '故事开始时的紫色果实', x: -3.15, z: -3.65, width: 1.65, depth: 1.45, height: 2.25,
    description: '以故事早期“橡胶果实”的名称陈列。紫色球状果体、遍布表面的旋涡纹，以及卷曲果柄，是这件展品最鲜明的外观特征。',
    features: ['紫色近球形果体', '遍布表面的旋涡纹样', '顶端弯卷的果柄；展签不展开后续身世剧透'], source: 'https://one-piece.com/news/70093/index.html',
    modelCredit: { title: 'Gomu Gomu No Mi', author: 'Kris', authorUrl: 'https://sketchfab.com/popit228fm',
      modelUrl: 'https://sketchfab.com/3d-models/gomu-gomu-no-mi-2d08af4cad6b4748b48de2fcb1aa0200',
      license: 'CC BY 4.0', licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
      changes: '已调整尺寸与位置，并合并同材质网格。' } },
  { id: 'wado', title: '和道一文字', subtitle: '索隆与古伊娜的约定', x: -2.8, z: -1.25, width: 1.05, depth: 2.1, height: 1.43, plinthHeight: .55, sideDisplay: true, displayYaw: Math.PI * 110 / 180,
    description: '古伊娜的刀后来由索隆继承，也承载着两人成为世界第一剑豪的约定。出鞘长刀与白色刀鞘并陈，可同时观察刀身、柄卷与刀镡。',
    features: ['白色刀鞘与浅色柄卷', '圆形刀镡与柄卷的菱形间隙', '出鞘刀身与白鞘分层并陈，由深色木架承托'], source: 'https://one-piece.com/anime/19/index.html',
    modelCredit: { title: 'Katana - Wado Ichimonji', author: 'NRiza', authorUrl: 'https://sketchfab.com/NRiza21',
      modelUrl: 'https://sketchfab.com/3d-models/katana-wado-ichimonji-6199b50ce733431fbedb7a5bf2fa9c1b',
      license: 'CC BY 4.0', licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
      changes: '新增双层刀架，调整尺寸与陈列朝向并合并网格；保留原始刀、鞘造型与贴图。' } },
  { id: 'going-merry', title: '黄金梅利号', subtitle: '一起出发的伙伴', x: 3.15, z: -2.05, width: 1.85, depth: 2.0, height: 2.65,
    description: '草帽一伙航程中的重要伙伴。羊首船头、船帆与甲板，记录着伙伴们在大海上共同生活的日常。沿着展台观察船体，重温这艘船陪伴大家启航的时光。',
    features: ['羊首造型的船头', '草帽一伙旗帜与帆装', '独立低台展示，可从侧面观察船体'], source: 'https://one-piece.com/character/going_merry/index.html' },
];
export const posterStartZ = 3.4;
