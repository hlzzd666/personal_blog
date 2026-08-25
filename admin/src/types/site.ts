export type QuoteItem = {
  author: string;
  text: string;
};

export type VisualAssetItem = {
  key: string;
  name: string;
  usage: "background";
  image_url: string;
  enabled: boolean;
  opacity: number;
  note: string;
};

export type SiteSettings = {
  site_subtitle: string;
  hero_image_url: string;
  nav_brand: string;
  site_launched_on: string;
  owner_avatar_url: string;
  quotes: QuoteItem[];
  visual_assets: VisualAssetItem[];
  owner_location_name: string;
  owner_latitude: number | null;
  owner_longitude: number | null;
};
