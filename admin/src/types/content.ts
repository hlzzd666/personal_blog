import type { Article } from "./article";

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

export type SeriesPayload = Pick<
  Series,
  "slug" | "title" | "description" | "cover_image_url" | "sort_order"
>;

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

export type NotePayload = Pick<
  Note,
  "slug" | "content_markdown" | "tags" | "external_url" | "published_at"
>;

export type DashboardStats = {
  article_count: number;
  series_count: number;
  note_count: number;
  total_views: number;
  total_likes: number;
  top_articles: Article[];
  recent_articles: Article[];
};

export type TaxonomyItem = {
  id: number;
  name: string;
  sort_order: number;
  article_count: number;
  created_at: string;
  updated_at: string;
};

export type TaxonomyPayload = Pick<TaxonomyItem, "name" | "sort_order">;

export type ArticleTaxonomy = {
  categories: TaxonomyItem[];
  tags: TaxonomyItem[];
};
