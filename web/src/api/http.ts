import axios from "axios";

export type ApiEnvelope<T> = {
  code: number;
  status: number;
  message: string;
  data: T;
  request_id: string;
};

export type ApiErrorPayload = {
  code: number;
  status: number;
  message: string;
  data?: {
    detail?: unknown;
  } | null;
  request_id?: string;
};

export class ApiError extends Error {
  code: number;
  status: number;
  detail: unknown;
  requestId?: string;

  constructor(payload: ApiErrorPayload) {
    super(payload.message || "request failed");
    this.name = "ApiError";
    this.code = payload.code ?? payload.status ?? 500;
    this.status = payload.status ?? payload.code ?? 500;
    this.detail = payload.data?.detail;
    this.requestId = payload.request_id;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const http = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: true,
});

http.interceptors.request.use((config) => {
  const headers = config.headers;
  if (!headers.get("X-Request-Id")) {
    headers.set("X-Request-Id", crypto.randomUUID());
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiEnvelope<unknown>;
    if (payload.code !== 200 || payload.status !== 200) {
      throw new ApiError({
        code: payload.code,
        status: payload.status,
        message: payload.message,
        data:
          payload.data && typeof payload.data === "object" && "detail" in (payload.data as Record<string, unknown>)
            ? { detail: (payload.data as Record<string, unknown>).detail }
            : null,
        request_id: payload.request_id,
      });
    }
    return response;
  },
  (error) => {
    if (axios.isAxiosError(error) && error.response?.data) {
      return Promise.reject(new ApiError(error.response.data as ApiErrorPayload));
    }
    return Promise.reject(
      new ApiError({
        code: 500,
        status: 500,
        message: error instanceof Error ? error.message : "network error",
        data: null,
      }),
    );
  },
);

export async function request<T>(config: Parameters<typeof http.request>[0]) {
  const response = await http.request<ApiEnvelope<T>>(config);
  return response.data.data;
}
