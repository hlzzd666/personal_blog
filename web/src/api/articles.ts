import { request } from "./http";

export type Article = {
  id: number;
  slug: string;
  title: string;
  summary: string;
  content_markdown: string;
  cover_image_url: string | null;
  is_repost: boolean;
  author: string;
  source_url: string | null;
  published_at: string | null;
  updated_at: string;
  views: number;
  likes: number;
  liked_by_current_visitor: boolean;
  tags: string[];
  category: string;
  created_at: string;
};

export type ArticlePayload = Omit<Article, "id" | "created_at" | "updated_at" | "views" | "likes" | "liked_by_current_visitor"> & {
  updated_at?: string | null;
  views?: number;
  likes?: number;
};

export type ArticleCountItem = {
  name: string;
  count: number;
};

export type ArticleMonthCount = {
  key: string;
  count: number;
};

export type ArticleListStats = {
  categories: ArticleCountItem[];
  tags: ArticleCountItem[];
  months: ArticleMonthCount[];
};

export type ArticleList = {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
  stats: ArticleListStats;
};

export function fetchArticles(params: Record<string, string | number | undefined> = {}) {
  return request<ArticleList>({ url: "/articles", method: "GET", params });
}

export function fetchArticle(slug: string) {
  return request<Article>({ url: `/articles/${encodeURIComponent(slug)}`, method: "GET" });
}

export function likeArticle(slug: string) {
  return request<{ likes: number; liked_by_current_visitor: boolean }>({ url: `/articles/${encodeURIComponent(slug)}/like`, method: "POST" });
}
