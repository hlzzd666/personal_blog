export type MediaReference = {
  source: string;
  label: string;
};

export type MediaFileItem = {
  filename: string;
  relative_path: string;
  url: string;
  content_type: string;
  media_type: "image" | "resume" | "other" | string;
  size: number;
  modified_at: string;
  referenced: boolean;
  references: MediaReference[];
};

export type MediaListResponse = {
  items: MediaFileItem[];
  total: number;
  used_count: number;
  unused_count: number;
  total_size: number;
  unused_size: number;
};

export type MediaCleanupResponse = {
  deleted_count: number;
  deleted_size: number;
  deleted_files: string[];
};
