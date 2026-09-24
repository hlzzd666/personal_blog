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

export type GallerySettingsPayload = Pick<
  GallerySettings,
  "hall_name" | "entry_title" | "show_entry" | "show_logo" | "logo_url"
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
  chapter_id: number | null;
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
  | "chapter_id"
  | "is_visible"
>;

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

export type GalleryChapterPayload = Omit<GalleryChapter, "id" | "sort_order" | "created_at" | "updated_at">;

export type GalleryManageResponse = {
  settings: GallerySettings;
  chapters: GalleryChapter[];
  characters: GalleryCharacter[];
};
