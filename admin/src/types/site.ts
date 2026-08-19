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
