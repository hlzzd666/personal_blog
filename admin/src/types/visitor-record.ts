export type VisitorRecord = {
  id: number;
  ip: string;
  city: string | null;
  region: string | null;
  country: string | null;
  page_path: string;
  referer: string | null;
  user_agent: string | null;
  device_type: string;
  visited_at: string;
};

export type VisitorRecordListResponse = {
  items: VisitorRecord[];
  total: number;
  page: number;
  page_size: number;
  total_visits: number;
  today_visits: number;
  unique_ips: number;
};

export type VisitorRecordFilters = {
  page: number;
  page_size: number;
  ip?: string;
  city?: string;
  page_path?: string;
  visited_from?: string;
  visited_to?: string;
};
