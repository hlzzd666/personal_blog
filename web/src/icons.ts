export const iconGroups = [
  { id: "navigation", label: "导航" },
  { id: "content", label: "内容" },
  { id: "action", label: "操作" },
  { id: "status", label: "状态" },
] as const;

export type IconGroup = (typeof iconGroups)[number]["id"];

export const iconCatalog = [
  { name: "home", label: "首页", motif: "草帽", usage: "主导航首页与返回首页", group: "navigation" },
  { name: "articles", label: "文章", motif: "悬赏令卷轴", usage: "文章列表、最新文章和阅读入口", group: "navigation" },
  { name: "series", label: "专题", motif: "记录指针", usage: "专题列表和连续阅读航线", group: "navigation" },
  { name: "notes", label: "动态", motif: "电话虫", usage: "短动态、消息和简短更新", group: "navigation" },
  { name: "gallery", label: "展厅", motif: "狮首帆船", usage: "3D 展厅和人物档案入口", group: "navigation" },
  { name: "about", label: "关于", motif: "伙伴旗帜", usage: "关于我、个人资料和团队信息", group: "navigation" },
  { name: "search", label: "搜索", motif: "黄铜望远镜", usage: "全站搜索与内容查找", group: "content" },
  { name: "toc", label: "目录", motif: "折叠海图", usage: "文章目录和章节导航", group: "content" },
  { name: "tag", label: "标签", motif: "船锚行李牌", usage: "内容标签与主题筛选", group: "content" },
  { name: "archive", label: "归档", motif: "日志宝箱", usage: "时间归档与历史内容", group: "content" },
  { name: "like", label: "喜欢", motif: "绳结红心", usage: "文章点赞与喜欢状态", group: "action" },
  { name: "share", label: "分享", motif: "新闻鸟", usage: "分享文章或复制链接", group: "action" },
  { name: "comment", label: "评论", motif: "电话虫气泡", usage: "评论、回复和讨论入口", group: "action" },
  { name: "favorite", label: "收藏", motif: "罗盘勋章", usage: "收藏内容和稍后阅读", group: "action" },
  { name: "previous", label: "上一项", motif: "左向绳箭", usage: "上一篇、上一页和上一个项目", group: "action" },
  { name: "next", label: "下一项", motif: "右向绳箭", usage: "下一篇、下一页和下一个项目", group: "action" },
  { name: "top", label: "回到顶部", motif: "桅杆上箭头", usage: "长页面快速返回顶部", group: "action" },
  { name: "external", label: "外部链接", motif: "出航罗盘", usage: "打开站外链接或新窗口", group: "action" },
  { name: "download", label: "下载", motif: "货箱下箭头", usage: "下载简历、附件或媒体", group: "action" },
  { name: "location", label: "位置", motif: "生命卡坐标", usage: "地图、位置和距离信息", group: "content" },
  { name: "time", label: "时间", motif: "黄铜怀表", usage: "发布时间、阅读时长和日期", group: "content" },
  { name: "views", label: "浏览", motif: "望远镜之眼", usage: "浏览次数和可见性", group: "content" },
  { name: "success", label: "成功", motif: "勾选航旗", usage: "保存、发布或操作成功", group: "status" },
  { name: "warning", label: "警告", motif: "风暴船钟", usage: "错误、风险和需要注意的状态", group: "status" },
] as const satisfies readonly {
  name: string;
  label: string;
  motif: string;
  usage: string;
  group: IconGroup;
}[];

export type IconName = (typeof iconCatalog)[number]["name"];

export function iconUrl(name: IconName) {
  return `${import.meta.env.BASE_URL}icons/${name}.png`;
}
