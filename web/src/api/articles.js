import { request } from "./http";
export function fetchArticles(params = {}) {
    return request({ url: "/articles", method: "GET", params });
}
export function fetchArticle(slug) {
    return request({ url: `/articles/${encodeURIComponent(slug)}`, method: "GET" });
}
export function likeArticle(slug) {
    return request({ url: `/articles/${encodeURIComponent(slug)}/like`, method: "POST" });
}
