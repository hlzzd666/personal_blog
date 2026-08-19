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
export async function uploadImage(file) {
    const formData = new FormData();
    formData.append("file", file);
    return request({
        method: "POST",
        url: "/media/images",
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 30000,
    });
}
