import { request } from "./http";

export function recordVisitorVisit(pagePath: string) {
  return request({
    url: "/visitor-records",
    method: "POST",
    data: { page_path: pagePath },
  }).catch(() => undefined);
}
