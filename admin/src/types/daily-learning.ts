export type DailyLearningSettings = {
  enabled: boolean;
  publish_time: string;
  ai_base_url: string;
  ai_model: string;
  api_key_configured: boolean;
  generation_instructions: string;
  tags: string[];
  timezone: string;
  updated_at: string;
};

export type DailyLearningSettingsPayload = Pick<
  DailyLearningSettings,
  "enabled" | "publish_time" | "ai_base_url" | "ai_model" | "generation_instructions" | "tags"
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
