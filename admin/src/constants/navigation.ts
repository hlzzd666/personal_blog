export const adminNavigation = [
  { label: "控制台", to: "/", icon: "DataBoard", group: "workspace" },
  { label: "文章管理", to: "/articles", icon: "Document", group: "content" },
  { label: "分类与标签", to: "/article-taxonomy", icon: "CollectionTag", group: "content" },
  { label: "专题管理", to: "/series", icon: "Collection", group: "content" },
  { label: "短动态", to: "/notes", icon: "ChatLineSquare", group: "content" },
  { label: "每日问答", to: "/daily-learning", icon: "MagicStick", group: "content" },
  { label: "3D 展厅", to: "/gallery", icon: "View", group: "content" },
  { label: "媒体资源", to: "/media", icon: "Picture", group: "content" },
  { label: "关于我", to: "/about", icon: "User", group: "site" },
  { label: "站点设置", to: "/site-settings", icon: "Setting", group: "site" },
] as const;

export const adminNavigationGroups = [
  { label: "工作台", key: "workspace" },
  { label: "内容管理", key: "content" },
  { label: "站点管理", key: "site" },
] as const;
