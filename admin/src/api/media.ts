import { request } from "./http";
import type { MediaCleanupResponse, MediaListResponse } from "../types/media";
import { compressImage } from "../utils/imageCompression";

export type ImageUploadResult = {
  url: string;
  filename: string;
  content_type: string;
  size: number;
};

export async function fetchMediaFiles(): Promise<MediaListResponse> {
  return request<MediaListResponse>({
    method: "GET",
    url: "/media/files",
  });
}

export async function cleanupUnreferencedMediaFiles(): Promise<MediaCleanupResponse> {
  return request<MediaCleanupResponse>({
    method: "DELETE",
    url: "/media/files/unreferenced",
    timeout: 30000,
  });
}

export async function uploadMediaImage(file: File): Promise<ImageUploadResult> {
  const compressedFile = await compressImage(file);
  const formData = new FormData();
  formData.append("file", compressedFile);
  return request<ImageUploadResult>({
    method: "POST",
    url: "/media/images",
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,
  });
}
