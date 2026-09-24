import { request } from "./http";

export type GallerySettings = {
  id: number;
  hall_name: string;
  entry_title: string;
  show_entry: boolean;
  show_logo: boolean;
  logo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type GalleryCharacter = {
  id: number;
  name: string;
  epithet: string;
  faction: string;
  bounty: string;
  ability: string;
  description: string;
  quote: string;
  poster_url: string | null;
  chapter_id: number | null;
  is_visible: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type GalleryChapter = {
  id: number;
  title: string;
  subtitle: string;
  heading: string;
  description: string;
  note: string;
  label: string;
  story: string;
  artwork_index: number;
  is_visible: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type GalleryResponse = {
  settings: GallerySettings;
  chapters: GalleryChapter[];
  characters: GalleryCharacter[];
};

let galleryRequest: Promise<GalleryResponse> | undefined;

export function fetchGallery(refresh = false) {
  if (refresh) galleryRequest = undefined;
  galleryRequest ??= request<GalleryResponse>({ url: "/gallery", method: "GET" }).catch((error) => {
    galleryRequest = undefined;
    throw error;
  });
  return galleryRequest;
}
