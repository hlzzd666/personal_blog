import { request } from "./http";
import type { Article, ArticlePayload, ArticleList } from "../types/article";

export function fetchManageArticles(params: Record<string, string | number | boolean | undefined> = {}) {
  return request<ArticleList>({ url: "/articles/manage", method: "GET", params });
}

export function createArticle(payload: ArticlePayload) {
  return request<Article>({ url: "/articles", method: "POST", data: payload });
}

export function updateArticle(id: number, payload: ArticlePayload) {
  return request<Article>({ url: `/articles/${id}`, method: "PUT", data: payload });
}

export function deleteArticle(id: number) {
  return request<{ id: number }>({ url: `/articles/${id}`, method: "DELETE" });
}
