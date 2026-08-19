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
  tags: string[];
  category: string;
  created_at: string;
};

export type ArticlePayload = Omit<Article, "id" | "created_at" | "updated_at" | "views" | "likes"> & {
  updated_at?: string | null;
  views?: number;
  likes?: number;
};

export type ArticleList = {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
};

export function fetchArticles(params: Record<string, string | number | undefined> = {}) {
  return request<ArticleList>({ url: "/articles", method: "GET", params });
}

export function fetchArticle(slug: string) {
  return request<Article>({ url: `/articles/${encodeURIComponent(slug)}`, method: "GET" });
}

export function likeArticle(slug: string) {
  return request<{ likes: number }>({ url: `/articles/${encodeURIComponent(slug)}/like`, method: "POST" });
}
