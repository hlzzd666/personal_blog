export type MediaReference = {
  source: string;
  label: string;
};

export type MediaFileItem = {
  storage: "local" | "oss";
  cleanup_eligible: boolean;
  filename: string;
  relative_path: string;
  url: string;
  content_type: string;
  media_type: "image" | "resume" | "other" | string;
  size: number | null;
  modified_at: string | null;
  referenced: boolean;
  references: MediaReference[];
};

export type MediaListResponse = {
  warnings: string[];
  oss_complete: boolean;
  upload_storage: "local" | "oss";
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
