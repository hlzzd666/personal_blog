import { request } from "./http";
import { compressImage } from "../utils/imageCompression";
import type {
  GalleryCharacter,
  GalleryCharacterPayload,
  GalleryChapter,
  GalleryChapterPayload,
  GalleryManageResponse,
  GallerySettings,
  GallerySettingsPayload,
} from "../types/gallery";

export type GalleryImageUploadResult = {
  url: string;
};

export function fetchManageGallery() {
  return request<GalleryManageResponse>({ url: "/gallery/manage", method: "GET" });
}

export function createGalleryChapter(payload: GalleryChapterPayload) {
  return request<GalleryChapter>({ url: "/gallery/chapters", method: "POST", data: payload });
}

export function updateGalleryChapter(id: number, payload: GalleryChapterPayload) {
  return request<GalleryChapter>({ url: `/gallery/chapters/${id}`, method: "PUT", data: payload });
}

export function deleteGalleryChapter(id: number) {
  return request<{ id: number }>({ url: `/gallery/chapters/${id}`, method: "DELETE" });
}

export function reorderGalleryChapters(chapterIds: number[]) {
  return request<GalleryChapter[]>({ url: "/gallery/chapters/order", method: "PUT", data: { chapter_ids: chapterIds } });
}

export function updateGallerySettings(payload: GallerySettingsPayload) {
  return request<GallerySettings>({ url: "/gallery/settings", method: "PUT", data: payload });
}

export function createGalleryCharacter(payload: GalleryCharacterPayload) {
  return request<GalleryCharacter>({ url: "/gallery/characters", method: "POST", data: payload });
}

export function updateGalleryCharacter(id: number, payload: GalleryCharacterPayload) {
  return request<GalleryCharacter>({
    url: `/gallery/characters/${id}`,
    method: "PUT",
    data: payload,
  });
}

export function deleteGalleryCharacter(id: number) {
  return request<{ id: number }>({ url: `/gallery/characters/${id}`, method: "DELETE" });
}

export function reorderGalleryCharacters(characterIds: number[]) {
  return request<GalleryCharacter[]>({
    url: "/gallery/characters/order",
    method: "PUT",
    data: { character_ids: characterIds },
  });
}

export async function uploadGalleryImage(kind: "logo" | "poster", file: File) {
  const compressedFile = await compressImage(file);
  const data = new FormData();
  data.append("file", compressedFile);
  return request<GalleryImageUploadResult>({
    url: `/gallery/media/${kind}`,
    method: "POST",
    data,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,
  });
}
