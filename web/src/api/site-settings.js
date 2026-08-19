import { request } from "./http";
export async function fetchSiteSettings() {
    return request({ url: "/site-settings", method: "GET" });
}
