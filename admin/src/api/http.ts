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

// 与后端 _STATUS_MESSAGES 保持一致，用于响应体不是标准错误信封时的兜底文案。
const HTTP_STATUS_MESSAGES: Record<number, string> = {
  400: "请求参数有误",
  401: "请先登录",
  403: "没有权限执行该操作",
  404: "请求的资源不存在",
  405: "请求方法不允许",
  409: "数据冲突",
  413: "上传内容过大",
  415: "不支持的文件类型",
  422: "请求参数不正确",
  429: "请求过于频繁，请稍后重试",
  500: "服务器内部错误，请稍后重试",
  502: "上游服务异常，请稍后重试",
  503: "服务暂时不可用，请稍后重试",
};

function httpStatusFallback(statusCode: number) {
  return HTTP_STATUS_MESSAGES[statusCode] ?? `请求失败（HTTP ${statusCode}）`;
}

// 页面侧统一取错：优先回显服务端返回的具体 message，非接口错误时退回本地文案。
export function resolveErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError && error.message) {
    return error.message;
  }
  return fallback;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const CSRF_COOKIE_NAME = "personal_blog_admin_csrf";
const CSRF_HEADER_NAME = "X-CSRF-Token";
const CSRF_METHODS = new Set(["post", "put", "patch", "delete"]);

function createRequestId() {
  const randomUuid = globalThis.crypto?.randomUUID;
  if (typeof randomUuid === "function") {
    return randomUuid.call(globalThis.crypto);
  }
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

export const http = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: true,
});

function readCookie(name: string) {
  const encodedName = `${encodeURIComponent(name)}=`;
  return (
    document.cookie
      .split(";")
      .map((item) => item.trim())
      .find((item) => item.startsWith(encodedName))
      ?.slice(encodedName.length) ?? ""
  );
}

http.interceptors.request.use((config) => {
  const headers = config.headers;
  if (!headers.get("X-Request-Id")) {
    headers.set("X-Request-Id", createRequestId());
  }
  const method = config.method?.toLowerCase() ?? "get";
  const csrfToken = readCookie(CSRF_COOKIE_NAME);
  if (CSRF_METHODS.has(method) && csrfToken && !headers.get(CSRF_HEADER_NAME)) {
    headers.set(CSRF_HEADER_NAME, decodeURIComponent(csrfToken));
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiEnvelope<unknown> | undefined;
    if (!payload || typeof payload !== "object") {
      return response;
    }
    if (payload.code !== 200 || payload.status !== 200) {
      throw new ApiError({
        code: payload.code ?? payload.status ?? 500,
        status: payload.status ?? payload.code ?? 500,
        message: payload.message || httpStatusFallback(Number(payload.status) || 500),
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
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const requestUrl = String(error.config?.url ?? "");
        if (
          error.response.status === 401 &&
          !requestUrl.includes("/auth/login") &&
          !requestUrl.includes("/auth/me")
        ) {
          window.dispatchEvent(new CustomEvent("personal-blog-admin-unauthorized"));
        }
        const data = error.response.data as ApiErrorPayload | undefined;
        if (data && typeof data === "object" && typeof data.message === "string" && data.message) {
          return Promise.reject(new ApiError(data));
        }
        return Promise.reject(
          new ApiError({
            code: error.response.status,
            status: error.response.status,
            message: httpStatusFallback(error.response.status),
            data: null,
          }),
        );
      }
      const isTimeout = error.code === "ECONNABORTED";
      return Promise.reject(
        new ApiError({
          code: 0,
          status: 0,
          message: isTimeout ? "请求超时，请稍后重试" : "无法连接服务器，请确认后端服务已启动",
          data: null,
        }),
      );
    }
    return Promise.reject(
      new ApiError({
        code: 500,
        status: 500,
        message: error instanceof Error ? error.message : "请求失败，请稍后重试",
        data: null,
      }),
    );
  },
);

export async function request<T>(config: Parameters<typeof http.request>[0]) {
  const response = await http.request<ApiEnvelope<T>>(config);
  return response.data.data;
}
