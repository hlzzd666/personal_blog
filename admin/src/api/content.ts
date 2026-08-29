import { request } from "./http";
import type {
  ArticleTaxonomy,
  DashboardStats,
  Note,
  NotePayload,
  Series,
  SeriesPayload,
  TaxonomyItem,
  TaxonomyPayload,
} from "../types/content";

export function fetchArticleTaxonomy() {
  return request<ArticleTaxonomy>({ url: "/article-taxonomy", method: "GET" });
}

export function createArticleCategory(payload: TaxonomyPayload) {
  return request<TaxonomyItem>({ url: "/article-taxonomy/categories", method: "POST", data: payload });
}

export function updateArticleCategory(id: number, payload: TaxonomyPayload) {
  return request<TaxonomyItem>({ url: `/article-taxonomy/categories/${id}`, method: "PUT", data: payload });
}

export function deleteArticleCategory(id: number) {
  return request<{ id: number }>({ url: `/article-taxonomy/categories/${id}`, method: "DELETE" });
}

export function createArticleTag(payload: TaxonomyPayload) {
  return request<TaxonomyItem>({ url: "/article-taxonomy/tags", method: "POST", data: payload });
}

export function updateArticleTag(id: number, payload: TaxonomyPayload) {
  return request<TaxonomyItem>({ url: `/article-taxonomy/tags/${id}`, method: "PUT", data: payload });
}

export function deleteArticleTag(id: number) {
  return request<{ id: number }>({ url: `/article-taxonomy/tags/${id}`, method: "DELETE" });
}

export function fetchSeries() {
  return request<{ items: Series[]; total: number }>({ url: "/series", method: "GET" });
}

export function createSeries(payload: SeriesPayload) {
  return request<Series>({ url: "/series", method: "POST", data: payload });
}

export function updateSeries(id: number, payload: SeriesPayload) {
  return request<Series>({ url: `/series/${id}`, method: "PUT", data: payload });
}

export function deleteSeries(id: number) {
  return request<{ id: number }>({ url: `/series/${id}`, method: "DELETE" });
}

export function fetchNotes(params: Record<string, string | number | undefined> = {}) {
  return request<{ items: Note[]; total: number; page: number; page_size: number }>({
    url: "/notes",
    method: "GET",
    params,
  });
}

export function createNote(payload: NotePayload) {
  return request<Note>({ url: "/notes", method: "POST", data: payload });
}

export function updateNote(id: number, payload: NotePayload) {
  return request<Note>({ url: `/notes/${id}`, method: "PUT", data: payload });
}

export function deleteNote(id: number) {
  return request<{ id: number }>({ url: `/notes/${id}`, method: "DELETE" });
}

export function fetchDashboardStats() {
  return request<DashboardStats>({ url: "/dashboard/stats", method: "GET" });
}
