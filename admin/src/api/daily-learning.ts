import { request } from "./http";
import type {
  DailyLearningRun,
  DailyLearningSettings,
  DailyLearningSettingsPayload,
  DailyLearningTestResult,
} from "../types/daily-learning";

export function fetchDailyLearningSettings() {
  return request<DailyLearningSettings>({ url: "/daily-learning/settings", method: "GET" });
}

export function updateDailyLearningSettings(payload: DailyLearningSettingsPayload) {
  return request<DailyLearningSettings>({ url: "/daily-learning/settings", method: "PUT", data: payload });
}

export function testDailyLearningAI() {
  return request<DailyLearningTestResult>({
    url: "/daily-learning/test",
    method: "POST",
    timeout: 70000,
  });
}

export function runDailyLearningNow() {
  return request<DailyLearningRun>({ url: "/daily-learning/run-now", method: "POST" });
}

export function fetchDailyLearningRuns(limit = 20) {
  return request<{ items: DailyLearningRun[]; total: number }>({
    url: "/daily-learning/runs",
    method: "GET",
    params: { limit },
  });
}
