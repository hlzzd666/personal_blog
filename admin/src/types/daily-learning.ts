export type DailyLearningSettings = {
  enabled: boolean;
  publish_time: string;
  schedule_type: "daily" | "weekly" | "monthly";
  schedule_weekday: number | null;
  schedule_day: number | null;
  ai_base_url: string;
  ai_model: string;
  api_key_configured: boolean;
  generation_topic: string;
  system_prompt: string;
  generation_instructions: string;
  generation_count: number;
  question_label: string;
  answer_label: string;
  article_title_template: string;
  article_slug_template: string;
  article_summary_template: string;
  author: string;
  series_id: number | null;
  series_title: string | null;
  category_id: number | null;
  category: string | null;
  tag_ids: number[];
  tags: string[];
  max_attempts: number;
  retry_delays_minutes: number[];
  timezone: string;
  updated_at: string;
};

export type DailyLearningSettingsPayload = Omit<
  DailyLearningSettings,
  "api_key_configured" | "series_title" | "category" | "timezone" | "updated_at"
> & {
  api_key?: string | null;
};

export type DailyLearningRunStatus = "pending" | "running" | "succeeded" | "failed";

export type DailyLearningRun = {
  id: number;
  run_date: string;
  scheduled_for: string;
  status: DailyLearningRunStatus;
  attempt_count: number;
  last_error: string | null;
  next_retry_at: string | null;
  article_id: number | null;
  article_slug: string | null;
  article_title: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DailyLearningTestResult = {
  ok: boolean;
  model: string;
  question_count: number;
  first_question: string;
  latency_ms: number;
};
