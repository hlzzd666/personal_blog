import { request } from "./http";
export async function fetchVisitorLocation() {
    return request({ url: "/visitor-location", method: "GET" });
}
