import axios from "axios";
export class ApiError extends Error {
    constructor(payload) {
        super(payload.message || "request failed");
        Object.defineProperty(this, "code", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "status", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "detail", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "requestId", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.name = "ApiError";
        this.code = payload.code ?? payload.status ?? 500;
        this.status = payload.status ?? payload.code ?? 500;
        this.detail = payload.data?.detail;
        this.requestId = payload.request_id;
    }
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
function readCookie(name) {
    const encodedName = `${encodeURIComponent(name)}=`;
    return (document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith(encodedName))
        ?.slice(encodedName.length) ?? "");
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
http.interceptors.response.use((response) => {
    const payload = response.data;
    if (payload.code !== 200 || payload.status !== 200) {
        throw new ApiError({
            code: payload.code,
            status: payload.status,
            message: payload.message,
            data: payload.data && typeof payload.data === "object" && "detail" in payload.data
                ? { detail: payload.data.detail }
                : null,
            request_id: payload.request_id,
        });
    }
    return response;
}, (error) => {
    if (axios.isAxiosError(error) && error.response?.data) {
        const requestUrl = String(error.config?.url ?? "");
        if (error.response.status === 401 &&
            !requestUrl.includes("/auth/login") &&
            !requestUrl.includes("/auth/me")) {
            window.dispatchEvent(new CustomEvent("personal-blog-admin-unauthorized"));
        }
        return Promise.reject(new ApiError(error.response.data));
    }
    return Promise.reject(new ApiError({
        code: 500,
        status: 500,
        message: error instanceof Error ? error.message : "network error",
        data: null,
    }));
});
export async function request(config) {
    const response = await http.request(config);
    return response.data.data;
}
