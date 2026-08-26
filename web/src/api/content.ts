import { request } from "./http";
import type { Article } from "./articles";

export type Series = {
  id: number;
  slug: string;
  title: string;
  description: string;
  cover_image_url: string | null;
  sort_order: number;
  article_count: number;
  created_at: string;
  updated_at: string;
};

export type SeriesDetail = Series & { articles: Article[] };

export type Note = {
  id: number;
  slug: string;
  content_markdown: string;
  tags: string[];
  external_url: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type NoteList = {
  items: Note[];
  total: number;
  page: number;
  page_size: number;
};

export function fetchSeries() {
  return request<{ items: Series[]; total: number }>({ url: "/series", method: "GET" });
}

export function fetchSeriesDetail(slug: string) {
  return request<SeriesDetail>({ url: `/series/${encodeURIComponent(slug)}`, method: "GET" });
}

export function fetchNotes(params: Record<string, string | number | undefined> = {}) {
  return request<NoteList>({ url: "/notes", method: "GET", params });
}

export function fetchNote(slug: string) {
  return request<Note>({ url: `/notes/${encodeURIComponent(slug)}`, method: "GET" });
}
