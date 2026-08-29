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
  category_id: number | null;
  tag_ids: number[];
  series_id: number | null;
  series_order: number | null;
  created_at: string;
};

export type ArticlePayload = Omit<Article, "id" | "created_at" | "updated_at"> & {
  updated_at?: string | null;
};

export type ArticleList = {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
};
