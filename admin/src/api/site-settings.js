import { request } from "./http";
export async function fetchSiteSettings() {
    return request({
        method: "GET",
        url: "/site-settings",
    });
}
export async function updateSiteSettings(payload) {
    return request({
        method: "PUT",
        url: "/site-settings",
        data: payload,
    });
}
