export type QuoteItem = {
  author: string;
  text: string;
};

export type SiteSettings = {
  site_subtitle: string;
  hero_image_url: string;
  nav_brand: string;
  owner_avatar_url: string;
  quotes: QuoteItem[];
  owner_location_name: string;
  owner_latitude: number | null;
  owner_longitude: number | null;
};
