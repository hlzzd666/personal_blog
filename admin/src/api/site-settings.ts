import { request } from "./http";
import type { SiteSettings } from "../types/site";

export async function fetchSiteSettings(): Promise<SiteSettings> {
  return request<SiteSettings>({
    method: "GET",
    url: "/site-settings",
  });
}

export async function updateSiteSettings(payload: SiteSettings): Promise<SiteSettings> {
  return request<SiteSettings>({
    method: "PUT",
    url: "/site-settings",
    data: payload,
  });
}
