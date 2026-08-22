import { request } from "./http";
export async function loginAdmin(payload) {
    return request({
        method: "POST",
        url: "/auth/login",
        data: payload,
    });
}
export async function fetchCurrentAdmin() {
    return request({
        method: "GET",
        url: "/auth/me",
    });
}
export async function logoutAdmin() {
    await request({
        method: "POST",
        url: "/auth/logout",
    });
}
