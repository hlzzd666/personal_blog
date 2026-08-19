import { request } from "./http";
export function fetchManageArticles(params = {}) {
    return request({ url: "/articles/manage", method: "GET", params });
}
export function createArticle(payload) {
    return request({ url: "/articles", method: "POST", data: payload });
}
export function updateArticle(id, payload) {
    return request({ url: `/articles/${id}`, method: "PUT", data: payload });
}
export function deleteArticle(id) {
    return request({ url: `/articles/${id}`, method: "DELETE" });
}
