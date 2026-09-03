export type GallerySettings = {
  id: number;
  hall_name: string;
  entry_title: string;
  show_entry: boolean;
  show_logo: boolean;
  logo_url: string | null;
  logo_display_url: string | null;
  created_at: string;
  updated_at: string;
};

export type GallerySettingsPayload = Pick<
  GallerySettings,
  "hall_name" | "entry_title" | "show_entry" | "show_logo" | "logo_url" | "logo_display_url"
>;

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
  poster_frame_url: string | null;
  poster_display_url: string | null;
  is_visible: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type GalleryCharacterPayload = Pick<
  GalleryCharacter,
  | "name"
  | "epithet"
  | "faction"
  | "bounty"
  | "ability"
  | "description"
  | "quote"
  | "poster_url"
  | "poster_frame_url"
  | "poster_display_url"
  | "is_visible"
>;

export type GalleryManageResponse = {
  settings: GallerySettings;
  characters: GalleryCharacter[];
};
