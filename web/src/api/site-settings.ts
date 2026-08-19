import { request } from "./http";

export type QuoteItem = {
  author: string;
  text: string;
};

export type SiteSettings = {
  site_subtitle: string;
  hero_image_url: string;
  nav_brand: string;
  quotes: QuoteItem[];
};

export async function fetchSiteSettings() {
  return request<SiteSettings>({ url: "/site-settings", method: "GET" });
}
