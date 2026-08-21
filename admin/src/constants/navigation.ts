export const adminNavigation = [
  { label: "控制台", to: "/", icon: "DataBoard", group: "workspace" },
  { label: "文章管理", to: "/articles", icon: "Document", group: "content" },
  { label: "媒体资源", to: "/media", icon: "Picture", group: "content" },
  { label: "关于我", to: "/about", icon: "User", group: "site" },
  { label: "站点设置", to: "/site-settings", icon: "Setting", group: "site" },
] as const;

export const adminNavigationGroups = [
  { label: "工作台", key: "workspace" },
  { label: "内容管理", key: "content" },
  { label: "站点管理", key: "site" },
] as const;
